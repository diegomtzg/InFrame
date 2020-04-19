import queue
import threading
import time
import sys

# Add support for imports from perception directory.
sys.path.append("../perception")

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

        # Instantiate Subsystems
        self.per = PerceptionMan()
        self.cam = CameraMan()
        self.mot = MotorMan()

        self.sto = StorageMan()
        self.comQ, self.comT = queue.Queue(maxsize=1), queue.Queue(maxsize=1)
        self.com = CommsMan(self.comQ, self.comT)

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

    def Launch(self):
        """
        Main function for launching the System.
        """
        # Instantiate and launch in threads: CommsMan, StorageMan
        comThread = threading.Thread(target=(self.com.Launch))
        stoThread = threading.Thread(target=(self.sto.Launch))
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

                # A valid command has been received from remote interface
                # for SysMan to start recording a specific target
                elif (msg != ''):
                    # TODO: Re-instantiate CameraMan to update source

                    # TODO: Detect objects in the first frame.

                    # TODO: Choose the human (me).

                    # If target already being tracked
                    if self.inFrame:
                        # Signal to StorageMan to compile frames.
                        self.sto.Compile("../testData/video%d.mp4" % self.currVideo, 30)
                        self.currVideo += 1
                        stoThread.join()

                        # Relaunch CameraMan with new source
                        self.sto = CameraMan(msg)
                        stoThread = threading.Thread(target=(self.sto.launch))
                        stoThread.start()

            # Main Tracking Code: Target already selected - iterate & adjust motors
            elif self.inFrame:
                # Request frame from CameraMan
                frame, frame_width, frame_height = self.cam.capture()

                # Send frame data to StorageMan
                self.sto.appendFrame(frame, frame_width, frame_height)

                # Track object in new frame
                # success, optical_flow, new_bbox = self.per.track_object_in_new_frame(frame)
                success, optical_flow, new_bbox = mockTrackObjectInNewFrame(frame)

                if success:
                    # Generate bounding box
                    # Send optical flow to MotorMan
                    self.mot.processOpticalFlowCommand(optical_flow)
                else:
                    # Indicate failure
                    print("SystemMan    : Tracking error.")

        # Terminate CommsMan & rejoin thread.
        if (self.com.TerminateCommsMan() == -1):
            raise TimeoutError
        comThread.join()

        # Signal to StorageMan to compile frames, terminate thread.
        self.sto.Compile("../testData/video%d.mp4" % self.currVideo, 30)
        stoThread.join()


def mockTrackObjectInNewFrame(frame):
    success, optical_flow, new_bbox = 0, 0, 0
    return success, optical_flow, new_bbox

if __name__ == '__main__':
    # test SystemMan interactions
    sys = SystemMan()
    sysThread = threading.Thread(target=sys.Launch)
    sysThread.start()

    start_time = time.time()

    # Simulate message send requests to remote
    sys.SendMessageToRemote("Target Selection Alternatives")
    sys.SendMessageToRemote("Bounding Boxes for Targets")

    # Simulate message retrieval from "Bluetooth" channel
    sys.SimulateReceiveBT("Target Selection")

    # Confirm message retrieval
    # testOutputBT = sys.simulateLogBluetooth()
    # print("Main         : Bluetooth message log:", testOutputBT)

    print(time.time() - start_time)

    sys.SHUTDOWN()
