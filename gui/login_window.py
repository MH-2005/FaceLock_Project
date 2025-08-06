import tkinter as tk
from tkinter import messagebox
from .config import Config
from core.security_manager import SecurityManager

class LoginWindow(tk.Toplevel):
    def __init__(self, master, on_login_success, current_hash):
        super().__init__(master)
        self.on_login_success = on_login_success
        self.current_hash = current_hash
        self.security_manager = SecurityManager

        self.setup_window()
        self.create_ui()
        self.transient(master)
        self.grab_set()

    def setup_window(self):
        self.title("Login")
        self.resizable(False, False)
        self.configure(bg=Config.DARK_GRAY_BG)
        self.update_idletasks()
        width, height = 450, 250
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')

    def create_ui(self):
        frame = tk.Frame(self, bg=Config.DARK_GRAY_BG, padx=30, pady=30)
        frame.pack(expand=True, fill='both')

        tk.Label(frame, text="Secure Login", font=Config.FONT_TITLE, fg=Config.WHITE_COLOR,
                 bg=Config.DARK_GRAY_BG).pack(pady=(0, 20))

        self.password_entry = tk.Entry(frame, show="*", font=('Segoe UI', 12), bg='#3d3d3d', fg=Config.WHITE_COLOR,
                                       relief='flat', insertbackground=Config.WHITE_COLOR)
        self.password_entry.pack(fill='x', ipady=8, pady=5)
        self.password_entry.bind('<Return>', self.check_password)

        tk.Button(frame, text="LOGIN", command=self.check_password, font=Config.FONT_BOLD, bg=Config.PRIMARY_COLOR,
                  fg=Config.WHITE_COLOR, relief='flat').pack(fill='x', pady=(15, 0), ipady=10)

        self.password_entry.focus()

    def check_password(self, event=None):
        entered_password = self.password_entry.get()
        if self.security_manager.verify_password(entered_password, self.current_hash):
            self.destroy()
            self.on_login_success()
        else:
            messagebox.showerror("Login Failed", "Incorrect password!", parent=self)
            self.password_entry.delete(0, tk.END)

    def show(self):
        self.deiconify()