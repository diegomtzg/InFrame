from ImageSources import CSICamera

class CameraMan():
    """
    Manager module for Jetson Nano's CSI Camera.
    See CSICamera class in ImageSources for more information.
    """

    def __init__(self):
        self.camera = CSICamera()

    def Capture(self):
        """
        API function call for pulling the next frame from camera.
        :returns: frame, width, height
        """
        return self.camera.getFrame()

    def Release(self):
        """
        Deallocates camera resources.
        """
        self.camera.close()
