import logging
import os
import sys


def get_logger(command_name):
    log_level = os.getenv("MWF_LOG_LEVEL") or logging.INFO
    logger = logging.getLogger(command_name)
    logger.propagate = False
    for h in logger.handlers:
        logger.removeHandler(h)
    logger.addHandler(logging.StreamHandler(sys.stdout))
    logger.setLevel(log_level)
    return logger
