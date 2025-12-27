import cv2
import time


class CaptureReturn:
    def __init__(self, ret, cv2_image, timestamp):
        self.timestamp = timestamp
        self.valid = ret
        self.image = cv2_image


class CaptureDevice:
    def __init__(self, camera_id, width, height, fps):
        self.capture = cv2.VideoCapture()
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self.capture.set(cv2.CAP_PROP_FPS, fps)
        self.capture.open(camera_id)

        if self.capture.isOpened() is False:
            raise Exception(f"Failed to open camera ID: {camera_id}")

        self.fps = self.capture.get(cv2.CAP_PROP_FPS)
        self.width = width
        self.height = height
        self.camera_id = camera_id
        self.wait_interval_sec = 0.1 / fps

    def __del__(self):
        self.capture.release()

    def wait(self):
        time.sleep(self.wait_interval_sec)

    def read_image(self):
        if self.capture.isOpened() is False:
            raise Exception("Could not detect new frame, camera device closed")

        ret, cv2_image = self.capture.read()
        timestamp = int(self.capture.get(cv2.CAP_PROP_POS_MSEC))
        capture_return = CaptureReturn(ret, cv2_image, timestamp)
        return capture_return
