from plyer import notification
from tkinter import messagebox
import tkinter as tk


class NotificationManager:
    def show_info(self, title, message):
        self._show_system_notification(title, message)

    def show_success(self, title, message):
        self._show_system_notification(title, message)

    def _show_system_notification(self, title, message):
        try:
            notification.notify(
                title=title,
                message=message,
                app_name="FaceLock",
                timeout=5
            )
        except Exception as e:
            # Fallback to a simple messagebox if plyer fails
            print(f"System notification failed: {e}")
            messagebox.showinfo(title, message)