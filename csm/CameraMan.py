# import cv2

class CameraMan():

    def __init__(self, sourcePath):
        # Initialize LocalVideo
        pass

    def Capture(self):
        """
        API function call for pulling the next frame from pre-loaded LocalVideo source.
        :return: Frame data
        """
        pass


if __name__ == '__main__':
    cam = CameraMan("../testData/testVideoTiny.mp4")
    image, count = cam.capture()
    if count != -1:
        cv2.imwrite("frame%d.jpg" % count, image)
    else:
        print("Error: count = -1")
