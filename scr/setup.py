import os
from pydantic import BaseModel
import yaml
from dotenv import load_dotenv
from scr.models import LinkedInJobsConfig
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    handlers=[
        logging.StreamHandler(),                          
    ]
)


def load_config_file(filename: str) -> dict:
    """Load config fime from name."""
    with open(os.path.join(BASE_DIR, filename), "r") as f:
        config = yaml.safe_load(f)
    return config


def save_config(config: BaseModel, filename: str):
    """Save config file."""
    with open(os.path.join(BASE_DIR, filename), 'w') as f:
        yaml.dump(config.model_dump(), f, default_flow_style=False)


BASE_DIR = os.getcwd()
DATA_DIR = os.path.join(BASE_DIR, 'data')
os.makedirs(DATA_DIR, exist_ok=True)

config = load_config_file('linkedin_jobs_config.yaml')
if config:
    config = LinkedInJobsConfig(**config)
else:
    config = LinkedInJobsConfig()


save_config(config, "config.yaml")
save_config(config.system_config, "system_config.yaml")