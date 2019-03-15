import logging
import logging.config
from pathlib import Path

import yaml

__all__ = ["setup_logging"]

LOG_CONFIG_FILE = Path(__file__).absolute().parent.joinpath("logging.yaml")

def setup_logging(logs_dir: Path, log_config: Path = LOG_CONFIG_FILE):
    """Setup logging configuration
    This MUST be called before creating any loggers.
    """
    if not log_config.is_file():
        raise RuntimeError("Logging file {log_file} not found".format(log_file=log_config))

    with log_config.open() as log_file:
        config = yaml.safe_load(log_file.read())

    # Prepend `LOGS_DIR` to all 'filename' attributes listed for handlers in logging.yaml
    for handler_name in config['handlers'].keys():
        handler_config = config['handlers'][handler_name]
        if 'filename' in handler_config:
            filename = Path(handler_config['filename']).name
            handler_config['filename'] = str(logs_dir.joinpath(filename))

    logging.config.dictConfig(config)
