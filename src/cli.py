import logging
from logging.config import dictConfig
import sys
import os
from core.pymap_core import ScriptGenerator
from core.tools import setup_argparse, set_logging, load_config


if __name__ == "__main__":
    args = setup_argparse()
    config = {}
    if args.config and os.path.isfile(args.config):
        config = load_config(args.config)
    elif os.path.isfile("config.json"):
        config = load_config()
    if "LOGGING" in config:
        dictConfig(config["LOGGING"])
    else:
        set_logging(args.log_level)

    options = {
        k: v for k, v in vars(args).items() if k not in ["host1", "host2", "creds_file"]
    }

    logging.debug(options)

    generator = ScriptGenerator(args.host1, args.host2, args.creds_file, **options)
    try:
        generator.process_input()
    except Exception as e:
        raise e
    sys.exit(0)
