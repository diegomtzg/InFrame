
class BoundingBox:
    """
    A bounding box surrounding a potential target object.
    """

    def __init__(self, left_coord, right_coord, top_coord, bottom_coord):
        self.top_left = (left_coord, top_coord)
        self.bottom_right = (right_coord, bottom_coord)
        self.center = ((left_coord + right_coord) / 2, (top_coord + bottom_coord) / 2)


    def vector_to(self, other_bbox):
        """
        Calculates vector from current bbox to a different one.
        :param other_bbox: Second bbox
        :return (x, y): Tuple representing vector from current bbox to another one.
        """
        x = other_bbox.center[0] - self.center[0]
        y = other_bbox.center[1] - self.center[1]

        return (x, y)