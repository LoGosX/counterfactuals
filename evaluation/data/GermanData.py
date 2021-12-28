import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler


class GermanData:
    def __init__(self, input_file, labels_file, test_frac=0.2):
        self.input = pd.read_csv(input_file, index_col=0)
        self.labels = pd.read_csv(labels_file, index_col=0, dtype=np.int32)
        self.index = 0

        self.X_train, self.X_test, self.y_train, self.y_test = \
            train_test_split(self.input, self.labels, test_size=test_frac)

        self.num_input_columns = len(self.input.columns)
        self.input_columns = self.input.columns
        self.num_label_columns = len(self.labels.columns)
        self.label_columns = self.labels.columns

        self._scaler = StandardScaler()
        self._scaler.fit(self.X_train)
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
            return self._scaler.inverse_transform(data)

    def scale(self, data):
        if type(data) is pd.DataFrame:
            return pd.DataFrame(self._scaler.transform(data), index=data.index, columns=data.columns)
        elif type(data) is pd.Series:
            return pd.Series(self._scaler.transform(pd.DataFrame([data]))[0].transpose(), index=data.index, dtype=np.float64)
        else:
            return self._scaler.transform(data)