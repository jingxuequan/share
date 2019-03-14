from datetime import datetime, timedelta

import tushare as ts
import pandas as pd

'''
    底部放量策略
'''
def get_strategy():
    # 10日
    ten = 10
    # 最大价格日
    day_price = 60
    # 120日
    one_hundred_twenty = 120

    all_stocks = ts.get_stock_basics()[["name", "industry", "pe"]]
    strategy_stocks = pd.DataFrame(columns=('code', 'name', 'industry', 'pe', 'date', 'close', 'five', 'ten',
                                            'day_one_hundred_twenty'))
    for code, name in all_stocks.iterrows():
        try:
            # pe
            pe = name['pe']
            # close 收盘价 volume 成交量
            temp = ts.get_hist_data(code=code, start='2018-01-01', end=datetime.now().strftime('%Y-%m-%d'))
            # print(temp)

            # 股票发生长时间停牌 则跳过
            if len(temp) <= 120:
                continue

            temp = temp.sort_index(ascending=True)

            df = temp.loc[:, ["close", "volume"]]
            # 最小价格
            df["min_price"] = df['close'].rolling(day_price).min()
            df["min_price"] = round(df["min_price"], 2)

            # 平均价格
            df["average_close"] = df['close'].rolling(day_price).mean()
            df["average_close"] = round(df["average_close"], 2)

            # 最大价格
            df["max_price"] = df['close'].rolling(day_price).max()
            df["max_price"] = round(df["max_price"], 2)

            # 10日平均成交量
            df["ten_volume"] = df['volume'].rolling(ten).mean()

            # 120日最大金额
            df["ten_volume"] = df['volume'].rolling(ten).mean()

            # 当日成交量
            df["buy"] = (df["max_price"] / df["min_price"] <= 1.20) & \
                        (df["max_price"] / 1.15 <= df["average_close"]) & \
                        (df["min_price"] * 1.15 >= df["average_close"]) & \
                        (df["close"] >= df["close"].shift(1) * 1.05) & \
                        (df['volume'] >= (df["ten_volume"] * 1.5))

            # 当日收盘价格收距120日最高价百分比
            df["mv"] = df['close'] / df['close'].rolling(ten).max()

            signals = df[df["buy"]]

            if len(signals) > 0:

                # 今天之前30天的策略
                timeDay = datetime.now() - timedelta(days=3);
                appointTime = list(signals.index);
                if max(appointTime) > timeDay.strftime("%Y-%m-%d"):
                    print(code, name['name'], max(list(signals.index)))
        except Exception as e:
            print("%s 出错,错误详情:[%s]" % (code, e))
            continue
    return strategy_stocks;


def get_code(code):
    if code[2:] == '60':
        return code + '.SH'
    else:
        return code + '.SZ'


if __name__ == "__main__":
    strategy_stocks = get_strategy()
