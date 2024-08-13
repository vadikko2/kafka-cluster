import numpy as np

CENTER_POINTS = (0, 5, 6, 11, 12)
LEGS_POINTS = (13, 14)


def get_center(keypoints: np.ndarray, points):
    return np.mean(keypoints[:, points, :-1], axis=1)


class RepeatDetector:
    def __init__(self, image_h: int, image_w: int):
        self.CENTER_POINTS = CENTER_POINTS
        self.LEGS_POINTS = LEGS_POINTS
        self.h, self.w = image_h, image_w
        self.mask = np.array([self.h, 0, 0])
        self.data_center = []
        self.data_legs = []

    def __call__(self, frame):
        bip = np.abs(self.mask - np.squeeze(np.multiply(frame, [self.h, self.w, 1])))
        center = get_center(bip, self.CENTER_POINTS)
        legs = get_center(bip, self.LEGS_POINTS)
        self.data_center += [x[::-1].tolist() for x in center]
        self.data_legs += [x[::-1].tolist() for x in legs]

    def set_params(self, params: dict):

        if "CENTER_POINTS" in params:
            self.CENTER_POINTS = params["CENTER_POINTS"]
        if "LEGS_POINTS" in params:
            self.LEGS_POINTS = params["LEGS_POINTS"]

    def get_params(self):
        return {
            "CENTER_POINTS": self.CENTER_POINTS,
            "LEGS_POINTS": self.LEGS_POINTS,
        }

    def set_data(self, data_center, data_legs):
        self.data_center = data_center[:]
        self.data_legs = data_legs[:]

        if type(self.data_center) is np.ndarray:
            self.data_center = self.data_center.tolist()
        if type(self.data_legs) is np.ndarray:
            self.data_legs = self.data_legs.tolist()

    def get_data(self):
        return np.array(self.data_center), np.array(self.data_legs)

    def clear_data(self):
        self.data_center = []
        self.data_legs = []
