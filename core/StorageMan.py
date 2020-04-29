import queue
import numpy as np
import os
from os.path import isfile, join

import multiprocessing

class StorageMan():

    def __init__(self):
        self.frames = []
        self.recvFrameQ = multiprocessing.Queue(maxsize=1)
        self.compileQ = multiprocessing.Queue(maxsize=1)
        self.width = -1
        self.height = -1

    def AppendFrame(self, frame, frame_width, frame_height):
        self.recvFrameQ.put((frame, frame_width, frame_height))

    def Compile(self, outputPath, fps):
        self.compileQ.put((outputPath, fps))

    def Launch(self):
        """
        Launches the Storage Manager. Loop will repeatedly listen to concurrent
        frame insertions. When a compile command is given, 
        """
        while self.compileQ.empty():
            if not self.recvFrameQ.empty():
                frame, self.width, self.height = self.recvFrameQ.get()
                self.frames.append(frame)
                print("StorageMan   : Frame received and stored.")

        opPath = self.compileInternal()
        print("StorageMan   : Frames compiled and output saved at: %s" % opPath)

    def compileInternal(self):
        outputPath, fps = self.compileQ.get()

        # # [WIP] For bringing together frames and saving video [Saved for later date once MVP reached]
        # output = cv2.VideoWriter(outputPath, cv2.VideoWriter_fourcc(*'DIVX'), fps, (width, height))
        # for frame in range(len(self.frames)):
        #     output.write(frame)
        # output.release()
        
        return outputPath

