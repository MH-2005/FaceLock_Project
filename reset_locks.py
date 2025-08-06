# reset_locks.py
import subprocess
import winreg
import ctypes
import sys
import os

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def find_devcon():
    # Looks for devcon.exe in the same folder as the script
    application_path = os.path.dirname(os.path.abspath(sys.argv[0]))
    path_to_check = os.path.join(application_path, 'devcon.exe')
    if os.path.exists(path_to_check):
        return os.path.normpath(path_to_check)
    return None

def main():
    if not is_admin():
        print("ERROR: This script must be run as an administrator!")
        input("Press Enter to exit...")
        return

    print("--- Starting System Reset ---")

    # Step 1: Re-enable the USB Storage Service via Registry
    try:
        key_path = r"SYSTEM\CurrentControlSet\Services\USBSTOR"
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, "Start", 0, winreg.REG_DWORD, 3) # 3 = Enabled
        winreg.CloseKey(key)
        print("[SUCCESS] USB Storage Service has been re-enabled.")
    except Exception as e:
        print(f"[ERROR] Could not re-enable USB Storage Service: {e}")

    # Step 2: Re-enable all USB devices using devcon.exe
    devcon_path = find_devcon()
    if devcon_path:
        print("\nAttempting to re-enable all USB devices with devcon.exe...")
        try:
            command = [devcon_path, "enable", "*USB*"]
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            print("[SUCCESS] Devcon 'enable *USB*' command executed.")
            print("Output:\n" + result.stdout)
        except Exception as e:
            print(f"[ERROR] Devcon command failed: {e}")
    else:
        print("[ERROR] devcon.exe not found. Cannot perform devcon reset.")

    print("\n--- Reset Complete ---")
    input("Press Enter to exit...")

if __name__ == "__main__":
    main()