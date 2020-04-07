import jetson.utils

import cv2
from threading import Thread
from queue import Queue
import time

class ImageSource:
    """
    Base class definition/interface for an image source.
    """

    def get_frame(self):
        """
        Returns a single frame from the image source, as well as its width and height.
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
        rgba_frame = cv2.cvtColor(rgb_frame, cv2.COLOR_BGR2RGBA)

        # Convert image to cuda memory capsule (pycapsule) object to pass
        # memory efficiently (expected by network detect method).
        cuda_frame = jetson.utils.cudaFromNumpy(rgba_frame)

        return cuda_frame


class VideoStream(ImageSource):
    """
    Defines a concurrent image source from a video stream (either from a locally stored video
    or from the camera). Small modifications from imutils' FileVideoStream class.
    """

    def __init__(self, path, transform=None, queue_size=128):
        self.source = cv2.VideoCapture(path)
        self.queue = Queue(maxsize=queue_size)
        self.stopped = False
        self.transform = transform

        # VideoStream's thread runs update function to continuously read and store input frames.
        self.thread = Thread(target=self.update, args=())
        self.thread.daemon = True


    @classmethod
    def from_camera(cls, capture_width = 1280, capture_height = 720, framerate = 120, flip_method = 0):
        """
        Builds a video stream from the Jetson Nano's MIPI CSI camera.
        List available camera using v4l2-ctl --list-devices.
        """
        gstreamer_pipeline = "nvarguscamerasrc ! video/x-raw(memory:NVMM), " \
                             "width=(int)%d, height=(int)%d, format=(string)NV12, framerate=(fraction)%d/1 ! " \
                             "nvvidconv flip-method=%d ! videoconvert ! video/x-raw, format=(string)BGR ! appsink" \
                             % (capture_width, capture_height, framerate, flip_method)

        cls.source = cv2.VideoCapture(gstreamer_pipeline, cv2.CAP_GSTREAMER)
        return cls


    def start(self):
        # Start reading frames from video stream.
        self.thread.start()


    def update(self):
        """
        Main thread function. Continuously reads frames and stores in queue until there are none left.
        """
        while not self.stopped:
            if not self.queue.full():
                grabbed, frame = self.source.read()

                # End of video file, stop reading frames.
                if not grabbed:
                    self.stopped = True

                # If there are transforms to be done on frames, do here on producer
                # thread since it is usually way ahead of consumer thread.
                if self.transform is not None:
                    frame = self.transform(frame)

                # Add frame to the queue.
                self.queue.put(frame)
            else:
                # Recheck to see if frames have been read from queue in 10ms.
                time.sleep(0.1)

        # Deallocate VideoCapture stream.
        self.source.release()


    def get_frame(self):
        return self.queue.get()


    def more(self):
        # Returns True if there are still frames in the queue. If stream is not stopped, try to wait a moment
        tries = 0
        while self.queue.qsize() == 0 and not self.stopped and tries < 5:
            time.sleep(0.1)
            tries += 1

        return self.queue.qsize() > 0

    # Insufficient to have consumer use while(more()) which does
    # not take into account if the producer has reached end of
    # file stream.
    def running(self):
        return self.more() or not self.stopped


    def stop(self):
        """
        Manually stops producer thread. Waits until stream resources are released since
        producer thread might be still grabbing frame.
        """
        self.stopped = True
        self.thread.join()


class CSICamera(ImageSource):
    """
    Defines an image source from the Jetson Nano's MIPI CSI camera.
    List available camera using v4l20ctl --list-devices.
    """

    def __init__(self, capture_width=1280, capture_height=720, framerate=120, flip_method=0):
        gstreamer_pipeline = "nvarguscamerasrc ! video/x-raw(memory:NVMM), " \
        "width=(int)%d, height=(int)%d, format=(string)NV12, framerate=(fraction)%d/1 ! " \
        "nvvidconv flip-method=%d ! videoconvert ! video/x-raw, format=(string)BGR ! appsink" \
        % (capture_width, capture_height, framerate, flip_method)

        self.camera = cv2.VideoCapture(gstreamer_pipeline, cv2.CAP_GSTREAMER)

    def get_frame(self):
        success, frame = self.camera.read()

        if not success:
            raise Exception('Could not read from camera')

        height, width = frame.shape[:2]

        return frame, width, height


    def close(self):
        self.camera.release()


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

        return frame, width, height


    def close(self):
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


    def get_frame(self):
        height, width = self.img.shape[:2]

        return self.img, width, height


    def close(self):
        # No deallocation necessary
        pass

