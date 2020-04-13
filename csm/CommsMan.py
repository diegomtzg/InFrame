import threading
import queue
import time

class CommsMan():

    def __init__(self, commsQueue, termCommsQueue):
        self.sysQueueSend = commsQueue
        self.sysQueueRecv = queue.Queue(maxsize=1)
        self.btQueue = queue.Queue(maxsize=1)
        self.terminateComms = queue.Queue(maxsize=1)
        self.testSendOutput = []

    def sendMessageToRemote(self, message):
        """
        External function which enables users to message CommsMan to send
        message to the remote interface via Bluetooth for user operation.
        :param message: Contents of message to send to remote (String)
        """
        self.sysQueueRecv.put(message)

    def terminateCommsMan(self):
        """
        External function to terminate CommsMan thread operations.
        """
        try:
            self.terminateComms.put(-1)
            return 0
        except:
            return -1

    def simulateReceiveBT(self, message):
        try:
            self.btQueue.put(message, timeout=10)
        except:
            print("SRBT         : Bluetooth-Receive queue insertion blocked > 10s on: %s" % message)

    def simulateLogBluetooth(self):
        return str(self.testSendOutput)

    def launch(self):
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
    commsQueue = queue.Queue(maxsize=1)
    cm = CommsMan(commsQueue)
    x = threading.Thread(target=cm.launch)
    print("CommsMan     : before running thread")
    x.start()
    print("CommsMan     : after launching thread")
    
    # Simulate message send requests to remote
    cm.sendMessageToRemote("Hello")
    cm.sendMessageToRemote("My name is ike")

    # Simulate message retrieval from "Bluetooth" channel
    cm.simulateReceiveBT("my name is Tim... the Enchanter!!")

    # Confirm message retrieval
    newMsg = commsQueue.get()
    testOutputBT = cm.simulateLogBluetooth()
    print("CommsMan     : received message: %s" % newMsg)
    print("CommsMan     : Bluetooth message log:", testOutputBT)

    # Terminate CommsMan & rejoin thread
    if (cm.terminateCommsMan() == -1):
        print("CommsMan     : Thread terminate has failed/timed-out.")
        raise TimeoutError
    x.join()
    print("CommsMan     : thread rejoined and main ends")



