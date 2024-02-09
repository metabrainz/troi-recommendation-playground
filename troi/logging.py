import logging

#TODO: consider **kwargs


def set_log_level(quiet):

    logger = logging.getLogger("troi")
    ch = logging.StreamHandler()
    if quiet:
        print("set ERROR")
        logger.setLevel(logging.ERROR)
    else:
        print("set INFO")
        logger.setLevel(logging.INFO)

    ch.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(ch)

    print("Logging setup:")
    info("This is INFO")
    error("This is ERROR")
    logger.info("info 2")


def debug(msg=""):
    '''
        Log a message with debug log level. These messages will only be shown when debugging is enabled.
    '''
    logging.getLogger("troi").debug(msg)


def info(msg=""):
    '''
        Log a message with info log level. These messages will only be shown when logging is set to info
    '''
    logging.getLogger("troi").info(msg)


def error(msg=""):
    '''
        Log a message with error log level.
    '''
    logging.getLogger("troi").error(msg)
