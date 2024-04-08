import logging


def set_log_level(quiet):
    logger = logging.getLogger("troi")
    level = logging.ERROR if quiet else logging.INFO
    logger.setLevel(level)
