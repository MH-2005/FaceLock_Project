import cv2
import numpy as np
import threading
import time
import os


class FastImageEnhancer:
    def __init__(self, clip_limit=2.0, tile_grid_size=(8, 8)):
        self.clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid_size)

    def process(self, image_bgr):
        if image_bgr is None:
            return None
        gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
        enhanced_contrast = self.clahe.apply(gray)
        return enhanced_contrast


class PresenceMonitor(threading.Thread):
    def __init__(self, on_presence_change, lock_delay=10, camera_index=0, logger=None):
        super().__init__(daemon=True)
        self.on_presence_change = on_presence_change
        self.lock_delay_seconds = lock_delay
        self.camera_index = camera_index
        self.logger = logger

        cascade_file = os.path.join('assets', 'haarcascade_frontalface_default.xml')
        if not os.path.exists(cascade_file):
            if self.logger:
                self.logger.error(f"Cascade file not found: {cascade_file}")
            raise FileNotFoundError(f"Cascade file not found: {cascade_file}")

        self.face_cascade = cv2.CascadeClassifier(cascade_file)
        self.image_enhancer = FastImageEnhancer()

        self.is_running = False
        self._lock = threading.Lock()

        self.last_presence_state = True
        self.no_face_start_time = None

    def run(self):
        self.is_running = True
        if self.logger:
            self.logger.info("Presence monitor thread started.")

        cap = cv2.VideoCapture(self.camera_index)
        if not cap.isOpened():
            if self.logger:
                self.logger.error(f"Could not open camera with index {self.camera_index}.")
            self.is_running = False
            return

        while self.is_running:
            ret, frame = cap.read()
            if not ret:
                if self.logger:
                    self.logger.warning("Failed to grab frame from camera. Retrying...")
                time.sleep(1)
                continue

            enhanced_frame = self.image_enhancer.process(frame)
            faces = self.face_cascade.detectMultiScale(
                enhanced_frame,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(40, 40)
            )

            current_face_present = len(faces) > 0
            self._update_state(current_face_present)

            time.sleep(0.1)

        cap.release()
        if self.logger:
            self.logger.info("Presence monitor thread stopped and camera released.")

    def stop(self):
        with self._lock:
            self.is_running = False

    def _update_state(self, is_present):
        with self._lock:
            if is_present:
                self.no_face_start_time = None
                if not self.last_presence_state:
                    self.last_presence_state = True
                    self.on_presence_change(True)
                    if self.logger:
                        self.logger.info("Presence DETECTED.")
            else:

                if self.no_face_start_time is None:
                    self.no_face_start_time = time.time()

                elapsed = time.time() - self.no_face_start_time
                if elapsed >= self.lock_delay_seconds:
                    if self.last_presence_state:
                        self.last_presence_state = False
                        self.on_presence_change(False)
                        if self.logger:
                            self.logger.warning(
                                f"Absence detected for {self.lock_delay_seconds} seconds. Signaling to lock.")