import os
import json
from pathlib import Path
from django.conf import settings

# Get the base directory of the Django project
BASE_DIR = Path(__file__).resolve().parent.parent


def load_user_settings():
    # Load custom settings from JSON file
    custom_settings = {}
    with open(os.path.join(BASE_DIR, "config.json")) as f:
        custom_settings = json.load(f)

    log_config = custom_settings.get("LOGGING", {})

    # Override the logging with the user supplied if it exists
    if isinstance(log_config, dict) and len(log_config) > 0:
        print("Settings overriden from config file")
        settings.LOGGING.update(log_config)

    # Store custom settings under a specific key in PYMAP_SETTINGS
    settings.PYMAP_SETTINGS.update(custom_settings)
