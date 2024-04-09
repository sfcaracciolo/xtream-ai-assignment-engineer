from pathlib import Path 
import pandas as pd
from string import ascii_uppercase

# all sorted from low to high price.
CUT_CATEGORIES = ('Fair', 'Good', 'Very Good', 'Premium', 'Ideal')
CLARITY_CATEGORIES = ('I1', 'SI2', 'SI1', 'VS2', 'VS1', 'VVS2', 'VVS1', 'IF')
COLOR_CATEGORIES = list(reversed(ascii_uppercase[3:10]))

def load(file_path: Path) -> pd.DataFrame:
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

    rec = input[~input.cut.isin(CUT_CATEGORIES)]
    input.drop(index=rec.index, inplace=True)

    input[~input.color.isin(COLOR_CATEGORIES)]
    input.drop(index=rec.index, inplace=True)
    
    input[~input.clarity.isin(CLARITY_CATEGORIES)]
    input.drop(index=rec.index, inplace=True)

def encoding(input: pd.DataFrame) -> None:

    input.cut = input.cut.map({k:v+1 for v, k in enumerate(CUT_CATEGORIES)})
    input.color = input.color.map({k:v+1 for v, k in enumerate(COLOR_CATEGORIES)})
    input.clarity = input.clarity.map({k:v+1 for v, k in enumerate(CLARITY_CATEGORIES)})

