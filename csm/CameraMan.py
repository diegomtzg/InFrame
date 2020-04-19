from ImageSources import CSICamera, LocalVideo

class CameraMan():
    """
    Manager module for Jetson Nano's CSI Camera (or locally
    saved video for testing purposes).
    See CSICamera class in ImageSources for more information.
    """

    def __init__(self, path=None):
        """
        Initializes the input stream from the CSI camera by default.
        For testing purposes, if a path is specified, it treats a
        locally saved video as its input.
        """
        if path is None:
            self.source = CSICamera()
        else:
            self.source = LocalVideo(path)


    def Capture(self):
        """
        API function call for pulling the next frame from camera.
        :returns: frame, width, height
        """
        return self.source.GetFrame()


    def Release(self):
        """
        Deallocates camera resources.
        """
        self.source.Close()
