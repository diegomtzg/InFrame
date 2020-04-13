import CommsMan as CommsMan
import StorageMan as StorageMan
import MotorMan as MotorMan
import CameraMan as CameraMan
import PerceptionMan as PerceptionMan

from CommsMan import CommsMan
from StorageMan import StorageMan
from MotorMan import MotorMan
from CameraMan import CameraMan
from PerceptionMan import PerceptionMan

# from ImageSources import ImageSource, LocalVideo, StillImage, Camera
# from PerceptionUtils import BoundingBox

import queue
import threading
import time
import sys

class SystemMan():

    def __init__(self):
        self.running = True
        self.inFrame = False
        self.currVideo = 0

        # Instantiate Subsystems
        self.per = PerceptionMan(threshold=0.5)
        self.cam = CameraMan("../testData/testOutput.mp4")
        self.mot = MotorMan()
        

        self.sto = StorageMan()
        self.comQ, self.comT = queue.Queue(maxsize=1), queue.Queue(maxsize=1)
        self.com = CommsMan(self.comQ, self.comT)

    def sendMessageToRemote(self, message):
        self.com.sendMessageToRemote(message)

    def terminateCommsMan(self):
        return self.com.terminateCommsMan()

    def simulateReceiveBT(self, message):
        self.com.simulateReceiveBT(message)

    def simulateLogBluetooth(self):
        return self.com.simulateLogBluetooth()

    def SHUTDOWN(self):
        self.simulateReceiveBT("Terminate")

    def launch(self):
        # Instantiate and launch in threads: CommsMan, StorageMan
        comThread = threading.Thread(target=(self.com.launch))
        stoThread = threading.Thread(target=(self.sto.launch))
        comThread.start()
        stoThread.start()

        while self.running:

            if not self.comQ.empty():
                # Pull and process message from CommsMan
                msg = self.comQ.get()

                print("Main         : received message: %s" % msg)

                # If msg commands new target selection
                if (msg == "Terminate"):
                    break
                elif (msg != ''):
                    # Restart PerceptionMan.

                    # Detect objects in the first frame.

                    # Choose the target.

                    # If target already being tracked
                    if self.inFrame:
                        # Signal to StorageMan to compile frames.
                        self.sto.compile("../testData/video%d.mp4" % self.currVideo, 30)
                        self.currVideo += 1
                        stoThread.join()
                        
                        # Relaunch CameraMan with new source
                        self.sto = CameraMan(msg)
                        stoThread = threading.Thread(target=(self.sto.launch))
                        stoThread.start()

            elif self.inFrame:
                # Request frame from CameraMan
                frame, frame_width, frame_height = self.cam.capture()

                # Send frame data to StorageMan
                self.sto.appendFrame(frame, frame_width, frame_height)

                # Track object in new frame
                success, optical_flow, new_bbox = self.per.track_object_in_new_frame(frame)

                if success:
                    # Generate bounding box
                    # Send optical flow to MotorMan
                    self.mot.adjustOrientation(optical_flow)
                else:
                    # Indicate failure
                    print("SystemMan    : Tracking error.")

        # Terminate CommsMan & rejoin thread.
        if (self.com.terminateCommsMan() == -1):
            raise TimeoutError
        comThread.join()

        # Signal to StorageMan to compile frames, terminate thread.
        self.sto.compile("../testData/video%d.mp4" % self.currVideo, 30)
        stoThread.join()        


if __name__ == '__main__':
    # test SystemMan interactions
    sys = SystemMan()
    sysThread = threading.Thread(target=sys.launch)
    sysThread.start()

    start_time = time.time()

    # Simulate message send requests to remote
    sys.sendMessageToRemote("Target Selection Alternatives")
    sys.sendMessageToRemote("Bounding Boxes for Targets")

    # Simulate message retrieval from "Bluetooth" channel
    sys.simulateReceiveBT("Target Selection")

    # Confirm message retrieval
    # testOutputBT = sys.simulateLogBluetooth()
    # print("Main         : Bluetooth message log:", testOutputBT)

    print(time.time() - start_time)

    sys.SHUTDOWN()
