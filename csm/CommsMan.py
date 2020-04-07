import threading
import queue
import time

class CommsMan():

    def __init__(self, commsQueue, termCommsQueue):
        self.terminateComms = termCommsQueue
        self.sysQueueSend = commsQueue
        self.sysQueueRecv = queue.Queue(maxsize=1)
        self.btQueue = queue.Queue(maxsize=1)
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
            cmTerm.put(-1)
            return 0
        except:
            return -1

    def simulateReceiveBT(self, message):
        try:
            self.btQueue.put(message, timeout=10)
        except:
            print("SRBT     : Bluetooth-Receive queue insertion blocked > 10s on: %s" % message)

    def simulateLogBluetooth(self):
        return str(self.testSendOutput)

    def launch(self):
        print("CommsMan : Main thread launching.")
        while self.terminateComms.empty():
            if not self.btQueue.empty():
                message = self.btQueue.get()
                self.sendMessageToSystem(message)
            elif not self.sysQueueRecv.empty():
                message = self.sysQueueRecv.get()
                self.testSendOutput.append(message)
        print("CommsMan : Main thread terminating.")

    def sendMessageToSystem(self, message):
        """
        Internal function for sending message to main System.
        :param message: Contents of message to send to system (String)
        """
        try:
            self.sysQueueSend.put(message, timeout=10)
            print("SCTS     : Message Sent to System: %s" % message)
        except:
            print("SCTS     : Message to System insertion blocked > 10s on: %s" % message)


if __name__ == '__main__':
    # Instantiate Comms object and launch thread
    commsQueue, cmTerm = queue.Queue(maxsize=1), queue.Queue(maxsize=1)
    cm = CommsMan(commsQueue, cmTerm)
    x = threading.Thread(target=cm.launch)
    print("Main     : before running thread")
    x.start()
    print("Main     : after launching thread")
    
    # Simulate message send requests to remote
    cm.sendMessageToRemote("hello")
    cm.sendMessageToRemote("my name is ike")

    # Simulate message retrieval from "Bluetooth" channel
    cm.simulateReceiveBT("hey Ike I am... Tim... the Enchanter!!")

    # Confirm message retrieval
    newMsg = commsQueue.get()
    testOutputBT = cm.simulateLogBluetooth()
    print("Main     : received message: %s" % newMsg)
    print("Main     : Bluetooth message log:", testOutputBT)

    # Terminate CommsMan & rejoin thread
    if (cm.terminateCommsMan() == -1):
        print("Main     : Thread terminate has failed/timed-out.")
        raise TimeoutError
    x.join()
    print("Main     : thread rejoined and main ends")


    
