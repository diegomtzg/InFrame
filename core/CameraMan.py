from utils.ImageSources import CSICamera, LocalVideo

import jetson.utils

class CameraMan():
    """
    Manager module for Jetson Nano's CSI Camera (or locally
    saved video for testing purposes).
    See CSICamera class in ImageSources for more information.
    """

    def __init__(self, path=None, onlyDetect=True, width=1280, height=720, camFile='0'):
        """
        Initializes the input stream from the CSI camera by default.
        For testing purposes, if a path is specified, it treats a
        locally saved video as its input.
        """
        if path is None:
            if onlyDetect:
                # Can only return RGBA image, so only good for standalone object detection.
                self.onlyDetecting = True
                self.source = jetson.utils.gstCamera(width, height, camFile)
            else:
                self.onlyDetecting = False
                self.source = CSICamera()
        else:
            self.source = LocalVideo(path)


    def Capture(self):
        """
        API function call for pulling the next frame from camera.
        :returns: frame, width, height
        """
        if self.onlyDetecting:
            # Much faster than capturing regular image and then transforming.
            return self.source.CaptureRGBA()
        else:
            return self.source.GetFrame()


    def Release(self):
        """
        Deallocates camera resources.
        """
        if not self.onlyDetecting:
            self.source.Close()
