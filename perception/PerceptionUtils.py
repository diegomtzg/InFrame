
class BoundingBox:
    """
    A bounding box surrounding a potential target object defined by two corner points (top left, bottom right).
    """

    def __init__(self, left, top, right, bottom):
        self.top_left = (int(left), int(top))
        self.bottom_right = (int(right), int(bottom))
        self.center = ((left + right) / 2, (top + bottom) / 2)


    def vector_to(self, other_bbox):
        """
        Calculates vector from center of this bbox to center of a different one.
        :param other_bbox: Second bbox
        :return (x, y): Tuple representing vector from current bbox to another one.
        """
        x = other_bbox.center[0] - self.center[0]
        y = other_bbox.center[1] - self.center[1]



        return (x, y)