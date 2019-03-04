# -*- coding: utf-8 -*-
from datetime import datetime, timedelta

import tushare as ts
import pandas as pd


def fourHigh():
    # 获取2018年第2季度的业绩报表数据
    shares = ts.get_stock_basics()
    strategy_stocks = pd.DataFrame(columns=('code', 'name', 'esp', 'bvps', 'reservedPerShare'))

    for code, name in shares.iterrows():
        if name['esp'] < 1:
            # 每股收益小于1
            continue
        if name['bvps'] < 10:
            # 每股净资产小于10
            continue
        if name['reservedPerShare'] < 3:
            # 每股公积金 < 3
            continue

        timeDay = datetime.now() - timedelta(days=1)

        single_share = ts.get_hist_data(code, start=timeDay.strftime('%Y-%m-%d'))

        print(code, name['name'], round(name['esp'], 2), round(name['bvps'], 2), name['reservedPerShare'], \
              name['totals'], name['outstanding'], name['outstanding'] * single_share['close'][:-1].values)
        new = pd.DataFrame({"code": str(code), "name": name['name'], "esp": round(name['esp'], 2), \
                            "bvps": name['bvps'], "reservedPerShare": name['reservedPerShare']}, index=[0])
        strategy_stocks = strategy_stocks.append(new, ignore_index=True)

    # strategy_stocks.drop_duplicates(subset=['code','name'],keep='first',inplace=True)
    # strategy_stocks.to_csv ("四高股.csv" , encoding = "gbk")


if __name__ == '__main__':
    fourHigh()
