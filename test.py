import tushare as ts
from datetime import datetime
import pandas as pd


def get_daily_data(pro):
    df = pro.moneyflow_hsgt(start_date='20181030', end_date=datetime.now().strftime('%Y%m%d'))
    # df = pro.daily(ts_code=get_code('300748'), start_date='20181030', end_date=datetime.now().strftime('%Y%m%d'))
    print(df)


def get_hsgt(pro):
    df = pro.moneyflow_hsgt(start_date='20181102', end_date=datetime.now().strftime('%Y%m%d'))
    print(df)


def get_code(code):
    if code[2:] == '60':
        return code + '.SH'
    else:
        return code + '.SZ'


if __name__ == '__main__':
    pf_list = []
    for i in range(1, 10):
        pf_list.append(dict(code=i, pf="pf" + str(i), reverse=True))
    print(pf_list)

    for i, val in enumerate(pf_list):
        if val["reverse"]:
            print("循环的值为: code: %s , pf: %s , reverse: %s" % (val["code"], val["pf"], val["reverse"]))
