from argparse import ArgumentParser
from pathlib import Path 
from src.challenge2.core import build_model 

parser = ArgumentParser(prog='Model builder')
parser.add_argument('-s', 
                    help='Path of the csv file',
                    required=True,
                    type=Path
                    )
parser.add_argument('-d',
                    help='Destination path of the model including filename.',
                    required=True,
                    type=Path
                    )


if __name__ == '__main__':
    args = parser.parse_args()
    try:
        build_model(args.s, model_path=args.d)
    except:
        print('error while building model.')
    else:
        print('model saved.')