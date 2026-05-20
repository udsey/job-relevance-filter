import logging
import os

from src.utils import load_config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
    ]
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("WDM").setLevel(logging.WARNING)

CONFIG_DIR = os.getcwd()
DATA_DIR = os.path.join(CONFIG_DIR, 'data')
CONFIG_DIR = os.path.join(CONFIG_DIR, 'configs')
os.makedirs(DATA_DIR, exist_ok=True)

config = load_config()
