import logging
import os

from pydantic import BaseModel
import yaml
from src.models import Config


def load_config() -> dict:
    """Load config fime from name."""
    filepath = os.path.join(CONFIG_DIR, 'config.yaml')
    if not os.path.exists(filepath):
        return Config()
    with open(filepath, "r") as f:
        config = yaml.safe_load(f)
        return Config(**config)


def save_config(config: BaseModel):
    """Save config file."""
    with open(os.path.join(CONFIG_DIR, 'config.yaml'), 'w') as f:
        yaml.dump(config.model_dump(), f, default_flow_style=False)


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
    ]
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("WDM").setLevel(logging.WARNING)
logging.getLogger("sentence_transformers").setLevel(logging.WARNING)
logging.getLogger("faiss").setLevel(logging.WARNING)
logging.getLogger("huggingface_hub").setLevel(logging.ERROR)

CONFIG_DIR = os.getcwd()
DATA_DIR = os.path.join(CONFIG_DIR, 'data')
CONFIG_DIR = os.path.join(CONFIG_DIR, 'configs')
INDEX_PATH = os.path.join(DATA_DIR, "memory.faiss")
META_PATH = os.path.join(DATA_DIR, "memory.pkl")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(CONFIG_DIR, exist_ok=True)

config = load_config()
