<<<<<<< HEAD
# import cv2

class CameraMan():

    def __init__(self, sourcePath):
        self.updateVideoObject(sourcePath)

    def updateVideoObject(self, sourcePath):
        # self.vid = cv2.VideoCapture(sourcePath)
        self.count = 0
        self.success = 1

    def capture(self):
=======
import cv2

class CameraMan(Object):

    def __init__(self, sourcePath):
        updateVideoObject(sourcePath)

    def updateVideoObject(self, sourcePath):
        self.vid = cv2.VideoCapture(sourcePath)
        self.count = 0
        self.success = 1

    def captureFrame(self):
>>>>>>> 9c21c787759683b791dab1279f9e2f4eb7386c52
        if (self.success):
            self.success, image = self.vid.read()
            self.count += 1
            return image, self.count-1
        else:
            return None, -1


if __name__ == '__main__':
    cam = CameraMan("../testData/testVideoTiny.mp4")
<<<<<<< HEAD
    image, count = cam.capture()
=======
    image, count = cam.captureFrame()
>>>>>>> 9c21c787759683b791dab1279f9e2f4eb7386c52
    if count != -1:
        cv2.imwrite("frame%d.jpg" % count, image)
    else:
        print("Error: count = -1")
