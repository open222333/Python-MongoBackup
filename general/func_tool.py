from datetime import datetime
from .func_logger import Log
from . import LOG_LEVEL
import os


logger = Log(__name__)
logger.set_date_handler()
logger.set_msg_handler()
if LOG_LEVEL:
    logger.set_level(LOG_LEVEL)


def get_lastst_date(path):
    '''取的最新日期的資料夾名稱'''
    date_dirs = os.listdir(path)
    format_date = '%Y%m%d'
    stock = {}
    for date in date_dirs:
        try:
            stock[datetime.strptime(date, format_date)] = date
        except Exception as err:
            logger.error(err, exc_info=True)
    return stock[max(stock.keys())]
