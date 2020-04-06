import cv2

class CameraMan(Object):

    def __init__(self, sourcePath):
        updateVideoObject(sourcePath)

    def updateVideoObject(self, sourcePath):
        self.vid = cv2.VideoCapture(sourcePath)
        self.count = 0
        self.success = 1

    def captureFrame(self):
        if (self.success):
            self.success, image = self.vid.read()
            self.count += 1
            return image, self.count-1
        else:
            return None, -1


if __name__ == '__main__':
    cam = CameraMan("../testData/testVideoTiny.mp4")
    image, count = cam.captureFrame()
    if count != -1:
        cv2.imwrite("frame%d.jpg" % count, image)
    else:
        print("Error: count = -1")
