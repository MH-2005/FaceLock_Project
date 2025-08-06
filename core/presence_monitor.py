import cv2
import numpy as np
import threading
import time
import os


class BaseDetector:
    def detect(self, frame):
        raise NotImplementedError


class HaarCascadeDetector(BaseDetector):
    def __init__(self, logger=None):
        self.logger = logger
        cascade_file = os.path.join('assets', 'haarcascade_frontalface_default.xml')
        if not os.path.exists(cascade_file):
            if self.logger: self.logger.error(f"Cascade file not found: {cascade_file}")
            raise FileNotFoundError(cascade_file)

        self.face_cascade = cv2.CascadeClassifier(cascade_file)
        if self.face_cascade.empty():
            if self.logger: self.logger.error(f"Failed to load cascade file: {cascade_file}")
            raise ValueError(f"Failed to load cascade file: {cascade_file}")

        self.enhancer = self._get_grayscale_enhancer()

    def _get_grayscale_enhancer(self):
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))

        def enhance(image_bgr):
            if image_bgr is None: return None
            gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
            return clahe.apply(gray)

        return enhance

    def detect(self, frame):
        enhanced_frame = self.enhancer(frame)
        if enhanced_frame is None: return False

        faces = self.face_cascade.detectMultiScale(
            enhanced_frame, scaleFactor=1.1, minNeighbors=5, minSize=(40, 40)
        )
        return len(faces) > 0


class CustomSkinDetector(BaseDetector):
    def __init__(self, logger=None):
        self.logger = logger
        self.scale_factor = 0.5
        self.min_face_area = 1000 / (self.scale_factor * self.scale_factor)
        self.skin_lower = np.array([0, 135, 85], dtype=np.uint8)
        self.skin_upper = np.array([255, 180, 135], dtype=np.uint8)
        self.kernel = np.ones((3, 3), np.uint8)

    def detect(self, frame):
        if frame is None: return False

        img = cv2.resize(frame, None, fx=self.scale_factor, fy=self.scale_factor, interpolation=cv2.INTER_LINEAR)
        ycbcr = cv2.cvtColor(img, cv2.COLOR_BGR2YCrCb)
        skin_mask = cv2.inRange(ycbcr, self.skin_lower, self.skin_upper)

        skin_mask = cv2.erode(skin_mask, self.kernel, iterations=1)
        skin_mask = cv2.dilate(skin_mask, self.kernel, iterations=2)

        contours, _ = cv2.findContours(skin_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            if cv2.contourArea(contour) < self.min_face_area:
                continue

            x, y, w, h = cv2.boundingRect(contour)
            if not (0.6 < (w / float(h)) < 1.4):
                continue

            return True

        return False


class PresenceMonitor(threading.Thread):
    def __init__(self, detector_engine, on_presence_change, lock_delay=10, camera_index=0, logger=None):
        super().__init__(daemon=True)
        self.detector = detector_engine
        self.on_presence_change = on_presence_change
        self.lock_delay_seconds = lock_delay
        self.camera_index = camera_index
        self.logger = logger

        self.is_running = False
        self._lock = threading.Lock()
        self.last_presence_state = True
        self.no_face_start_time = None

        # --- NEW: Startup grace period ---
        self.start_time = None
        self.grace_period_seconds = 5

    def run(self):
        self.is_running = True
        self.start_time = time.time()  # Record the start time
        if self.logger: self.logger.info(f"Presence monitor thread started with {self.detector.__class__.__name__}.")

        cap = cv2.VideoCapture(self.camera_index)
        if not cap.isOpened():
            if self.logger: self.logger.error(f"Could not open camera with index {self.camera_index}.")
            self.is_running = False
            return

        while self.is_running:
            ret, frame = cap.read()
            if not ret:
                if self.logger: self.logger.warning("Failed to grab frame. Retrying...")
                time.sleep(1)
                continue

            # --- NEW: Check if grace period is active ---
            if time.time() - self.start_time < self.grace_period_seconds:
                # During the grace period, we assume the user is present
                self._update_state(is_present=True)
                time.sleep(0.5)  # Check less frequently during startup
                continue

            face_present = self.detector.detect(frame)
            self._update_state(face_present)
            time.sleep(0.1)

        cap.release()
        if self.logger: self.logger.info("Presence monitor thread stopped and camera released.")

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
                    if self.logger: self.logger.info("Presence DETECTED.")
            else:
                if self.no_face_start_time is None:
                    self.no_face_start_time = time.time()

                elapsed = time.time() - self.no_face_start_time
                if elapsed >= self.lock_delay_seconds:
                    if self.last_presence_state:
                        self.last_presence_state = False
                        self.on_presence_change(False)
                        if self.logger: self.logger.warning(
                            f"Absence detected for {self.lock_delay_seconds} seconds. Signaling to lock.")