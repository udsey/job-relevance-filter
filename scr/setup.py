import os
from pydantic import BaseModel
import yaml
from dotenv import load_dotenv
from scr.models import Config
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    handlers=[
        logging.StreamHandler(),                          
    ]
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("WDM").setLevel(logging.WARNING)


def load_config() -> dict:
    """Load config fime from name."""
    filepath = os.path.join(BASE_DIR, 'config.yaml')
    if not os.path.exists(filepath):
        return Config()
    with open(filepath, "r") as f:
        config = yaml.safe_load(f)
        return Config(**config)
    

def save_config(config: BaseModel):
    """Save config file."""
    with open(os.path.join(BASE_DIR, 'config.yaml'), 'w') as f:
        yaml.dump(config.model_dump(), f, default_flow_style=False)


def load_yaml(filepath: str):
    with open(filepath, "r") as f:
        return yaml.safe_load(f)


def save_to_yaml(model_instance: BaseModel, filepath: str):
    with open(filepath, 'w') as f:
        yaml.dump(model_instance.model_dump(), f, default_flow_style=False, 
                  allow_unicode=True)


BASE_DIR = os.getcwd()
DATA_DIR = os.path.join(BASE_DIR, 'data')
os.makedirs(DATA_DIR, exist_ok=True)

config =  load_config()
