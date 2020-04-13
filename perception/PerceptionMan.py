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
    - net: Pre-trained network to use for object detection (ssd-mobilenet-v2 by default).
    - conf: Minimum confidence threshold to qualify as a detected object (0.5 by default).
    """

    def __init__(self, network='ssd-mobilenet-v2', threshold=0.5):
        # Load pre-trained object detection network.
        self.net = jetson.inference.detectNet(network=network, threshold=threshold)

        # CSRT tracker yields higher tracking accuracy with slower throughput.
        self.tracker = cv2.TrackerCSRT_create()


    def detectObjects(self, image, width, height):
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
        cudaImg = ImageSource.rgb2crgba(image)

        # Detect objects in a given image and overlay results on top of it.
        detections = self.net.Detect(cudaImg, width, height)

        return detections, cudaImg


    def initTracker(self, firstFrame, bbox):
        """
        Initializes a CSRT tracker to track the object in the given bounding box.
        :param firstFrame: The first frame of the video in which the subject will be tracked.
        :param bbox: The box surrounding the target object (BoundingBox from PerceptionUtils).
        :return success: True if tracker was successfully initialized, false otherwise.
        """
        x1, y1 = bbox.topLeft
        x2, y2 = bbox.bottomRight

        # Tracker API uses width and height to define second point.
        width = x2 - x1
        height = y2 - y1
        success = self.tracker.init(firstFrame, (x1, y1, width, height))

        # Update current bounding box.
        self.currBoundingBox = bbox

        return success


    def trackObjectInNewFrame(self, curr_frame):
        """
        Tracks the previously defined target (during initialization) in the current frame.
        :param curr_frame: Current frame in which to look for target.
        :return success:  True if tracking in the current frame succeeded, false otherwise.
        :return opticalFlow: Vector from the center of the previous bounding box to the current one (i.e. object movement).
        :return newBbox: New bounding box around target object.
        """
        success, newBbox = self.tracker.update(curr_frame)

        # Turn new bbox into our definition of a bbox (note: tracker's bbox uses width and height instead of a second point).
        width = newBbox[2]
        height = newBbox[3]
        newBbox = BoundingBox(left=newBbox[0], top=newBbox[1],
                               right=newBbox[0] + width, bottom=newBbox[1] + height)

        # Calculate optical flow using the two most recent bboxes and update current bbox.
        opticalFlow = self.currBoundingBox.vector_to(newBbox)
        self.currBoundingBox = newBbox

        return success, opticalFlow, newBbox



# Test Script
if __name__ == '__main__':
    source = CSICamera(sensor_mode=3)
    perception = PerceptionMan()
    display = jetson.utils.glDisplay()

    try:
        fps = FPS().start()
        while True:
            last_time = time.time()
            frame, width, height = source.getFrame()
            detections, result_img = perception.detectObjects(frame, width, height)

            display.RenderOnce(result_img, width, height)
            print("Elapsed Time: ", time.time() - last_time)

            # For tracking
            # cv2.imshow("CSI Camera", frame)
            #
            # # Processor yield time to allow for multitasking.
            # keyCode = cv2.waitKey(1)
            #
            # # Stop the program on the ESC key
            # if keyCode & 0xFF == 27:
            #     break

            fps.update()
    finally:
        # Benchmark performance
        fps.stop()
        print("Approx FPS: %.2f" % fps.fps())

        # Terminate resources
        source.close()
        cv2.destroyAllWindows()

