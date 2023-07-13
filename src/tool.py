from datetime import datetime
from .logger import Log
from . import LOG_LEVEL
import os


logger = Log()
if LOG_LEVEL:
    logger.set_level(LOG_LEVEL)

logger.set_date_handler()
logger.set_msg_handler()


