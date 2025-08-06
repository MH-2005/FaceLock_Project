import sys
import tkinter as tk
from tkinter import messagebox
import json
import os

from utils.logger_setup import setup_logging
from core.security_manager import SecurityManager
from core.system_controller import SystemController
from core.presence_monitor import PresenceMonitor

from gui.login_window import LoginWindow
from gui.main_window import MainWindow

logger = setup_logging()
SETTINGS_FILE = "config/settings.json"


class FaceLockApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.withdraw()

        self.system_controller = SystemController()
        if not self.system_controller.is_admin():
            logger.warning("Application not running with admin privileges. Hardware control may fail.")

        self.current_password_hash = self._load_or_create_password_hash()

        self.presence_monitor = None
        self.main_window = None

    def _load_or_create_password_hash(self):
        os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
        try:
            with open(SETTINGS_FILE, 'r') as f:
                settings = json.load(f)
                if 'password_hash' in settings:
                    return settings['password_hash']
        except (FileNotFoundError, json.JSONDecodeError):
            pass

        default_hash = SecurityManager.hash_password("admin")
        self._save_password_hash(default_hash)
        logger.info("Settings file not found or invalid. Created a new one with default password 'admin'.")
        return default_hash

    def _save_password_hash(self, new_hash):
        self.current_password_hash = new_hash
        with open(SETTINGS_FILE, 'w') as f:
            json.dump({'password_hash': new_hash}, f, indent=4)
        logger.info("Password hash has been updated.")

    def run(self):
        login_window = LoginWindow(
            master=self.root,
            on_login_success=self.on_login_success,
            current_hash=self.current_password_hash
        )
        login_window.show()
        self.root.mainloop()

    def on_login_success(self):
        self.main_window = MainWindow(
            on_exit=self.shutdown,
            on_password_change=self._save_password_hash,
            get_current_hash_func=lambda: self.current_password_hash,
            system_controller=self.system_controller
        )
        self.main_window.start_monitoring_callback = self.start_monitoring
        self.main_window.stop_monitoring_callback = self.stop_monitoring

        self.main_window.show()
        logger.info("Login successful. Main window displayed.")

    def _handle_presence_change(self, is_present):
        if is_present:
            logger.info("Presence re-detected.")
            return

        logger.warning("Absence detected. Locking workstation and securing ports.")

        self.system_controller.lock_workstation()

        whitelisted_ids = self.main_window.whitelisted_devices if self.main_window else set()
        all_usb_devices = self.system_controller.get_usb_devices()

        protected_keywords = ["camera", "keyboard", "mouse", "hub", "controller"]

        for device in all_usb_devices:
            device_id = device.get('id')
            device_name = device.get('name', '').lower()

            is_whitelisted = device_id in whitelisted_ids
            is_protected = any(keyword in device_name for keyword in protected_keywords)

            if not is_whitelisted and not is_protected:
                logger.info(f"Disabling non-essential device: {device.get('name')}")
                self.system_controller.set_device_state_by_id(device_id, enable=False)

    def start_monitoring(self):
        if self.presence_monitor and self.presence_monitor.is_alive():
            logger.warning("Monitoring is already running.")
            return

        try:
            self.presence_monitor = PresenceMonitor(
                on_presence_change=self._handle_presence_change,
                lock_delay=10,
                logger=logger
            )
            self.presence_monitor.start()
            if self.main_window:
                self.main_window.notification_manager.show_success("Monitoring Started",
                                                                   "System is now being monitored.")
        except FileNotFoundError as e:
            logger.error(f"Could not start monitoring: {e}")
            messagebox.showerror("Error",
                                 f"Could not start monitoring. Ensure '{e.filename}' is in the correct folder.")
            if self.main_window:  # Revert UI state
                self.main_window.is_monitoring = False
                self.main_window.toggle_monitoring()

    def stop_monitoring(self):
        if not self.presence_monitor or not self.presence_monitor.is_alive():
            logger.warning("Monitoring is not running.")
            return

        self.presence_monitor.stop()
        self.presence_monitor.join(timeout=2.0)
        self.presence_monitor = None
        logger.info("Monitoring has been stopped by the user.")
        if self.main_window:
            self.main_window.notification_manager.show_info("Monitoring Stopped", "System is no longer monitored.")

    def shutdown(self):
        logger.info("Shutdown sequence initiated.")
        self.stop_monitoring()
        if self.main_window and self.main_window.tray_icon:
            self.main_window.tray_icon.stop()
        self.root.quit()
        logger.info("Application has been shut down gracefully.")
        sys.exit(0)


if __name__ == "__main__":
    app = FaceLockApp()
    app.run()