import cv2

import jetson.utils


class Camera:
    """
    Defines an image source from the Jetson Nano's MIPI CSI camera.
    List available camera using v4l20ctl --list-devices.
    """

    def __init__(self, device_file='dev/video0'):
        self.camera = jetson.utils.gstCamera(1280, 720, device_file)


    def get_frame(self):
        # Capture frame and convert it to float4 RGBA.
        img, width, height = self.camera.CaptureRGBA()
        return img, width, height


class LocalVideo:
    """
    Defines an image source from a locally stored video.
    """

    def __init__(self, path):
        self.video = cv2.VideoCapture(path)


    def get_frame(self):
        success, frame = self.video.read()

        if not success:
            raise Exception('Could not read local video')

        width, height = frame.shape[:2]

        # Add alpha channel (opacity) to image since network expects RGBA image.
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)

        # Convert image to cuda memory capsule (pycapsule) object to pass
        # memory efficiently (expected by network detect method).
        cuda_frame = jetson.utils.cudaFromNumpy(frame)

        return cuda_frame, height, width


    def close(self):
        self.video.release()
