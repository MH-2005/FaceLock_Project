import sys
import tkinter as tk
from tkinter import messagebox
import json
import os
import threading
import ctypes
from ctypes import wintypes

from utils.logger_setup import setup_logging
from core.security_manager import SecurityManager
from core.system_controller import SystemController
from core.presence_monitor import PresenceMonitor, HaarCascadeDetector, CustomSkinDetector
from gui.login_window import LoginWindow
from gui.main_window import MainWindow
import reset_locks


logger = setup_logging()
SETTINGS_FILE = "config/app_settings.json"
PASSWORD_FILE = "config/password.json"


def wait_for_user_login():
    def on_unlock():
        reset_locks.main()

    user32 = ctypes.WinDLL('user32', use_last_error=True)
    WTS_SESSION_UNLOCK = 0x8
    WM_WTSSESSION_CHANGE = 0x02B1
    NOTIFY_FOR_ALL_SESSIONS = 1

    hwnd = None
    msg = wintypes.MSG()

    def window_proc(hwnd, msg_type, wparam, lparam):
        if msg_type == WM_WTSSESSION_CHANGE and wparam == WTS_SESSION_UNLOCK:
            on_unlock()
        return user32.DefWindowProcW(hwnd, msg_type, wparam, lparam)

    wndproc = ctypes.WINFUNCTYPE(wintypes.LRESULT, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM)(window_proc)

    wc = wintypes.WNDCLASSW()
    wc.lpfnWndProc = wndproc
    wc.lpszClassName = "UserLoginMonitor"
    wc.hInstance = user32.GetModuleHandleW(None)

    class_atom = user32.RegisterClassW(ctypes.byref(wc))
    if not class_atom:
        return

    hwnd = user32.CreateWindowExW(0, class_atom, "UserLoginMonitor", 0, 0, 0, 0, 0, None, None, wc.hInstance, None)
    if not hwnd:
        return

    if not user32.WTSRegisterSessionNotification(hwnd, NOTIFY_FOR_ALL_SESSIONS):
        user32.DestroyWindow(hwnd)
        return

    while True:
        result = user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
        if result <= 0:
            break
        user32.TranslateMessage(ctypes.byref(msg))
        user32.DispatchMessageW(ctypes.byref(msg))


class FaceLockApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.withdraw()

        self.system_controller = SystemController(logger=logger)
        self.system_controller.reset_all_usb_ports()

        if not self.system_controller.is_admin():
            logger.error("FATAL: Application must be run with administrator privileges.")
            messagebox.showerror("Permission Denied",
                                 "This application requires administrator privileges. Please restart as admin.")
            sys.exit(1)

        self.settings = self._load_settings()
        self.current_password_hash = self._load_or_create_password_hash()

        self.presence_monitor = None
        self.main_window = None

    def _load_settings(self):
        try:
            with open(SETTINGS_FILE, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {'lockdown_level': 'standard', 'detection_engine': 'haar'}

    def _load_or_create_password_hash(self):
        try:
            with open(PASSWORD_FILE, 'r') as f:
                return json.load(f)['password_hash']
        except (FileNotFoundError, json.JSONDecodeError, KeyError):
            default_hash = SecurityManager.hash_password("admin")
            self._save_password_hash(default_hash)
            logger.info("Password file not found. Created with default 'admin'.")
            return default_hash

    def _save_password_hash(self, new_hash):
        self.current_password_hash = new_hash
        os.makedirs(os.path.dirname(PASSWORD_FILE), exist_ok=True)
        with open(PASSWORD_FILE, 'w') as f:
            json.dump({'password_hash': new_hash}, f, indent=4)
        logger.info("Password hash has been updated.")

    def run(self):
        login_window = LoginWindow(
            master=self.root,
            on_login_success=self.on_login_success,
            current_hash=self.current_password_hash
        )
        login_window.show()

        login_thread = threading.Thread(target=wait_for_user_login, daemon=True)
        login_thread.start()

        self.root.mainloop()

    def on_login_success(self):
        self.system_controller.reset_all_usb_ports()

        self.main_window = MainWindow(
            on_exit=self.shutdown,
            on_password_change=self._save_password_hash,
            get_current_hash_func=lambda: self.current_password_hash,
            system_controller=self.system_controller,
            settings=self.settings
        )
        self.main_window.start_monitoring_callback = self.start_monitoring
        self.main_window.stop_monitoring_callback = self.stop_monitoring
        self.main_window.show()
        logger.info("Main window displayed.")

    def _handle_presence_change(self, is_present):
        if is_present:
            return

        logger.warning("Absence detected. Locking workstation and securing ports.")
        self.system_controller.lock_workstation()

        lockdown_level = self.settings.get('lockdown_level', 'standard')

        if lockdown_level == 'total':
            logger.info("Applying TOTAL LOCKDOWN: Disabling USB storage service.")
            self.system_controller.set_usb_storage_state(enable=False)
        else:
            logger.info("Applying STANDARD LOCK: Disabling non-whitelisted devices.")
            protected_keywords = ["root hub", "host controller", "camera", "webcam", "keyboard", "mouse", "bluetooth"]
            whitelisted_ids = self.main_window.whitelisted_devices if self.main_window else set()
            all_usb_devices = self.system_controller.get_usb_devices()

            for device in all_usb_devices:
                device_id, device_name = device.get('id'), device.get('name', '').lower()
                is_protected = any(keyword in device_name for keyword in protected_keywords)
                is_whitelisted = device_id in whitelisted_ids

                if not is_protected and not is_whitelisted:
                    logger.info(f"Disabling non-essential device: {device.get('name')}")
                    self.system_controller.set_device_state_by_id(device_id, enable=False)

    def start_monitoring(self):
        if self.presence_monitor and self.presence_monitor.is_alive():
            logger.warning("Monitoring is already running.")
            return
        try:
            engine_choice = self.settings.get('detection_engine', 'haar')
            detector = CustomSkinDetector(logger=logger) if engine_choice == 'skin' else HaarCascadeDetector(logger=logger)
            self.presence_monitor = PresenceMonitor(detector_engine=detector,
                                                    on_presence_change=self._handle_presence_change, lock_delay=10,
                                                    logger=logger)
            self.presence_monitor.start()
            if self.main_window:
                self.main_window.update_monitoring_ui(is_active=True)
                self.main_window.notification_manager.show_success("Monitoring Started",
                                                                   "System is now being monitored.")
        except (FileNotFoundError, ValueError) as e:
            logger.error(f"Could not start monitoring: {e}")
            messagebox.showerror("Error", "Could not start monitoring. Ensure asset files are correct and readable.")
            if self.main_window:
                self.main_window.update_monitoring_ui(is_active=False)

    def stop_monitoring(self):
        if not self.presence_monitor or not self.presence_monitor.is_alive():
            logger.warning("Monitoring is not running.")
            return
        self.presence_monitor.stop()
        self.presence_monitor.join(timeout=2.0)
        self.presence_monitor = None
        if self.main_window:
            self.main_window.update_monitoring_ui(is_active=False)
            self.main_window.notification_manager.show_info("Monitoring Stopped", "System is no longer monitored.")

    def shutdown(self):
        logger.info("Shutdown sequence initiated.")
        self.stop_monitoring()
        if self.main_window and self.main_window.tray_icon:
            self.main_window.tray_icon.stop()

        self.system_controller.reset_all_usb_ports()
        self.root.quit()
        logger.info("Application has been shut down gracefully.")
        sys.exit(0)


if __name__ == "__main__":
    app = FaceLockApp()
    app.run()
