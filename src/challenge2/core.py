from pathlib import Path
from typing import Self 
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression 
import pickle 
from string import ascii_uppercase

class Model(LinearRegression):

    cut_cat = np.array(('Fair', 'Good', 'Very Good', 'Premium', 'Ideal'), dtype=object)
    color_cat = np.array(list(reversed(ascii_uppercase[3:10])), dtype=object) # J to D
    clarity_cat = np.array(('I1', 'SI2', 'SI1', 'VS2', 'VS1', 'VVS2', 'VVS1', 'IF'), dtype=object)
    features = ['carat', 'cut', 'color', 'clarity', 'depth', 'table', 'x', 'y', 'z']
    
    def __init__(self, *, fit_intercept: bool = True, copy_X: bool = True, n_jobs = None, positive: bool = False) -> None:
        super().__init__(fit_intercept=fit_intercept, copy_X=copy_X, n_jobs=n_jobs, positive=positive)
        self.scaler = StandardScaler()

    @staticmethod
    def curation_inplace(ds: pd.DataFrame) -> None:
        # removing nans
        rec = ds[ds.isna().any(axis=1)]
        ds.drop(index=rec.index, inplace=True)

        # removing nulls
        rec = ds[ds.isnull().any(axis=1)]
        ds.drop(index=rec.index, inplace=True)

        # removing duplicated rows
        rec = ds[ds.duplicated()]
        ds.drop(index=rec.index, inplace=True)

        # removing out of range records
        rec = ds.query('(price <= 0) or (x <= 0) or (y <=0) or (z <= 0) or (depth <= 0) or (table <= 0)')
        ds.drop(index=rec.index, inplace=True)

        # removing invalid classes
        rec = ds[~ds.cut.isin(Model.cut_cat)]
        ds.drop(index=rec.index, inplace=True)

        rec = ds[~ds.color.isin(Model.color_cat)]
        ds.drop(index=rec.index, inplace=True)

        rec = ds[~ds.clarity.isin(Model.clarity_cat)]
        ds.drop(index=rec.index, inplace=True)

    @staticmethod
    def featuring_inplace(ds: pd.DataFrame) -> None: 
        width = .5*(ds.x+ds.y) # estimation of width.
        ds.loc[:,'depth'] = 100 * ds.z / width

    @staticmethod
    def encoding_inplace(ds: pd.DataFrame):
        """ds header: cut, color and clarity"""
        ds.loc[:,'cut'] = ds.cut.map({k:i+1 for i,k in enumerate(Model.cut_cat)})
        ds.loc[:,'color'] = ds.color.map({k:i+1 for i,k in enumerate(Model.color_cat)})
        ds.loc[:,'clarity'] = ds.clarity.map({k:i+1 for i,k in enumerate(Model.clarity_cat)})

    @staticmethod
    def extract_features(ds: pd.DataFrame) -> pd.DataFrame:
        return ds.get(Model.features)
    
    @staticmethod
    def extract_target(ds: pd.DataFrame) -> pd.Series:
        return ds.get(['price'])
    
    def fit(self, X: pd.DataFrame, y: pd.Series) -> LinearRegression:
        self.featuring_inplace(X)
        self.encoding_inplace(X)
        scaled_X = self.scaler.fit_transform(X)
        scaled_y = np.log(y)
        return super().fit(scaled_X, scaled_y)
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        self.featuring_inplace(X)
        self.encoding_inplace(X)
        scaled_X = self.scaler.transform(X)
        y = super().predict(scaled_X)
        return np.exp(y)
    
    def save(self, path: Path, filename: str = 'model'):
        path.mkdir(parents=True, exist_ok=True)
        pickle.dump(self, open(path / f'{filename}.pickle', 'wb'))

    @staticmethod
    def load(path: Path) -> LinearRegression:
        if path.is_dir():
            path = path / 'model.pickle'
        return pickle.load(open(path, 'rb'))
    
    @classmethod
    def build(cls, ds: pd.DataFrame) -> Self:
        model = cls()
        model.curation_inplace(ds)
        X = model.extract_features(ds)
        y = model.extract_target(ds)
        model.fit(X, y)
        return model



