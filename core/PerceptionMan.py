import jetson.inference
import jetson.utils
from imutils.video import FPS

import cv2
import time

from utils.ImageSources import ImageSource, LocalVideo, LocalImage, CSICamera
from utils.PerceptionUtils import BoundingBox
from CameraMan import CameraMan

class PerceptionMan:
    """
    Perception subsystem management module for object detection and object tracking.
    args:
    - net: Pre-trained network to use for object detection (ssd-mobilenet-v2 by default).
    - conf: Minimum confidence threshold to qualify as a detected object (0.5 by default).
    """

    # Number of frames before tracker is reset to account for accumulated error.
    RESET_TRACKER_FREQ = 20

    def __init__(self, network='ssd-mobilenet-v2', threshold=0.5):
        # Load pre-trained object detection network.
        self.net = jetson.inference.detectNet(network=network, threshold=threshold)


    def DetectObjects(self, image, width, height):
        """
        Detects objects in a given image according to the confidence threshold
        specified in the constructor. Overlays results on input image by default.
        :param image: The input image in RGBA space like network expects.
        :param width: Width of the input image.
        :param height: Height of the input image.
        :return detections: A list of the detected object bounding boxes (type jetson.inference.detectNet.Detection)
        :return result_img: CUDA rgba image with object detection results overlaid
        """

        last_time = time.time()

        # Transform image into RGBA space and place into a cuda container since object detection model expects it.
        #cudaImg = ImageSource.rgb2crgba(image)

        # Detect objects in a given image and overlay results on top of it.
        detections = self.net.Detect(image, width, height)

        print("DETECT OBJECTS TIME", time.time() - last_time)

        return detections, image


    def InitTracker(self, firstFrame, bbox):
        """
        Initializes a CSRT tracker to track the object in the given bounding box.
        :param firstFrame: The first frame of the video in which the subject will be tracked.
        :param bbox: The box surrounding the target object (BoundingBox from PerceptionUtils).
        :return success: True if tracker was successfully initialized, false otherwise.
        """

        last_time = time.time()

        x1, y1 = bbox.topLeft
        x2, y2 = bbox.bottomRight

        # Tracker API uses width and height to define second point.
        width = x2 - x1
        height = y2 - y1

        # CSRT tracker yields higher tracking accuracy with slower throughput.
        # Since we are ussing MOSSE for higher throughput, we need to run object
        # detection to recenter the tracker every certain number of frames.
        self.tracker = cv2.TrackerMOSSE_create()
        success = self.tracker.init(firstFrame, (x1, y1, width, height))

        # Update current bounding box.
        self.currBoundingBox = bbox

        print("INIT TRACKER TIME", time.time() - last_time)

        return success


    def TrackObjectInNewFrame(self, currFrame):
        """
        Tracks the previously defined target (during initialization) in the current frame.
        :param currFrame: Current frame in which to look for target.
        :return success:  True if tracking in the current frame succeeded, false otherwise.
        :return opticalFlow: Vector from the center of the previous bounding box to the current one (i.e. object movement).
        :return newBbox: New bounding box around target object.
        """

        last_time = time.time()

        success, newBbox = self.tracker.update(currFrame)

        # Turn new bbox into our definition of a bbox (note: tracker's bbox uses width and height instead of a second point).
        width = newBbox[2]
        height = newBbox[3]
        newBbox = BoundingBox(left=newBbox[0], top=newBbox[1],
                               right=newBbox[0] + width, bottom=newBbox[1] + height)

        # Calculate optical flow using the two most recent bboxes and update current bbox.
        opticalFlow = self.currBoundingBox.VectorTo(newBbox)
        self.currBoundingBox = newBbox

        print("TRACKING TIME", time.time() - last_time)

        return success, opticalFlow, newBbox


    def FindClassInDetections(self, detectionsList, classID):
        """
        Finds the first bounding box pertaining to an object with a target classID
        in a list of detection results.
        Note: Class ID is an index into this list of classes:
        https://github.com/dusty-nv/jetson-inference/blob/master/data/networks/ssd_coco_labels.txt
        :param detectionsList: Results from object detection.
        :param classID: target classID to look for.
        :return: bounding box around target with specified classID or none if not found
        """
        target = None

        for detection in detectionsList:
            if detection.ClassID == classID:
                target = detection

        if target is None:
            return None
        else:
            return BoundingBox(left=target.Left, top=target.Top, right=target.Right, bottom=target.Bottom)


    def ResetTracker(self, frame, width, height, classID):
        """
        Re-initializes the tracker to center on a bounding box returned from
        object detection with a given classID.
        :param frame, width, height: Latest frame and frame metadata
        :param classID: desired classID to recenter tracker on, there can only be one per frame
        See FindClassInDetections method for more information on classID
        """
        print("Resetting tracker...")

        cudaImg = ImageSource.rgb2crgba(frame)
        detections, _ = self.DetectObjects(cudaImg, width, height)
        resetBbox = self.FindClassInDetections(detections, classID)

        if resetBbox is not None:
            self.InitTracker(frame, resetBbox)



# Outline of full system CSM if only perception code was running.
if __name__ == '__main__':
    # If not path is specified, CameraMan instantiates a CSICamera image source.
    source = CameraMan()
    perception = PerceptionMan(threshold=0.3)
    display = jetson.utils.glDisplay()
    testFile= open('test.txt', 'w+')

    # I put everything in a try block so that even when I interrupt the program
    # with ctrl + c we still free the camera and all the other resources inside
    # of the finally block.
    try:
        # Here, the system is idle, waiting for a command from the remote interface.

        # Once we get a command, we detect objects and send them back to the user so that
        # they can select a target.
        # Note: For info on the detections list returned from detectObjects, see jetson.inference.detectNet.Detection
        # from here https://rawgit.com/dusty-nv/jetson-inference/python/docs/html/python/jetson.inference.html#detectNet
        frame, width, height = source.Capture()
        detections, _ = perception.DetectObjects(frame, width, height)

        # TODO(@Ike): Send image to phone to select target class

        # Since the remote interface isn't set up yet, this part simulates choosing one of the bounding boxes returned
        # from object detection (the classID is set manually here, assuming that the target is a human)
        # Once the remote interface works, we would extract the class ID from the selected bounding box and save it
        # to reset the tracker every n frames. Here, we set it manually to 1 (person).
        # See helper method for more info.
        currBbox = perception.FindClassInDetections(detections, classID=1)

        # Now we can begin the main program/tracking loop.
        fps = FPS().start()
        while True:
            # Get latest frame.
            frame, width, height = source.Capture()
            detections, _ = perception.DetectObjects(frame, width, height)
            display.RenderOnce(frame, width, height)

            newBbox = perception.FindClassInDetections(detections, classID=1)

            # If we found the target, update bbox and print results.
            if newBbox is not None:
                opticalFlow = currBbox.VectorTo(newBbox)
                testFile.write("%d, %d\n" % (opticalFlow))

            fps.update()

    finally:
        # Terminate resources
        source.Release()
        fps.stop()
        print("FPS: ", fps.fps())

