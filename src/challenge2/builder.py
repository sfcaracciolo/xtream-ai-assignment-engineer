from argparse import ArgumentParser
from pathlib import Path 
from src.challenge2.core import build_model, load_csv

parser = ArgumentParser(prog='Model builder')
parser.add_argument('-s', metavar='csv path', 
                    help='Absolute or relative path of the csv file with diamonds data.',
                    required=True,
                    dest='CSV_PATH',
                    type=Path
                    )
parser.add_argument('-d', metavar='model path',
                    help='Absolute or relative destination path of the model without extension.',
                    required=True,
                    dest='MODEL_PATH',
                    type=Path
                    )

if __name__ == '__main__':
    args = parser.parse_args()
    try:
        data = load_csv(args.CSV_PATH)
        _ = build_model(data, model_path=args.MODEL_PATH.with_suffix('.pickle'))
    except Exception as exc:
        print(exc)
    else:
        print('model saved.')