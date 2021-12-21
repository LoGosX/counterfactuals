from typing import List, Tuple

import numpy as np
from sklearn.preprocessing import OneHotEncoder, StandardScaler
import pandas as pd


def _stack_continuous_nominal(c, n):
    return np.hstack([c, n])


class DataFrameMapper:
    def __init__(self, nominal_columns: List[str]):
        self._nominal_columns = nominal_columns
        self._continuous_columns: List[str] = None
        self._nominal_columns_original_positions: List[int] = None
        self._data_frame_columns = None
        self._one_hot_encoder: OneHotEncoder = None
        self._standard_scaler: StandardScaler = None
        self._original_columns: List[str] = None
        self._n_continuous_columns: int = None

    @property
    def nominal_columns(self):
        return self._nominal_columns

    @property
    def one_hot_spans(self) -> List[Tuple[int, int]]:
        if self._one_hot_encoder is None:
            return None
        spans = []
        one_hot_start = self._n_continuous_columns
        for category in self._one_hot_encoder.categories_:
            n_categories = len(category)
            spans.append((one_hot_start, one_hot_start + n_categories))
            one_hot_start += n_categories
        return spans

    @property
    def _n_one_hot_columns(self):
        if self._one_hot_encoder is None:
            return None
        return sum(len(category) for category in self._one_hot_encoder.categories_)

    def transformed_column_span(self, column: str) -> Tuple[int, int]:
        for col, span in zip(self._nominal_columns, self.one_hot_spans):
            if col == column:
                return span

        # column is continuous and is at the beginning of transformed array
        idx = self._continuous_columns.index(column)
        return idx, idx + 1

    def inverse_transform(self, x: np.ndarray) -> pd.DataFrame:

        if self._one_hot_encoder is None and self._standard_scaler is not None:
            reconstructed_continuous = self._standard_scaler.inverse_transform(x)
            return pd.DataFrame(data=reconstructed_continuous, columns=self._original_columns)
        elif self._standard_scaler is None and self._one_hot_encoder is not None:
            reconstructed_nominal = self._one_hot_encoder.inverse_transform(x)
            return pd.DataFrame(data=reconstructed_nominal, columns=self._original_columns)
        n_one_hot = self._n_one_hot_columns
        one_hot_columns = x[:, -n_one_hot:]
        continuous_columns = x[:, :-n_one_hot]

        reconstructed_continuous = self._standard_scaler.inverse_transform(continuous_columns)
        reconstructed_labels = self._one_hot_encoder.inverse_transform(one_hot_columns)

        reconstructed = reconstructed_continuous.astype(object)
        for i, column in enumerate(sorted(self._nominal_columns_original_positions)):
            reconstructed = np.insert(reconstructed, column, reconstructed_labels[:, i], axis=1)

        return pd.DataFrame(data=reconstructed, columns=self._original_columns)

    def fit(self, x: pd.DataFrame, y=None, **fit_params):
        self._original_columns = list(x.columns)
        self._fit_nominal(x)
        self._fit_continuous(x)
        return self

    def fit_transform(self, x: pd.DataFrame) -> np.ndarray:
        self.fit(x)
        return self.transform(x)

    def transform(self, x: pd.DataFrame, y=None) -> np.ndarray:
        continuous = self._transform_continuous(x)
        nominal = self._transform_nominal(x)
        return _stack_continuous_nominal(continuous, nominal)

    def _fit_continuous(self, x: pd.DataFrame):
        x = x.drop(columns=self._nominal_columns)
        self._continuous_columns = list(x.columns)
        self._n_continuous_columns = x.shape[1]
        if not self._continuous_columns:
            return
        sc = StandardScaler()
        sc.fit(x)
        self._standard_scaler = sc

    def _transform_continuous(self, x: pd.DataFrame):
        x = x.drop(columns=self._nominal_columns)
        if not self._continuous_columns:
            return np.empty((x.shape[0],), dtype="float32")
        x_numpy = self._standard_scaler.transform(x)
        return x_numpy

    def _fit_nominal(self, x: pd.DataFrame):
        if not self._nominal_columns:
            return
        nominal_columns_original_positions = []
        for i, column in enumerate(x.columns):
            if column in self._nominal_columns:
                nominal_columns_original_positions.append(i)

        nominal_columns = x[self._nominal_columns]

        ohe = OneHotEncoder(sparse=False)
        ohe.fit(nominal_columns)
        self._one_hot_encoder = ohe
        self._nominal_columns_original_positions = nominal_columns_original_positions

    def _transform_nominal(self, x: pd.DataFrame):
        ohe = self._one_hot_encoder
        if ohe is None:
            return np.empty((x.shape[0],))
        nominal_columns = x[self._nominal_columns]
        one_hot_encoded = ohe.transform(nominal_columns)

        return one_hot_encoded
