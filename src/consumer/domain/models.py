import collections
import logging

import numpy as np
from numpy.lib import stride_tricks
from scipy import signal

from consumer.domain import action_recognizers, pose_classifiers

logger = logging.getLogger("models")


class Model:
    def __init__(
        self,
        pose_clf: pose_classifiers.PoseClassifier,
        model_config: dict,
    ) -> None:
        self.pose_clf = pose_clf
        self.labels, self.negative_key = self.pose_clf.get_labels()
        self.negative_key = int(self.negative_key)

        self.labels = {int(k): v for k, v in self.labels.items()}
        self.labels = np.array([self.labels[key] for key in sorted(self.labels.keys())])
        self.negative_label = self.labels[self.negative_key]

        self.write_size = (model_config["write_width"], model_config["write_height"])
        self.bip_threshold = float(model_config["bip_threshold"])
        self.time_clf_threshold = float(model_config["time_clf_threshold"])
        self.frame_conf_count = int(model_config["frame_conf_count"])

    def count_complete_ex(self, obj, labels_history=None, old_rD_x=None, old_rD_y=None):
        from consumer.domain import repeat_detectors

        repeat_detecor = repeat_detectors.RepeatDetector(self.write_size[0], self.write_size[1])

        if old_rD_x and old_rD_y:
            repeat_detecor.set_data(old_rD_x, old_rD_y)

        keypoints_with_scores = np.array(obj["points"])

        if obj["with_clf"]:
            pred = self.pose_clf(keypoints_with_scores, proba=True)
            pred = np.concatenate([pred[[0] * (self.frame_conf_count - 1)], pred])

            frame_conf = stride_tricks.sliding_window_view(pred, (self.frame_conf_count, pred.shape[1]))[:, 0]
            labels_history_temp, confidence = action_recognizers.recognizer_action(
                frame_conf,
                self.labels,
                self.negative_key,
                time_clf_threshold=self.time_clf_threshold,
            )
        else:
            labels_history_temp = np.array([obj["label"]] * len(obj["points"]))

        if labels_history is None:
            labels_history = labels_history_temp
        else:
            labels_history = np.concatenate([np.array(labels_history), labels_history_temp])

        repeat_detecor(keypoints_with_scores)

        # rD_x - body,	rD_y - legs
        rD_x, rD_y = repeat_detecor.get_data()

        logger.info(
            f'user_id: {obj["user_id"]}, rD_x.shape={rD_x.shape}, '
            f"rD_y.shape={rD_y.shape}, labels_history.len={len(labels_history)}",
        )

        peaks_legx_x, _ = signal.find_peaks(-rD_y[:, 0], prominence=(50.0, None))
        peaks_body_x, _ = signal.find_peaks(-rD_x[:, 0], prominence=(50.0, None))
        peaks_body_y, _ = signal.find_peaks(-rD_x[:, 1], prominence=(50.0, None))

        labels_legs_x = labels_history[peaks_legx_x]
        labels_body_x = labels_history[peaks_body_x]
        labels_body_y = labels_history[peaks_body_y]

        result = np.concatenate(
            [
                labels_legs_x[labels_legs_x == "abs"],
                labels_body_x[labels_body_x == "abs"],
                # labels_body_x[labels_body_x == "lunges"],
                labels_body_y[~np.isin(labels_body_y, ["abs", "lunges", self.negative_label])],
            ],
        )

        result = collections.Counter(result.tolist())

        del repeat_detectors

        return dict(result), labels_history.tolist(), rD_x.tolist(), rD_y.tolist()
