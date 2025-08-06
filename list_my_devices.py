import subprocess
import ctypes
import sys
import os

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def find_devcon():
    application_path = os.path.dirname(os.path.abspath(sys.argv[0]))
    path_to_check = os.path.join(application_path, 'devcon.exe')
    if os.path.exists(path_to_check):
        return os.path.normpath(path_to_check)
    return None

def main():
    if not is_admin():
        print("ERROR: Please run this script as an administrator!")
        input("Press Enter to exit...")
        return

    devcon_path = find_devcon()
    if not devcon_path:
        print("ERROR: devcon.exe not found in this folder.")
        input("Press Enter to exit...")
        return

    print("--- Listing all USB Devices ---")
    try:
        result = subprocess.run([devcon_path, "find", "*USB*"], capture_output=True, text=True, check=True)
        print(result.stdout)
    except Exception as e:
        print(f"An error occurred: {e}")

    print("\n--- End of List ---")
    input("Press Enter to exit...")

if __name__ == "__main__":
    main()