import queue
import threading
import time
import cv2
import sys

import utils.Exceptions as newExceptions
from utils.PerceptionUtils import BoundingBox
from utils.ImageSources import ImageSource

from CommsMan import CommsMan
from StorageMan import StorageMan
from MotorMan import MotorMan
from CameraMan import CameraMan
from PerceptionMan import PerceptionMan


class SystemMan():

    def __init__(self):
        self.running = True
        self.inFrame = False
        self.currVideo = 0
        self.framesSinceReset = -1

        # Instantiate sequential subsystems
        self.per = PerceptionMan()
        self.cam = CameraMan(onlyDetect=False)
        self.mot = MotorMan()

        # Instantiate and launch in threads: CommsMan, StorageMan
        self.comQ, self.comT = queue.Queue(maxsize=1), queue.Queue(maxsize=1)
        self.com = CommsMan(self.comQ, self.comT)
        self.comThread = threading.Thread(target=(self.com.Launch))
        self.comThread.start()

        self.sto = StorageMan()
        self.stoThread = threading.Thread(target=(self.sto.Launch))
        self.stoThread.start()

    def SendMessageToRemote(self, message):
        """
        API for indicating to SystemMan to send a message to the remote interface.
        :param message: String message to be sent.
        """
        self.com.SendMessageToRemote(message)

    def SimulateReceiveBT(self, message):
        """
        API for simulating the CSM's receiving of a Bluetooth message.
        :param message: String message to be received and operated.
        """
        self.com.SimulateReceiveBT(message)

    def SimulateLogBluetooth(self):
        """
        API for retrieving the simulated log of messages marked to be sent over Bluetooth.
        :return: String representing message log.
        """
        return self.com.SimulateLogBluetooth()

    def SHUTDOWN(self):
        """
        API for signaling entire system to shut down (including all threads for CSM modules).
        """
        self.SimulateReceiveBT("Terminate")

    def compileFrames(self):
        self.sto.Compile("../testData/video%d.mp4" % self.currVideo, 30)
        self.stoThread.join()

        self.currVideo += 1

    def restartNewVideoStorage(self):
        self.sto = StorageMan()
        self.stoThread = threading.Thread(target=(self.sto.launch))
        self.stoThread.start()

    def parseMsgForBoundingBox(self, msg):
        a = msg.split(";")
        l,t,r,b = int(a[0]), int(a[1]), int(a[2]), int(a[3])

        return BoundingBox(left=l, top=t, right=r, bottom=b)

    def Launch(self):
        """
        Main function for launching the System.
        """

        while self.running:

            if not self.comQ.empty():
                # Pull and process message from CommsMan
                msg = self.comQ.get()

                print("Main         : received message: %s" % msg)

                # TODO(@Ike): Gracefully handle unknown/invalid messages without crashing

                # Shut down the system
                if (msg == "Terminate"):
                    break

                # Stop filming current target and compile footage
                elif (msg == "Finish"):
                    if self.inFrame:
                        # Signal to StorageMan to compile frames.
                        self.compileFrames()

                        # Relaunch StorageMan with new source
                        self.restartNewVideoStorage()

                        self.inFrame = False
                    else:
                        raise newExceptions.BadState("IDLE", "FILMING")

                # Start recording specific target
                elif (msg == "Start"):
                    # Once we get a command, we detect objects and send them back to the user so that
                    # they can select a target.
                    # Note: For info on the detections list returned from detectObjects, see jetson.inference.detectNet.Detection
                    # from here https://rawgit.com/dusty-nv/jetson-inference/python/docs/html/python/jetson.inference.html#detectNet
                    frame, width, height = self.cam.Capture()

                    # Transform image into RGBA space and place into a cuda container since object detection model expects it.
                    cudaImg = ImageSource.rgb2crgba(frame)
                    detections, _ = self.per.DetectObjects(cudaImg, width, height)

                    # TODO(@Ike - once iOS working): Send {detections, frame, width, height} to Remote Interface
                    pass

                    # Since the remote interface isn't set up yet, this part simulates choosing one of the bounding boxes returned
                    # from object detection (the classID is set manually here, assuming that the target is a human)
                    # Once the remote interface works, we would extract the class ID from the selected bounding box and save it
                    # to reset the tracker every n frames. Here, we set it manually to 1 (person).
                    iBB = self.per.FindClassInDetections(detections, classID=1)
                    receivedSimStr = str(iBB.topLeft[0]) + ";" + str(iBB.topLeft[1]) + ";" + str(iBB.bottomRight[0]) + ";" + str(iBB.bottomRight[0])
                    self.SimulateReceiveBT(receivedSimStr)

                # Specific target selected, msg contains information about selected target
                else:
                    self.inFrame = True

                    # Parse message from remote interface into initial, user-selected bounding box
                    initialBbox = self.parseMsgForBoundingBox(msg)

                    # Now that we have a bounding box returned from the "remote interface", we can initialize the
                    # tracker using said bounding box.
                    # Note: Here, we assume that the target hasn't moved from its original location since we are using that same
                    # bounding box.
                    frame, width, height = self.cam.Capture()
                    self.per.InitTracker(frame, initialBbox)

                    self.framesSinceReset = 0

            # Main Tracking Code: Target already selected - iterate & adjust motors
            elif self.inFrame:
                # Request frame from CameraMan
                frame, frame_width, frame_height = self.cam.Capture()

                if self.framesSinceReset == self.per.RESET_TRACKER_FREQ:
                    # Reset tracker every n frames using object detection since it accumulates error over time
                    # Note: There can only be one human present per frame in this case
                    self.per.ResetTracker(frame, width, height, classID=1)
                    self.framesSinceReset = 0

                # Track previously defined object in latest frame.
                success, opticalFlow, newBbox = self.per.TrackObjectInNewFrame(frame)
                self.framesSinceReset += 1

                if success:
                    # We can use the opticalFlow here (x, y) and send it to the motors.
                    # For now, we draw the latest bbox and print out the optical flow.
                    cv2.rectangle(frame, newBbox.topLeft, newBbox.bottomRight, (0, 0, 255), 2)
                    print(opticalFlow)
                else:
                    # There was a tracking error, we need to handle it by resetting the tracker using
                    # object detection.
                    self.per.ResetTracker(frame, width, height, classID=1)

                # TODO(@Ike): Send frame data to StorageMan (@Diego should we leave storage for post-demo2? I say ay)
                # self.sto.appendFrame(frame, frame_width, frame_height)

                # For testing purposes, display the results on a window.
                cv2.imshow("Tracking Result", frame)

                # Processor yield time (in ms) to allow for multitasking.
                keyCode = cv2.waitKey(1)

                # Stop the program on the ESC key
                if keyCode & 0xFF == 27:
                    break

        # Destroy/deallocate resources
        self.cam.Release()
        cv2.destroyAllWindows()

        # Terminate CommsMan & rejoin thread.
        if (self.com.TerminateCommsMan() == -1):
            raise TimeoutError
        self.comThread.join()

        self.compileFrames()


if __name__ == '__main__':
    # Test SystemMan interactions
    system = SystemMan()
    sysThread = threading.Thread(target=system.Launch)
    sysThread.start()

    # Simulate repeated message retrievals from Remote Interface until "Terminate" message is received and System shuts down.
    userInput = ""
    while (userInput != "Terminate"):
        print("Enter simulated BT message: ")
        userInput = input()
        print("UserInput: %s" % userInput)
        system.SimulateReceiveBT(userInput)

