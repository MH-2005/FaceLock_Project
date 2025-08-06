import ctypes
import os
import sys
import subprocess


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
            application_path = os.path.dirname(os.path.abspath(__file__))

        # We assume devcon.exe is in the parent directory of 'core'
        base_path = os.path.join(application_path, '..')
        path_to_check = os.path.join(base_path, 'devcon.exe')

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
        command = [self.devcon_path, action, f"@{device_id}"]

        result = self._run_command(command)
        return result.returncode == 0 and "disabled" in result.stdout or "enabled" in result.stdout

    def get_pnp_devices(self, device_class="Keyboard"):
        command = f"Get-PnpDevice -Class {device_class} | Select-Object InstanceId, Name, Present | Format-List"
        full_command = ['PowerShell', '-Command', command]

        result = self._run_command(full_command)
        devices = []
        if result.returncode == 0:
            content = result.stdout.strip().replace('\r', '')
            entries = content.split('\n\n')
            for entry in entries:
                device = {}
                for line in entry.split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        key = key.strip().lower().replace(' ', '_')
                        device[key] = value.strip()
                if device.get('present', '').lower() == 'true':
                    devices.append(device)
        return devices

    def set_pnp_device_state(self, instance_id, enable=True):
        action = "Enable-PnpDevice" if enable else "Disable-PnpDevice"
        escaped_id = instance_id.replace('"', '\\"')
        command = f'{action} -InstanceId "{escaped_id}" -Confirm:$false'
        full_command = ['PowerShell', '-Command', command]

        result = self._run_command(full_command)
        return result.returncode == 0