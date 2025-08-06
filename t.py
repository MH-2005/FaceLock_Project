import subprocess

DEVCON_PATH = r"devcon.exe"

def list_usb_devices():
    result = subprocess.run([DEVCON_PATH, "find", "*USB*"], capture_output=True, text=True)
    devices = []
    for line in result.stdout.splitlines():
        if line.strip() and not line.startswith("No matching devices"):
            # جدا کردن ID از نام
            parts = line.split(" : ")
            device_id = parts[0].strip()
            name = parts[1].strip() if len(parts) > 1 else "Unknown"
            devices.append((device_id, name))
    return devices

def disable_device(device_id):
    subprocess.run([DEVCON_PATH, "disable", f"@{device_id}"])

def enable_device(device_id):
    subprocess.run([DEVCON_PATH, "enable", f"@{device_id}"])

# نمایش دستگاه‌ها
devices = list_usb_devices()
for i, (dev_id, name) in enumerate(devices, start=1):
    print(f"{i}. {name}  -->  {dev_id}")

choice = int(input("\nشماره دستگاهی که میخوای غیرفعال بشه رو انتخاب کن: "))
# disable_device(devices[choice-1][0])

# اگر خواستی دوباره فعال کنی:
enable_device(devices[choice-1][0])