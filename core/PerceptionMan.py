import jetson.inference
import jetson.utils
from imutils.video import FPS

import cv2
import time

from utils.ImageSources import ImageSource, LocalVideo, LocalImage, CSICamera
from utils.PerceptionUtils import BoundingBox

class PerceptionMan:
    """
    Perception subsystem management module for object detection and object tracking.
    args:
    - net: Pre-trained network to use for object detection (ssd-mobilenet-v2 by default).
    - conf: Minimum confidence threshold to qualify as a detected object (0.5 by default).
    """

    # Number of frames before tracker is reset to account for accumulated error.
    RESET_TRACKER_FREQ = 40

    def __init__(self, network='ssd-mobilenet-v2', threshold=0.5):
        # Load pre-trained object detection network.
        self.net = jetson.inference.detectNet(network=network, threshold=threshold)


    def DetectObjects(self, image, width, height):
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


    def InitTracker(self, firstFrame, bbox):
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

        # CSRT tracker yields higher tracking accuracy with slower throughput.
        # Since we are ussing MOSSE for higher throughput, we need to run object
        # detection to recenter the tracker every certain number of frames.
        self.tracker = cv2.TrackerMOSSE_create()
        success = self.tracker.init(firstFrame, (x1, y1, width, height))

        # Update current bounding box.
        self.currBoundingBox = bbox

        return success


    def TrackObjectInNewFrame(self, currFrame):
        """
        Tracks the previously defined target (during initialization) in the current frame.
        :param currFrame: Current frame in which to look for target.
        :return success:  True if tracking in the current frame succeeded, false otherwise.
        :return opticalFlow: Vector from the center of the previous bounding box to the current one (i.e. object movement).
        :return newBbox: New bounding box around target object.
        """
        success, newBbox = self.tracker.update(currFrame)

        # Turn new bbox into our definition of a bbox (note: tracker's bbox uses width and height instead of a second point).
        width = newBbox[2]
        height = newBbox[3]
        newBbox = BoundingBox(left=newBbox[0], top=newBbox[1],
                               right=newBbox[0] + width, bottom=newBbox[1] + height)

        # Calculate optical flow using the two most recent bboxes and update current bbox.
        opticalFlow = self.currBoundingBox.VectorTo(newBbox)
        self.currBoundingBox = newBbox

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

        detections, _ = self.DetectObjects(frame, width, height)
        resetBbox = self.FindClassInDetections(detections, classID)

        if resetBbox is not None:
            self.InitTracker(frame, resetBbox)



# Outline of full system CSM if only perception code was running.

if __name__ == '__main__':

    # Something like this but for the CSM seeing perception modules
    # is in SystemMan (so you can import anything from the perception dir)
    import sys
    sys.path.append("../csm")
    from CameraMan import CameraMan

    # If not path is specified, CameraMan instantiates a CSICamera image source.
    source = CameraMan()

    perception = PerceptionMan()

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

        # Since the remote interface isn't set up yet, this part simulates choosing one of the bounding boxes returned
        # from object detection (the classID is set manually here, assuming that the target is a human)
        # Once the remote interface works, we would extract the class ID from the selected bounding box and save it
        # to reset the tracker every n frames. Here, we set it manually to 1 (person).
        # See helper method for more info.
        initialBbox = perception.FindClassInDetections(detections, classID=1)

        # Now that we have a bounding box returned from the "remote interface", we can initialize the
        # tracker using said bounding box.
        # Note: Here, we assume that the target hasn't moved from its original location since we are using that same
        # bounding box.
        frame, width, height = source.Capture()
        perception.InitTracker(frame, initialBbox)

        # Count number of frames so we can reset tracker every n frames
        framesSinceReset = 0

        # Now we can begin the main program/tracking loop.
        while True:

            # Get latest frame.
            frame, width, height = source.Capture()

            if framesSinceReset == perception.RESET_TRACKER_FREQ:
                # Reset tracker every n frames using object detection since it accumulates error over time
                # Note: There can only be one human present per frame in this case
                perception.ResetTracker(frame, width, height, classID=1)
                framesSinceReset = 0

            # Track previously defined object in latest frame.
            success, opticalFlow, newBbox = perception.TrackObjectInNewFrame(frame)
            framesSinceReset += 1

            if success:
                # We can use the opticalFlow here (x, y) and send it to the motors.
                # For now, we draw the latest bbox and print out the optical flow.
                cv2.rectangle(frame, newBbox.topLeft, newBbox.bottomRight, (0, 0, 255), 2)
                print(opticalFlow)
            else:
                # There was a tracking error, we need to handle it by resetting the tracker using
                # object detection.
                perception.ResetTracker(frame, width, height, classID=1)

            # For testing purposes, let's display the results on a window.
            cv2.imshow("Tracking Result", frame)

            # Processor yield time (in ms) to allow for multitasking.
            keyCode = cv2.waitKey(1)

            # Stop the program on the ESC key
            if keyCode & 0xFF == 27:
                 break

    finally:
        # Terminate resources
        source.Release()
        cv2.destroyAllWindows()

