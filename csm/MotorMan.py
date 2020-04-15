class MotorMan():

    def __init__(self):
        self.orientationTilt = 0
        self.orientationTurn = 0

    def processOpticalFlowCommand(self, optical_flow):
        """
        Converts optical flow data (vectors) into deltas motor must
        turn to re-center camera view.
        """
        # [INSERT CODE BELOW] CONVERTING OPTICAL FLOW TO MOTOR DELTAS

        deltaTilt, deltaTurn = 0,0
        
        self.orientationTilt += deltaTilt
        self.orientationTurn += deltaTurn



