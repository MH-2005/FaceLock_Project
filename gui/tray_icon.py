import pystray
from PIL import Image, ImageDraw
import threading
from .config import Config

class TrayIcon:
    def __init__(self, main_window):
        self.main_window = main_window
        self.icon = self._create_pystray_icon()
        self.thread = threading.Thread(target=self.icon.run, daemon=True)
        self.thread.start()

    def _create_image(self, color):
        width = 64
        height = 64
        image = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        dc = ImageDraw.Draw(image)
        dc.ellipse([8, 8, width - 8, height - 8], fill=color)
        return image

    def _create_pystray_icon(self):
        menu = pystray.Menu(
            pystray.MenuItem("Show Window", self.main_window.show, default=True),
            pystray.MenuItem("Toggle Monitoring", self.main_window.toggle_monitoring),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Exit", self.main_window.exit_app)
        )
        image = self._create_image(Config.DARK_GRAY_FRAME)
        return pystray.Icon("FaceLock", image, "FaceLock", menu)

    def update_icon_status(self, active: bool):
        if self.icon:
            color = Config.SUCCESS_COLOR if active else Config.DARK_GRAY_FRAME
            self.icon.icon = self._create_image(color)

    def stop(self):
        if self.icon:
            self.icon.stop()