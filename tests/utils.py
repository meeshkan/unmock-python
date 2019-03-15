import logging

LOGGER = None

def get_logger():
    """Returns a logger for test-use (does not write to log files)"""
    global LOGGER
    if LOGGER is None:
        LOGGER = logging.getLogger("tests.unmock")
        LOGGER.setLevel(logging.DEBUG)
        frmtr = logging.Formatter("[%(asctime)s] %(levelname)s\\%(name)s:\t%(message)s")
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(frmtr)
        LOGGER.addHandler(console_handler)
    return LOGGER
