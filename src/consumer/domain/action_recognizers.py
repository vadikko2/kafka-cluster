import numpy as np


def recognizer_action(data, labels, negative_key, time_clf_threshold=0.75):
    data_mean = np.mean(data, axis=1)
    data_max = np.max(data_mean, axis=1)
    data_mean_max = np.argmax(data_mean, axis=1)
    data_mean_max = np.where(
        data_max >= time_clf_threshold,
        data_mean_max,
        negative_key,
    )
    return labels[data_mean_max.tolist()], data_max
