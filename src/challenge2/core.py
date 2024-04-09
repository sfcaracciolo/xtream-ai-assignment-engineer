from pathlib import Path 
import pandas as pd
import numpy as np
from sklearn.preprocessing import OneHotEncoder 
from sklearn.linear_model import LinearRegression 

def load(file_path: Path) -> pd.DataFrame:
    # here, some checks before load file
    return pd.read_csv(file_path)

def curation(input: pd.DataFrame) -> None:
    
    # removing nans
    rec = input[input.isna().any(axis=1)]
    input.drop(index=rec.index, inplace=True)

    # removing nulls
    rec = input[input.isnull().any(axis=1)]
    input.drop(index=rec.index, inplace=True)

    # removing duplicated rows
    rec = input[input.duplicated()]
    input.drop(index=rec.index, inplace=True)

    # removing out of range records
    rec = input.query('(price <= 0) or (x <= 0) or (y <=0) or (z <= 0) or (depth <= 0) or (table <= 0)')
    input.drop(index=rec.index, inplace=True)

def encoding(input: pd.DataFrame) -> pd.DataFrame:

    enc = OneHotEncoder(sparse_output=False)
    cat_data = input.get(['cut', 'clarity', 'color']).to_numpy()
    enc.fit(cat_data) # if new classes appear will be added

    ohe_data = pd.DataFrame(
        data=enc.transform(cat_data),
        columns=np.hstack(enc.categories_),
        index=input.index,
        dtype='bool'
    )

    return ohe_data

def build_model(csv_path: Path, model_path: Path) -> LinearRegression:
    input = load(csv_path)
    curation(input)
    ohe_data = encoding(input)
    X = input.drop(columns=['price', 'cut','color','clarity']).join(ohe_data)
    X -= X.mean() # standarizing samples
    X /= X.std()
    log_y = input.price.map(np.log).to_numpy() # target
    return LinearRegression().fit(X, log_y)

def predict(model: LinearRegression, samples: np.ndarray) -> np.ndarray:
    return np.exp(model.predict(samples))

