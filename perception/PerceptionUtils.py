
class BoundingBox:
    """
    A bounding box surrounding a potential target object defined by two corner points (top left, bottom right).
    """

    def __init__(self, left, top, right, bottom):
        self.topLeft = (int(left), int(top))
        self.bottomRight = (int(right), int(bottom))
        self.center = ((left + right) / 2, (top + bottom) / 2)


    def VectorTo(self, otherBbox):
        """
        Calculates vector from center of this bbox to center of a different one.
        :param otherBbox: Second bbox
        :return (x, y): Tuple representing vector from current bbox to another one.
        """
        x = otherBbox.center[0] - self.center[0]
        y = otherBbox.center[1] - self.center[1]



        return (x, y)
