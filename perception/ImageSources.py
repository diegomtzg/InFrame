import cv2

import jetson.utils

class ImageSource:
    """
    Base class definition/interface for an image source.
    """

    def get_frame(self):
        """
        Returns a single frame from the image source, as well as its width and height.
        Frame must be in RGBA space and inside of a CUDA memory
        capsule as expected by the object detection network.
        args: None
        returns: frame, width, height
        """
        raise NotImplementedError


    def close(self):
        """
        Closes/deallocates an image source, if necessary.
        args: None
        returns: None
        """
        raise NotImplementedError


    def RGB_to_cudaRGBA(self, rgb_frame):
        """
        Transforms a standard RGB frame to a frame with an alpha channel
        and inside of a cuda memory capsule to pass into the object detection network.
        args:
            - rgb_frame: Standard frame in RGB color space.
        returns: Frame in RGBA space and inside a cuda memory capsule.
        """

        # Add alpha channel (opacity) to image since network expects RGBA image.
        rgba_frame = cv2.cvtColor(rgb_frame, cv2.COLOR_BGR2RGBA)

        # Convert image to cuda memory capsule (pycapsule) object to pass
        # memory efficiently (expected by network detect method).
        cuda_frame = jetson.utils.cudaFromNumpy(rgba_frame)

        return cuda_frame


class Camera(ImageSource):
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


    def close(self):
        # No deallocation necessary
        pass


class LocalVideo(ImageSource):
    """
    Defines an image source from a locally stored video.
    """

    def __init__(self, path):
        self.video = cv2.VideoCapture(path)


    def get_frame(self):
        success, frame = self.video.read()

        if not success:
            raise Exception('Could not read local video')

        height, width = frame.shape[:2]

        cuda_frame = super().RGB_to_cudaRGBA(frame)

        return cuda_frame, width, height


    def close(self):
        self.video.release()


class StillImage(ImageSource):
    """
    Defines an image source from a JPEG image.
    Res argument in constructor resizes image to specified resolution (or 720p by default).
    """

    def __init__(self, path, res=(1280, 720)):
        self.img = cv2.imread(path, cv2.IMREAD_UNCHANGED)

        if self.img is None:
            raise Exception('Could not read image.')

        if res is not None:
            self.img = cv2.resize(self.img, res, interpolation=cv2.INTER_AREA)


    def get_frame(self):
        height, width = self.img.shape[:2]
        rgba_frame = super().RGB_to_cudaRGBA(self.img)

        return rgba_frame, width, height


    def close(self):
        # No deallocation necessary
        pass
