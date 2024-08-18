import typing

import numpy as np
import orjson


class Descriptor(typing.Protocol):
    def set_params(self, params: dict) -> None:
        pass

    def get_params(self) -> typing.Dict[typing.Text, typing.Any]:
        raise NotImplementedError

    def __call__(self, frame: np.ndarray) -> np.ndarray:
        raise NotImplementedError


class ModelType(typing.Protocol):
    def predict(self, data: np.ndarray) -> np.ndarray:
        raise NotImplementedError

    def predict_proba(self, data: np.ndarray) -> np.ndarray:
        raise NotImplementedError


class PoseClassifier:
    def __init__(
        self,
        model: ModelType,
        descriptor: Descriptor,
        meta: typing.Dict[typing.Literal["classes", "descriptor", "negative"], typing.Any],
    ):
        self.descriptor = descriptor
        self.meta = meta
        self.model = model
        if "descriptor" in meta:
            self.descriptor.set_params(self.meta["descriptor"]["params"])

    def get_labels(self) -> typing.Tuple[typing.Any, typing.Optional[typing.Any]]:
        return self.meta["classes"], self.meta["negative"] if "negative" in self.meta else None

    def __call__(self, keypoints: np.ndarray, proba=False):
        data_for_predict = self.descriptor(keypoints)

        if proba:
            return self.model.predict_proba(data_for_predict)

        return self.model.predict(data_for_predict)

    def __str__(self):
        return str(orjson.dumps(self.meta))
