import ctypes
import os
import sys
import subprocess
import winreg


class SystemController:
    def __init__(self, logger=None):
        self.logger = logger
        self.devcon_path = self._find_devcon()

    def is_admin(self):
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False

    def _find_devcon(self):
        if getattr(sys, 'frozen', False):
            application_path = os.path.dirname(sys.executable)
        else:
            application_path = os.path.dirname(os.path.abspath(sys.argv[0]))

        path_to_check = os.path.join(application_path, 'devcon.exe')

        if os.path.exists(path_to_check):
            return os.path.normpath(path_to_check)
        if self.logger:
            self.logger.error("devcon.exe not found in the application's root directory.")
        return None

    def lock_workstation(self):
        try:
            ctypes.windll.user32.LockWorkStation()
            return True
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to lock workstation: {e}")
            return False

    def _run_command(self, command_list):
        if self.logger:
            self.logger.info(f"Executing command: {' '.join(command_list)}")

        try:
            result = subprocess.run(command_list, capture_output=True, text=True, check=True,
                                    creationflags=subprocess.CREATE_NO_WINDOW)

            # Log the output for debugging purposes
            if result.stdout:
                self.logger.info(f"Command STDOUT: {result.stdout.strip()}")
            if result.stderr:
                self.logger.warning(f"Command STDERR: {result.stderr.strip()}")

            return result

        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            if self.logger:
                error_output = e.stderr if hasattr(e, 'stderr') else str(e)
                self.logger.error(f"Command failed: {' '.join(command_list)}. Error: {error_output}")
            return None

    def get_usb_devices(self):
        if not self.devcon_path:
            return []

        result = self._run_command([self.devcon_path, "find", "*USB*"])
        if not result:
            return []

        devices = []
        for line in result.stdout.splitlines():
            if line.strip() and not line.startswith("No matching devices"):
                parts = line.split(" : ", 1)
                device_id = parts[0].strip()
                name = parts[1].strip() if len(parts) > 1 else "Unknown USB Device"
                devices.append({'id': device_id, 'name': name})
        return devices

    def set_device_state_by_id(self, device_id, enable=True):
        if not self.devcon_path:
            return False

        action = "enable" if enable else "disable"
        command = [self.devcon_path, action, f"@{device_id}"]

        result = self._run_command(command)

        if result and result.stdout:
            # A more reliable check for success
            if "disabled" in result.stdout.lower() or "enabled" in result.stdout.lower():
                if "No matching devices" not in result.stdout:
                    return True

        if self.logger:
            self.logger.error(f"Failed to change state for device {device_id}.")
        return False

    def set_usb_storage_state(self, enable=True):
        key_path = r"SYSTEM\CurrentControlSet\Services\USBSTOR"
        value = 3 if enable else 4
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(key, "Start", 0, winreg.REG_DWORD, value)
            winreg.CloseKey(key)
            if self.logger:
                status = "Enabled" if enable else "Disabled"
                self.logger.info(f"USBSTOR service has been {status}.")
            return True
        except (PermissionError, FileNotFoundError, OSError) as e:
            if self.logger:
                self.logger.error(f"Failed to change USBSTOR state: {e}")
            return False