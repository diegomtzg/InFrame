import jetson.utils

import cv2

class ImageSource:
    """
    Base class definition/interface for an image source.
    """

    def GetFrame(self):
        """
        Returns a single frame from the image source, as well as its width and height.
        args: None
        returns: frame, width, height
        """
        raise NotImplementedError


    def Close(self):
        """
        Closes/deallocates an image source, if necessary.
        args: None
        returns: None
        """
        raise NotImplementedError


    @staticmethod
    def rgb2crgba(rgb_frame):
        """
        Helper method that transforms a standard RGB frame to a frame with an alpha channel
        and inside of a cuda memory capsule to pass into the object detection network.
        args:
            - rgb_frame: Standard frame in RGB color space.
        returns: Frame in RGBA space and inside a cuda memory capsule.
        """

        # Add alpha channel (opacity) to image since network expects RGBA image.
        rgbaFrame = cv2.cvtColor(rgb_frame, cv2.COLOR_BGR2RGBA)

        # Convert image to cuda memory capsule (pycapsule) object to pass
        # memory efficiently (expected by network detect method).
        cudaFrame = jetson.utils.cudaFromNumpy(rgbaFrame)

        return cudaFrame


class CSICamera(ImageSource):
    """
    Defines an image source from the Jetson Nano's MIPI CSI camera.
    List available camera using v4l2-ctl --list-devices.

    :param sensor_id: Selects the camera (0 or 1 on Jetson Nano B01)
    :param sensor_mode: Sets resolution and frame rate on camera sensor.
        Sensor modes for our CSI Picam:
        [0] 3264 x 2464; 21 fps
        [1] 3264 x 1848; 28 fps
        [2] 1920 x 1080; 30 fps
        [3] 1280 x 720; 60 fps
        [4] 1280 x 720; 120 fps
    """

    def __init__(self, sensor_id=0, sensor_mode=3, flip_method=0, display_width=1280, display_height=720):
        gstreamerPipeline = "nvarguscamerasrc sensor_id=%d sensor_mode=%d ! "\
                             "video/x-raw(memory:NVMM) ! "\
                             "nvvidconv flip-method=%d ! "\
                             "video/x-raw, width=(int)%d, height=(int)%d, format=(string)BGRx ! "\
                             "videoconvert ! "\
                             "video/x-raw, format=(string)BGR ! appsink" \
                             % (sensor_id, sensor_mode, flip_method, display_width, display_height)

        self.camera = cv2.VideoCapture(gstreamerPipeline, cv2.CAP_GSTREAMER)

    def GetFrame(self):
        success, frame = self.camera.read()

        if not success:
            raise Exception('Could not read from camera')

        height, width = frame.shape[:2]

        return frame, width, height


    def Close(self):
        self.camera.release()


class LocalVideo(ImageSource):
    """
    Defines an image source from a locally stored video.
    """

    def __init__(self, path):
        self.video = cv2.VideoCapture(path)


    def GetFrame(self):
        success, frame = self.video.read()

        if not success:
            raise Exception('Could not read local video')

        height, width = frame.shape[:2]

        return frame, width, height


    def Close(self):
        self.video.release()


class LocalImage(ImageSource):
    """
    Defines an image source from a locally stored still image.
    Res argument in constructor resizes image to specified resolution (or 720p by default).
    """

    def __init__(self, path, res=(1280, 720)):
        self.img = cv2.imread(path, cv2.IMREAD_UNCHANGED)

        if self.img is None:
            raise Exception('Could not read image.')

        if res is not None:
            self.img = cv2.resize(self.img, res, interpolation=cv2.INTER_AREA)


    def GetFrame(self):
        height, width = self.img.shape[:2]

        return self.img, width, height


    def Close(self):
        # No deallocation necessary
        pass

