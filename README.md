# Smart Presence Lock (FaceLock)

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)

A desktop security application for Windows that automatically locks your computer and hardware ports when you step away, built as a high-intensity bootcamp project.

## A Bootcamp Challenge

This project is the proud result of an intensive challenge from the **Kariz AI Bootcamp**. A dedicated team of 10 developers collaborated to design, build, and deliver this entire application in **less than 24 hours**.

---

## ✨ Features

- **Automatic Lock**: Locks the workstation automatically when no face is detected by the webcam.
- **Multi-Level Hardware Security**:
  - **Standard Lock**: Disables specific, non-whitelisted USB devices.
  - **Total Lockdown**: Disables the entire USB storage service via the registry for maximum security.
- **Multiple Detection Engines**: Allows the user to choose between the reliable Haar Cascade engine or a custom, lightweight skin-tone detector.
- **Run on Startup**: Can be configured to launch with administrator privileges when Windows starts, managed via Windows Task Scheduler.
- **System Tray Icon**: Runs silently in the background and is accessible from the system tray for easy control.

---

## 📝 Requirements

- Windows 10 or 11
- Python 3.8+
- A webcam

---

1.  Install the required Python packages:
    ```bash
    pip install -r requirements.txt
    ```
2.  Place the following required files in the project folder:
    -   `devcon.exe` in the main directory.
    -   `haarcascade_frontalface_default.xml` inside the `assets/` folder.

---

## 🚀 Usage

To use all features, the application must be run with **Administrator Privileges**.

1.  Open Command Prompt or PowerShell **as Administrator**.
2.  Navigate to the project directory.
3.  Run the application:
    ```bash
    python main.py
    ```
The default password on the first run is `admin`. You can change this and configure all other settings from the control panel.

---

## 👥 Contributors

This project is the result of the collaborative effort of the following team members from the Kariz AI Bootcamp:

- **Mohammad Mombini**
- **Amir Mahdi Teymouri**
- **Soheil Mirjalili**
- **Ali Mehranpoor**
- **Aref Karimi**
- **Reza Hedayat**
- **Danial**
- **Mohammad Amin**
- **Amirhossein Khorashadizadeh**
- **MohammadReza Hasanzadeh**

---

## 🙏 Acknowledgments

A special thanks to our instructor at the **Kariz AI Bootcamp** for their guidance and for inspiring this challenging and rewarding project.

---

## 📜 License

This project is licensed under the **GNU General Public License v3.0**. This is a strict, "copyleft" license that ensures that any derivative works must also be open-source under the same terms.

See the `LICENSE` file in this repository for the full text.