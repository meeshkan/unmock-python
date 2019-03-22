import logging
import logging.config
import os
import yaml
from .utils import makedirs

__all__ = ["setup_logging"]

LOG_CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logging.yaml")
LOGS_DIR = os.path.join(os.path.expanduser("~"), ".unmock", "logs")

def setup_logging(logs_dir, log_config=LOG_CONFIG_FILE):
    """Setup logging configuration
    This MUST be called before creating any loggers.
    """
    if not os.path.isfile(log_config):
        raise RuntimeError("Logging file {log_file} not found".format(log_file=log_config))

    with open(log_config) as log_file:
        config = yaml.safe_load(log_file.read())

    if logs_dir is None:
        logs_dir = LOGS_DIR
    makedirs(logs_dir)

    # Prepend `LOGS_DIR` to all 'filename' attributes listed for handlers in logging.yaml
    for handler_name in config['handlers'].keys():
        handler_config = config['handlers'][handler_name]
        if 'filename' in handler_config:
            handler_config['filename'] = os.path.join(logs_dir, handler_config['filename'])

    logging.config.dictConfig(config)
