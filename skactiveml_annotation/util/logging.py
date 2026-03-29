import logging


def configure_logging():
    logging.basicConfig(
        format='[%(levelname)s] %(message)s',
        datefmt='%H:%M',  # This sets the time format to just hours and minutes
        level=logging.INFO
    )

def configure_logging_background_callback():
    # Clear existing handlers in the background process
    logger = logging.getLogger()
    if logger.hasHandlers():
        logger.handlers.clear()
    configure_logging()


def clear_handlers():
    logger = logging.getLogger()
    logger.handlers.clear()
