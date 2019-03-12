from datetime import datetime, timedelta

import pandas as pd
import tushare as ts
import os.path
import json

'''
均线突破
前2个月在15%上下
放量(5日平均量的一倍)突破2个月内的最大值*0.7 
'''


def get_strategy(start_date, end_date):
    ts.set_token('9303ab9ddece253dc96ac6f4662f22a1d0d92579f1d18368f87aaf65')

    day_two_month = 22

    all_stocks = ts.get_stock_basics()["name"]

    for code, name in all_stocks.iteritems():
        try:
            df = ts.get_k_data(code, start=start_date, end=end_date, ktype="D", autype="qfq")  # 读日K行情数据
            # 上市时间大于4年的不看
            if len(df) > 1000:
                continue

            df.index = df.pop("date")

            # 前2月最小值
            df["min"] = df['close'].rolling(day_two_month).min()
            # 前2月最大值
            df["max"] = df['close'].rolling(day_two_month).max()
            # 前2月波动值
            df["volatility"] = round(df['close'].rolling(day_two_month).mean(), 4)

            # 前2个月在95%上下波动 放量(5日平均量的一倍) 收盘价比开盘价多 8%
            df["buy"] = ((df["min"] / df["volatility"] >= 0.9) & \
                         (df["max"] / df["volatility"] < 1.1)) & \
                        (1.6 * (df["volume"].rolling(6).mean()) < df["volume"]) & \
                        (df["close"] * 0.98 >= df["open"])
            signals = df[df["buy"]]

            if len(signals) > 0:
                # 今天之前X天的策略
                timeDay = datetime.now() - timedelta(days=5);
                appointTime = max(list(signals.index));
                if (appointTime > timeDay.strftime("%Y-%m-%d")):
                    print("代码[%s] 名称[%s]  日期[%s]  开始[%s]  结束[%s]" % (code, name, appointTime,
                                                                     df[df.index == appointTime]["open"].values[0],
                                                                     df[df.index == appointTime]["close"].values[0]))
        except Exception as e:
            print("%s 出错,错误详情:[%s]" % (code, e))
            continue


def get_code(code):
    if code[2:] == '60':
        return code + '.SH'
    else:
        return code + '.SZ'


if __name__ == "__main__":
    strategy_stocks = get_strategy("2019-01-01", datetime.now().strftime('%Y-%m-%d'))
