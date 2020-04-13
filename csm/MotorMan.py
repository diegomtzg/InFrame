class MotorMan():

    def __init__(self):
        self.orientationX = 0
        self.orientationY = 0

    def opticalFlowToMotorDeltas(self, optical_flow):
        """
        Converts optical flow data (vectors) into deltas motor must
        turn to re-center camera view.
        """
        deltaX, deltaY = 0,0

        pass
        
        return deltaX, deltaY

    def adjustOrientation(self, optical_flow):
        """
        External function for taking optical_flow and updating internal
        orientation.
        """
        self.orientationX, self.orientationY = self.opticalFlowToMotorDeltas(optical_flow)
        return self.orientationX, self.orientationY

