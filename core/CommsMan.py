import threading
import queue
import time

import multiprocessing

class CommsMan():

    def __init__(self, commsQueue):
        # Sending data CommsMan --> SystemMan
        self.sysQueueSend = commsQueue
        # Sending data SystemMan --> CommsMan
        self.sysQueueRecv = multiprocessing.Queue(maxsize=1)

        # Queue from which Bluetooth cmds are simulated as being received
        self.btQueue = multiprocessing.Queue(maxsize=1)

        # Queue indicating CommsMan thread to terminate
        self.terminateComms = multiprocessing.Queue(maxsize=1)

        # Array representing log of messages marked to send out to remote interface
        self.testSendOutput = []

    def SendMessageToRemote(self, message):
        """
        External function which enables users to message CommsMan to send
        message to the remote interface via Bluetooth for user operation.
        :param message: Contents of message to send to remote (String)
        """
        self.sysQueueRecv.put(message)

    def TerminateCommsMan(self):
        """
        External function to terminate CommsMan thread operations.
        :return: Int 0 indicating no error terminating CommsMan, -1 indicating error (e.g. termination already signaled)
        """
        try:
            self.terminateComms.put(-1, block=False)
            return 0
        except:
            # If user spams terminateCommsMan, this will disable holding
            # the system up, handling exception raised by terminateComms
            # Queue being full during time of insertion.
            return -1

    def SimulateReceiveBT(self, message):
        """
        External function for simulating/testing CommsMan's ability to receive Bluetooth msgs
        and send them to SystemMan.
        :param message: Contents of message being received via "Bluetooth" (String)
        """
        try:
            self.btQueue.put(message, timeout=10)
        except:
            print("SRBT         : Bluetooth-Receive queue insertion blocked > 10s on: %s" % message)

    def SimulateLogBluetooth(self):
        """
        External function for printing the array log simulating messages to be sent out via Bluetooth.
        :return: String containing log contents
        """
        return str(self.testSendOutput)

    def Launch(self):
        # print("CommsMan     : Main thread launching.")
        while self.terminateComms.empty():
            if not self.btQueue.empty():
                message = self.btQueue.get()
                self.sendMessageToSystem(message)
            elif not self.sysQueueRecv.empty():
                message = self.sysQueueRecv.get()
                self.testSendOutput.append(message)
                print("CommsMan     : Sent message: %s" % message)
        print("CommsMan     : Main thread terminating.")

    def sendMessageToSystem(self, message):
        """
        Internal function for sending message to main System.
        :param message: Contents of message to send to system (String)
        """
        try:
            self.sysQueueSend.put(message, timeout=10)
            # print("SCTS         : Message Sent to System: %s" % message)
        except:
            print("SCTS         : Message to System insertion blocked > 10s on: %s" % message)


if __name__ == '__main__':
    # Instantiate Comms object and launch thread
    commsQueue = multiprocessing.Queue(maxsize=1)
    cm = CommsMan(commsQueue)
    x = multiprocessing.Process(target=cm.Launch)
    print("CommsMan     : before running thread")
    x.start()
    print("CommsMan     : after launching thread")
    
    # Simulate message send requests to remote
    cm.SendMessageToRemote("Hello")
    cm.SendMessageToRemote("My name is ike")

    # Simulate message retrieval from "Bluetooth" channel
    cm.SimulateReceiveBT("my name is Tim... the Enchanter!!")

    # Confirm message retrieval
    newMsg = commsQueue.get()
    testOutputBT = cm.SimulateLogBluetooth()
    print("CommsMan     : received message: %s" % newMsg)
    print("CommsMan     : Bluetooth message log:", testOutputBT)

    # Terminate CommsMan & rejoin thread
    if (cm.TerminateCommsMan() == -1):
        print("CommsMan     : Thread terminate has failed/timed-out.")
        raise TimeoutError
    x.join()
    print("CommsMan     : thread rejoined and main ends")



