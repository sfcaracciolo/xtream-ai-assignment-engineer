from argparse import ArgumentParser
from pathlib import Path 
from src.challenge2.core import Model
import pandas as pd

parser = ArgumentParser(prog='Model builder')
parser.add_argument('-s', metavar='csv path', 
                    help='Absolute or relative path of the csv file with diamonds data.',
                    required=True,
                    dest='CSV_PATH',
                    type=Path
                    )
parser.add_argument('-d', metavar='model path',
                    help='Absolute or relative destination filepath of the model.',
                    required=True,
                    dest='MODEL_PATH',
                    type=Path
                    )

if __name__ == '__main__':
    args = parser.parse_args()
    try:
        data = pd.read_csv(args.CSV_PATH)
        model = Model.build(data)
        model.save(args.MODEL_PATH.parent, filename=args.MODEL_PATH.stem)
    except Exception as exc:
        print(exc)
    else:
        print('model saved.')