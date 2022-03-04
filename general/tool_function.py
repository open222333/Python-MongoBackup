from datetime import datetime
import os


def get_lastst_date(path):
    '''取的最新日期的資料夾名稱'''
    date_dirs = os.listdir(path)
    format_date = '%Y%m%d'
    stock = {}
    for date in date_dirs:
        try:
            stock[datetime.strptime(date, format_date)] = date
        except:
            pass
    return stock[max(stock.keys())]
