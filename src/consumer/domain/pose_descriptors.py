import typing

import numpy as np

# Default Point config

ANGLES = {
    "Head position": ((5, 0), (0, 6)),
    "Left side(Head and arm)": ((0, 5), (5, 7)),
    "Left hand": ((5, 7), (7, 9)),
    "Left hand and left side": ((7, 5), (5, 11)),
    "Left side and left leg": ((5, 11), (11, 13)),
    "Left leg": ((11, 13), (13, 15)),
    "Right side(Head and arm)": ((0, 6), (6, 8)),
    "Right hand": ((6, 8), (8, 10)),
    "Right hand and right side": ((8, 6), (6, 12)),
    "Right side and right leg": ((6, 12), (12, 14)),
    "Right leg": ((12, 14), (14, 16)),
}

DISTANCES = {
    "Nose and left sholder": (0, 5),
    "Nose and left wrist": (0, 9),
    "Nose and left knee": (0, 13),
    "left wrist and ankle": (9, 15),
    "left elbow and knee": (7, 13),
    "left hip and ankle": (11, 15),
    "left sholder and knee": (5, 13),
    "left sholder and wrist": (5, 9),
    "Nose and right sholder": (0, 6),
    "Nose and right wrist": (0, 10),
    "Nose and right knee": (0, 14),
    "right wrist and ankle": (10, 16),
    "right elbow and knee": (8, 14),
    "right hip and ankle": (12, 16),
    "right sholder and knee": (6, 15),
    "right sholder and wrist": (6, 10),
    "wrists": (9, 10),
    "elbows": (7, 8),
    "knees": (13, 14),
    "ankles": (15, 16),
}

AXIS = {
    "Corpuse": ((5, 6), (11, 12)),
    "Hips": ((11, 12), (13, 14)),
    "Legs": ((13, 14), (15, 16)),
    "Global": ((0, 0), (13, 14)),
}

dist_norm_coef = (6, (13, 15), (14, 16))


# utils static functions
def create_vector(a, b):
    return b - a


def l1(v):
    return np.sqrt(v[:, 0] ** 2 + v[:, 1] ** 2)


def dot(v1, v2):
    return np.sum(v1 * v2, axis=1)


def radian2Degree(angle):
    return angle * (180 / np.pi)


def anlge_v(v1, v2):
    angle = radian2Degree(np.arccos(dot(v1, v2) / (l1(v1) * l1(v2))))
    angle = np.where(np.isnan(angle), -1, (180 - angle) // 1)
    return angle


def angle(a, b, c):
    v1 = create_vector(a, b)
    v2 = create_vector(b, c)
    return anlge_v(v1, v2)


def angle_descr(a, b, c):
    angle_bones = angle(a, b, c)
    return angle_bones


def axis_angle_descr(a, b):
    N = np.mean([a, b], axis=0)
    N = np.array([[N[:, 0], N[:, 1] - 20], [N[:, 0], N[:, 1] + 20]])
    N = np.transpose(N, (2, 0, 1))
    v1, v2 = create_vector(a, b), create_vector(N[:, 0], N[:, 1])

    return N, anlge_v(v1, v2)


def point_dist(a, b, norm=1):
    return np.sqrt(np.sum((a - b) ** 2, axis=0)) / norm


class PoseDescriptor:
    def __init__(self, image_h: int, image_w: int, threshold: float = 0.1):
        self.h, self.w = image_h, image_w
        self.mask = np.array([self.h, 0, 0])
        self.threshold = threshold

        self.use_ANGLES = True
        self.use_AXIS = True
        self.use_DISTANCES = True

        self.ANGLES = ANGLES
        self.AXIS = AXIS
        self.DISTANCES = DISTANCES

        self.dist_norm_coef = dist_norm_coef

        self.ANGLES_features = sorted(self.ANGLES.keys())
        self.AXIS_features = sorted(self.AXIS.keys())
        self.DISTANCES_features = sorted(self.DISTANCES.keys())

    def set_params(self, params: dict) -> None:

        if "use_ANGLES" in params:
            self.use_ANGLES = bool(params["use_ANGLES"])

        if "use_AXIS" in params:
            self.use_AXIS = bool(params["use_AXIS"])

        if "use_DISTANCES" in params:
            self.use_DISTANCES = bool(params["use_DISTANCES"])

        if "point_description" in params:
            if "ANGLES" in params["point_description"]:
                self.ANGLES = params["point_description"]["ANGLES"]

            if "AXIS" in params["point_description"]:
                self.AXIS = params["point_description"]["AXIS"]
            if "DISTANCES" in params["point_description"]:
                self.DISTANCES = params["point_description"]["DISTANCES"]
            if "dist_norm_coef" in params["point_description"]:
                self.dist_norm_coef = params["point_description"]["dist_norm_coef"]

        self.ANGLES_features = sorted(self.ANGLES.keys())
        self.AXIS_features = sorted(self.AXIS.keys())
        self.DISTANCES_features = sorted(self.DISTANCES.keys())

    def get_params(self) -> typing.Dict:
        return {
            "use_ANGLES": self.use_ANGLES,
            "use_AXIS": self.use_AXIS,
            "use_DISTANCES": self.use_DISTANCES,
            "point_description": {
                "ANGLES": self.ANGLES,
                "AXIS": self.AXIS,
                "DISTANCES": self.DISTANCES,
                "dist_norm_coef": self.dist_norm_coef,
            },
        }

    def get_features(self):
        features = []
        if self.use_ANGLES:
            features += ["ANGLES: " + x for x in sorted(self.ANGLES.keys())]
        if self.use_AXIS:
            features += ["AXIS: " + x for x in self.AXIS.keys()]
        if self.use_DISTANCES:
            features += ["DISTANCES: " + x for x in self.DISTANCES.keys()]

        return features

    def __call__(self, frame: np.ndarray) -> np.ndarray:
        frame_data = []
        bip = np.abs(self.mask - np.squeeze(np.multiply(frame, [self.h, self.w, 1])))

        dnc = point_dist(
            np.fliplr(
                np.mean([bip[:, self.dist_norm_coef[1][0]][:-1], bip[:, self.dist_norm_coef[1][1]][:-1]], axis=0),
            ),
            np.fliplr(
                np.mean(
                    [bip[:, self.dist_norm_coef[2][0]][:-1], bip[:, self.dist_norm_coef[2][1]][:-1]],
                    axis=0,
                ),
            ),
        )
        dnc *= self.dist_norm_coef[0]

        if self.use_ANGLES:
            for name in self.ANGLES_features:
                k = self.ANGLES[name]

                a = np.fliplr(bip[:, k[0][0]][:, :-1])
                b = np.fliplr(bip[:, k[0][1]][:, :-1])
                c = np.fliplr(bip[:, k[1][1]][:, :-1])

                angle_bones = angle_descr(a, b, c) / 180

                c1 = bip[:, k[0][0], 2]
                c2 = bip[:, k[0][1], 2]
                c3 = bip[:, k[1][0], 2]
                c4 = bip[:, k[1][1], 2]

                angle_bones = np.where(
                    ((c1 > self.threshold) & (c2 > self.threshold)) & ((c3 > self.threshold) & (c4 > self.threshold)),
                    angle_bones,
                    -1,
                )

                frame_data.append(angle_bones)

        if self.use_AXIS:
            for name in self.AXIS_features:
                k = self.AXIS[name]

                a = np.fliplr(np.mean([bip[:, k[0][0]][:, :-1], bip[:, k[0][1]][:, :-1]], axis=0))
                b = np.fliplr(np.mean([bip[:, k[1][0]][:, :-1], bip[:, k[1][1]][:, :-1]], axis=0))

                _, angle_axis = axis_angle_descr(a, b)
                angle_axis /= 180

                c1 = bip[:, k[0][0], 2]
                c2 = bip[:, k[0][1], 2]
                c3 = bip[:, k[1][0], 2]
                c4 = bip[:, k[1][1], 2]

                angle_axis = np.where(
                    ((c1 > self.threshold) & (c2 > self.threshold)) & ((c3 > self.threshold) & (c4 > self.threshold)),
                    angle_axis,
                    -1,
                )

                frame_data.append(angle_axis)

        if self.use_DISTANCES:
            for name in self.DISTANCES_features:
                k = self.DISTANCES[name]
                dist = point_dist(bip[:, k[0]][:, :-1], bip[:, k[1]][:, :-1], norm=dnc)

                frame_data.append(dist)

        return np.array(frame_data).T
