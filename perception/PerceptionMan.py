import jetson.inference
import jetson.utils
from imutils.video import FPS

import cv2
import time

from ImageSources import ImageSource, LocalVideo, LocalImage, CSICamera
from PerceptionUtils import BoundingBox

class PerceptionMan:
    """
    Perception subsystem management module for object detection and object tracking.
    args:
    - net: Pre-trained network to use for object detection (ssd_mobilenet_v2 by default).
    - conf: Minimum confidence threshold to qualify as a detected object (0.5 by default).
    """

    def __init__(self, network='ssd-mobilenet-v2', threshold=0.3):
        # Load pre-trained object detection network.
        self.net = jetson.inference.detectNet(network=network, threshold=threshold)

        # CSRT tracker yields higher tracking accuracy with slower throughput.
        self.tracker = cv2.TrackerCSRT_create()
        # self.tracker = cv2.TrackerMOSSE_create()
        # self.tracker = cv2.TrackerMedianFlow_create()


    def detect_objects(self, image, width, height):
        """
        Detects objects in a given image according to the confidence threshold
        specified in the constructor. Overlays results on input image by default.
        :param image: The input image in standard RGB space.
        :param width: Width of the input image.
        :param height: Height of the input image.
        :return detections: A list of the detected object bounding boxes (type jetson.inference.detectNet.Detection)
        :return result_img: CUDA rgba image with object detection results overlaid
        """
        # Transform image into RGBA space and place into a cuda container since object detection model expects it.
        cuda_img = ImageSource.rgb2crgba(image)

        # Detect objects in a given image and overlay results on top of it.
        detections = self.net.Detect(cuda_img, width, height)

        return detections, cuda_img


    def initialize_tracker(self, first_frame, bbox):
        """
        Initializes a CSRT tracker to track the object in the given bounding box.
        :param first_frame: The first frame of the video in which the subject will be tracked.
        :param bbox: The box surrounding the target object (BoundingBox from PerceptionUtils).
        :return success: True if tracker was successfully initialized, false otherwise.
        """
        x1, y1 = bbox.top_left
        x2, y2 = bbox.bottom_right

        # Tracker API uses width and height to define second point.
        width = x2 - x1
        height = y2 - y1
        success = self.tracker.init(first_frame, (x1, y1, width, height))

        # Update current bounding box.
        self.curr_bounding_box = bbox

        return success


    def track_object_in_new_frame(self, curr_frame):
        """
        Tracks the previously defined target (during initialization) in the current frame.
        :param curr_frame: Current frame in which to look for target.
        :return success:  True if tracking in the current frame succeeded, false otherwise.
        :return optical_flow: Vector from the center of the previous bounding box to the current one (i.e. object movement).
        :return new_bbox: New bounding box around target object.
        """
        success, new_bbox = self.tracker.update(curr_frame)

        # Turn new bbox into our definition of a bbox (note: tracker's bbox uses width and height instead of a second point).
        width = new_bbox[2]
        height = new_bbox[3]
        new_bbox = BoundingBox(left=new_bbox[0], top=new_bbox[1],
                               right=new_bbox[0] + width, bottom=new_bbox[1] + height)

        # Calculate optical flow using the two most recent bboxes and update current bbox.
        optical_flow = self.curr_bounding_box.vector_to(new_bbox)
        self.curr_bounding_box = new_bbox

        return success, optical_flow, new_bbox



# Test Script
if __name__ == '__main__':
    source = CSICamera(sensor_mode=3)
    fps = FPS().start()

    try:
        while True:
            frame, frame_width, frame_height = source.get_frame()

            cv2.imshow("CSI Camera", frame)

            # Processor yield time to allow for multitasking.
            keyCode = cv2.waitKey(1)

            # Stop the program on the ESC key
            if keyCode & 0xFF == 27:
                break

            fps.update()
    finally:
        # Benchmark performance
        fps.stop()
        print("Approx FPS: %.2f" % fps.fps())

        # Terminate resources
        source.close()
        cv2.destroyAllWindows()

