from . import challenge2

from dotenv import load_dotenv
from pathlib import Path 
import os 

load_dotenv()

DB_FILE = Path(os.getenv('DB_FILE'))
CSV_FILE = Path(os.getenv('CSV_FILE'))
CURRENT_MODEL_PATH = Path(os.getenv('CURRENT_MODEL_PATH'))
BACKUP_MODELS_PATH = Path(os.getenv('BACKUP_MODELS_PATH'))
ROOT_PATH = Path(__file__).parent.parent