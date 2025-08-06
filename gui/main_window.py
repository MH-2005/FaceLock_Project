import tkinter as tk
from tkinter import ttk, messagebox
import json
from .config import Config
from .notification_manager import NotificationManager
from .tray_icon import TrayIcon
from core.security_manager import SecurityManager


class MainWindow(tk.Toplevel):
    def __init__(self, on_exit, on_password_change, get_current_hash_func, system_controller):
        super().__init__()
        self.on_exit = on_exit
        self.on_password_change = on_password_change
        self.get_current_hash = get_current_hash_func
        self.system_controller = system_controller
        self.security_manager = SecurityManager

        self.whitelisted_devices = self._load_whitelist()

        self.withdraw()
        self.notification_manager = NotificationManager()
        self.tray_icon = TrayIcon(self)

        self.is_monitoring = False
        self.start_monitoring_callback = None
        self.stop_monitoring_callback = None

        self.setup_window()
        self.create_ui()
        self.populate_usb_devices()

    def setup_window(self):
        self.title("FaceLock Control Panel")
        self.geometry("800x600")
        self.minsize(700, 500)
        self.configure(bg=Config.LIGHT_GRAY)
        self.protocol("WM_DELETE_WINDOW", self.minimize_to_tray)

    def create_ui(self):
        header_frame = tk.Frame(self, bg=Config.PRIMARY_COLOR, height=60)
        header_frame.pack(fill='x', expand=False)
        header_frame.pack_propagate(False)
        tk.Label(header_frame, text="FaceLock", font=Config.FONT_TITLE, fg=Config.WHITE_COLOR,
                 bg=Config.PRIMARY_COLOR).pack(side='left', padx=20)
        self.status_label = tk.Label(header_frame, text="● Inactive", font=Config.FONT_NORMAL, fg='#ffcccc',
                                     bg=Config.PRIMARY_COLOR)
        self.status_label.pack(side='right', padx=20)

        notebook = ttk.Notebook(self)
        notebook.pack(expand=True, fill='both', padx=10, pady=10)

        settings_frame = ttk.Frame(notebook)
        hardware_frame = ttk.Frame(notebook)

        notebook.add(settings_frame, text="⚙️ Settings")
        notebook.add(hardware_frame, text="🔌 Hardware Management")

        self.create_settings_tab(settings_frame)
        self.create_hardware_tab(hardware_frame)

    def create_settings_tab(self, parent_frame):
        monitoring_frame = ttk.LabelFrame(parent_frame, text="Monitoring Control", padding=(20, 10))
        monitoring_frame.pack(fill='x', padx=20, pady=10)

        self.start_button = tk.Button(monitoring_frame, text="▶️ Start Monitoring", command=self.toggle_monitoring,
                                      bg=Config.SUCCESS_COLOR, fg=Config.WHITE_COLOR, font=Config.FONT_BOLD,
                                      relief='flat', padx=20, pady=10)
        self.start_button.pack(pady=10)

        pwd_frame = ttk.LabelFrame(parent_frame, text="Change Password", padding=(20, 10))
        pwd_frame.pack(fill='x', padx=20, pady=20)
        # ... (Password change fields remain the same)
        ttk.Label(pwd_frame, text="Old Password:").grid(row=0, column=0, padx=5, pady=5, sticky='w')
        self.old_pwd_entry = ttk.Entry(pwd_frame, show="*", width=30)
        self.old_pwd_entry.grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(pwd_frame, text="New Password:").grid(row=1, column=0, padx=5, pady=5, sticky='w')
        self.new_pwd_entry = ttk.Entry(pwd_frame, show="*", width=30)
        self.new_pwd_entry.grid(row=1, column=1, padx=5, pady=5)
        ttk.Label(pwd_frame, text="Confirm New Password:").grid(row=2, column=0, padx=5, pady=5, sticky='w')
        self.confirm_pwd_entry = ttk.Entry(pwd_frame, show="*", width=30)
        self.confirm_pwd_entry.grid(row=2, column=1, padx=5, pady=5)
        ttk.Button(pwd_frame, text="Change Password", command=self.change_password).grid(row=3, column=1, padx=5,
                                                                                         pady=10, sticky='e')

    def create_hardware_tab(self, parent_frame):
        usb_frame = ttk.LabelFrame(parent_frame, text="USB Device Whitelist", padding=(20, 10))
        usb_frame.pack(fill='both', expand=True, padx=20, pady=10)

        cols = ('Status', 'Name', 'ID')
        self.usb_tree = ttk.Treeview(usb_frame, columns=cols, show='headings')
        self.usb_tree.heading('Status', text='Status')
        self.usb_tree.heading('Name', text='Device Name')
        self.usb_tree.heading('ID', text='Device ID')
        self.usb_tree.column('Status', width=80, anchor='center')
        self.usb_tree.column('ID', width=300)

        self.usb_tree.tag_configure('whitelisted', foreground='green')
        self.usb_tree.tag_configure('blocked', foreground='red')

        self.usb_tree.pack(fill='both', expand=True, side='top')
        self.usb_tree.bind('<Double-1>', self.toggle_whitelist)

        button_frame = ttk.Frame(usb_frame)
        button_frame.pack(fill='x', pady=10)
        ttk.Button(button_frame, text="Refresh List", command=self.populate_usb_devices).pack(side='left')
        ttk.Button(button_frame, text="Save Whitelist", command=self._save_whitelist).pack(side='right')

    def populate_usb_devices(self):
        for i in self.usb_tree.get_children():
            self.usb_tree.delete(i)

        devices = self.system_controller.get_usb_devices()
        for dev in devices:
            dev_id = dev.get('id', '')
            status = 'Whitelisted' if dev_id in self.whitelisted_devices else 'Blocked'
            tag = 'whitelisted' if dev_id in self.whitelisted_devices else 'blocked'
            self.usb_tree.insert('', 'end', values=(status, dev.get('name', ''), dev_id), tags=(tag,))

    def toggle_whitelist(self, event):
        item_id = self.usb_tree.focus()
        if not item_id:
            return

        item = self.usb_tree.item(item_id)
        dev_id = item['values'][2]

        if dev_id in self.whitelisted_devices:
            self.whitelisted_devices.remove(dev_id)
        else:
            self.whitelisted_devices.add(dev_id)

        self.populate_usb_devices()

    def _load_whitelist(self):
        # In a real app, this should be loaded from an encrypted settings file
        # For simplicity, we load from a simple json file here.
        try:
            with open('config/whitelist.json', 'r') as f:
                return set(json.load(f))
        except (FileNotFoundError, json.JSONDecodeError):
            return set()

    def _save_whitelist(self):
        try:
            with open('config/whitelist.json', 'w') as f:
                json.dump(list(self.whitelisted_devices), f, indent=4)
            self.notification_manager.show_success("Whitelist Saved", "The list of safe devices has been updated.")
        except Exception as e:
            messagebox.showerror("Error", f"Could not save whitelist: {e}", parent=self)

    # ... (Other methods like change_password, toggle_monitoring, show, etc. remain the same)
    def change_password(self):
        old_pwd = self.old_pwd_entry.get()
        new_pwd = self.new_pwd_entry.get()
        confirm_pwd = self.confirm_pwd_entry.get()

        if not all((old_pwd, new_pwd, confirm_pwd)):
            messagebox.showerror("Error", "All fields are required.", parent=self)
            return
        if not self.security_manager.verify_password(old_pwd, self.get_current_hash()):
            messagebox.showerror("Error", "Old password is not correct.", parent=self)
            return
        if new_pwd != confirm_pwd:
            messagebox.showerror("Error", "New passwords do not match.", parent=self)
            return

        new_hash = self.security_manager.hash_password(new_pwd)
        self.on_password_change(new_hash)

        self.old_pwd_entry.delete(0, tk.END)
        self.new_pwd_entry.delete(0, tk.END)
        self.confirm_pwd_entry.delete(0, tk.END)
        messagebox.showinfo("Success", "Password changed successfully.", parent=self)

    def toggle_monitoring(self):
        self.is_monitoring = not self.is_monitoring
        if self.is_monitoring:
            if self.start_monitoring_callback:
                self.start_monitoring_callback()
                self.start_button.config(text="⏸️ Stop Monitoring", bg=Config.ERROR_COLOR)
                self.status_label.config(text="● Active", fg='#90EE90')
                self.tray_icon.update_icon_status(active=True)
        else:
            if self.stop_monitoring_callback:
                self.stop_monitoring_callback()
                self.start_button.config(text="▶️ Start Monitoring", bg=Config.SUCCESS_COLOR)
                self.status_label.config(text="● Inactive", fg='#ffcccc')
                self.tray_icon.update_icon_status(active=False)

    def show(self):
        self.deiconify()
        self.update_idletasks()
        x = (self.winfo_screenwidth() - self.winfo_width()) // 2
        y = (self.winfo_screenheight() - self.winfo_height()) // 2
        self.geometry(f'+{x}+{y}')
        self.lift()

    def minimize_to_tray(self):
        self.withdraw()
        self.notification_manager.show_info("Minimized", "Application is running in the background.")

    def exit_app(self):
        if messagebox.askyesno("Exit", "Are you sure you want to exit?"):
            self.on_exit()