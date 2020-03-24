import jetson.inference  # Python bindings from TensorRT C++ Libraries.
import jetson.utils  # Camera and display helper methods.

from ImageSources import LocalVideo, Camera


class PerceptionMan:
    """
    Perception subsystem management module for object detection and object tracking.
    args:
    - net: Pre-trained network to use for object detection (ssd_mobilenet_v2 by default).
    - conf: Minimum confidence threshold to qualify as a detected object (0.5 by default).
    """

    def __init__(self, network='ssd-mobilenet-v2', threshold=0.5):
        # Load pre-trained object detection network.
        self.net = jetson.inference.detectNet(network, threshold)


    def detect_objects(self, image, width, height):
        # Detect objects in a given image and overlay results on top of it.
        detections = self.net.Detect(image, width, height)
        return detections


    def track_object(self):
        pass


# Test Script
if __name__ == '__main__':
    perception = PerceptionMan()
    source = LocalVideo('/home/diego/Desktop/InFrame/perception/skateboarder_test.mp4')
    display = jetson.utils.glDisplay()

    while display.IsOpen():
        while True:
            img, width, height = source.get_frame()
            perception.detect_objects(img, width, height)
            display.RenderOnce(img, width, height)
            display.SetTitle("ObjectDetection | Network {:.0f} FPS".format(perception.net.GetNetworkFPS()))

    source.close()
