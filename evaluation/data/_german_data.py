import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from counterfactuals.constraints import Freeze, OneHot, ValueMonotonicity


class GermanData:
    def __init__(self, input_file, labels_file, test_frac=0.2):
        self.input = pd.read_csv(input_file, index_col=0, dtype=np.float64)
        self.labels = pd.read_csv(labels_file, index_col=0, dtype=np.int32)
        self.constraints = [OneHot(7, 10), OneHot(11, 15), OneHot(16, 25), OneHot(26, 30), OneHot(31, 34),
                            OneHot(35, 37), OneHot(38, 41), OneHot(42, 44), OneHot(45, 47), OneHot(48, 51),
                            OneHot(52, 53), OneHot(54, 55), OneHot(56, 60)]
        self.additional_constraints = [Freeze(['credit']), ValueMonotonicity(['age'], "increasing")]
        self.index = 0

        self.X_train, self.X_test, self.y_train, self.y_test = \
            train_test_split(self.input, self.labels, test_size=test_frac)

        self.num_input_columns = len(self.input.columns)
        self.input_columns = self.input.columns
        self.num_label_columns = len(self.labels.columns)
        self.label_columns = self.labels.columns

        self._scaler = StandardScaler()
        self._scaler.fit(self.X_train.to_numpy(dtype=np.float64))
        self.X_train = pd.DataFrame(self._scaler.transform(self.X_train), index=self.X_train.index,
                                    columns=self.X_train.columns)

        if self.X_test.shape[0] > 0:
            self.X_test = pd.DataFrame(self._scaler.transform(self.X_test), index=self.X_test.index,
                                       columns=self.X_test.columns)

    def unscale(self, data):
        if type(data) is pd.DataFrame:
            return pd.DataFrame(self._scaler.inverse_transform(data), index=data.index, columns=data.columns)
        elif type(data) is pd.Series:
            return pd.Series(self._scaler.inverse_transform(pd.DataFrame([data]))[0].transpose(), index=data.index)
        else:
            scaled = self._scaler.inverse_transform([data])[0]
            scaled[scaled < 1**-16] = 0
            return scaled

    def scale(self, data):
        if type(data) is pd.DataFrame:
            return pd.DataFrame(self._scaler.transform(data), index=data.index, columns=data.columns)
        elif type(data) is pd.Series:
            return pd.Series(self._scaler.transform(pd.DataFrame([data]))[0].transpose(), index=data.index)
        else:
            scaled = self._scaler.transform([data])[0]
            scaled[scaled < 1**-16] = 0
            return scaled