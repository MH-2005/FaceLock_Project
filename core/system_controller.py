import ctypes
import os
import sys
import subprocess
import winreg


class SystemController:
    def __init__(self):
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
        return None

    def lock_workstation(self):
        try:
            ctypes.windll.user32.LockWorkStation()
            return True
        except Exception:
            return False

    def _run_command(self, command):
        return subprocess.run(command, capture_output=True, text=True, shell=True,
                              creationflags=subprocess.CREATE_NO_WINDOW)

    def get_usb_devices(self):
        if not self.devcon_path:
            return []

        result = self._run_command([self.devcon_path, "find", "*USB*"])
        devices = []
        if result.returncode == 0:
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
        command = f'"{self.devcon_path}" {action} "@{device_id}"'

        result = self._run_command(command)
        return result.returncode == 0 and ("disabled" in result.stdout.lower() or "enabled" in result.stdout.lower())

    def set_usb_storage_state(self, enable=True):
        key_path = r"SYSTEM\CurrentControlSet\Services\USBSTOR"
        value = 3 if enable else 4
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_WRITE)
            winreg.SetValueEx(key, "Start", 0, winreg.REG_DWORD, value)
            winreg.CloseKey(key)
            return True
        except Exception:
            return False