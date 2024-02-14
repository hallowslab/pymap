import os
import json
from pathlib import Path
from django.conf import settings

# Get the base directory of the Django project
BASE_DIR = Path(__file__).resolve().parent.parent


def load_user_settings() -> None:
    # Load custom settings from JSON file
    environment = settings.DJANGO_ENV
    print("ENVIRON", environment)
    config_file = "config.dev.json" if environment == "development" else "config.json"
    custom_settings = {}
    with open(os.path.join(BASE_DIR, config_file)) as f:
        custom_settings = json.load(f)

    log_config = custom_settings.get("LOGGING", {})

    # Override the logging with the user supplied if it exists
    if isinstance(log_config, dict) and len(log_config) > 0:
        settings.LOGGING.update(log_config)

    # Store custom settings under a specific key in PYMAP_SETTINGS
    settings.PYMAP_SETTINGS.update(custom_settings)


def load_user_env() -> None:
    CONFIGS = ["CELERY_BROKER_URL", "CELERY_RESULT_BACKEND"]
    custom_settings = {v: os.getenv(v) for v in CONFIGS if os.getenv(v)}

    if len(custom_settings.keys()) > 0:
        for key, value in custom_settings.items():
            setattr(settings, key, value)
