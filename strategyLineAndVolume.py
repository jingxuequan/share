from datetime import datetime, timedelta

import tushare as ts
import pandas as pd


def get_strategy():
    ts.set_token('9303ab9ddece253dc96ac6f4662f22a1d0d92579f1d18368f87aaf65')

    day_two = 2
    # 5日线
    day_five = 5
    # 10日线
    day_ten = 10
    # 120日线
    day_one_hundred_twenty = 120
    # 50日线
    day_fifty = 50

    all_stocks = ts.get_stock_basics()[["name", "industry", "pe"]]
    strategy_stocks = pd.DataFrame(columns=('code', 'name', 'industry', 'pe', 'date', 'close', 'five', 'ten',
                                            'day_one_hundred_twenty'))
    for code, name in all_stocks.iterrows():
        try:
            # pe
            pe = name['pe']
            # close 收盘价 volume 成交量

            # temp = ts.get_k_data(code, start='2018-03-01', ktype="D", autype="qfq")
            pro = ts.pro_api()
            temp = pro.daily(ts_code=get_code(code), start_date='20180101', end_date=datetime.now().strftime('%Y%m%d'))
            # print(temp)

            # 股票发生长时间停牌 则跳过
            if len(temp) > 130:
                continue

            temp.index = temp.pop("trade_date")
            temp = temp.sort_index(ascending=True)

            df = temp.loc[:, ["close", "vol"]]
            # 2日线
            df["two"] = df['close'].rolling(day_two).mean()
            df["two"] = round(df["two"], 2)
            # 5日线
            df["five"] = df['close'].rolling(day_five).mean()
            df["five"] = round(df["five"], 2)
            # 10日线
            df["ten"] = df['close'].rolling(day_ten).mean()
            df["ten"] = round(df["ten"], 2)
            # 120日线
            df["day_one_hundred_twenty"] = df['close'].rolling(day_one_hundred_twenty).mean()
            df["day_one_hundred_twenty"] = round(df["day_one_hundred_twenty"], 2)
            # 50日线
            df['fifty'] = df['close'].rolling(day_fifty).mean()
            df["fifty"] = round(df["fifty"], 2)

            # 10日平均成交量
            df["ten_volume"] = df['vol'].rolling(day_ten).mean()

            df["buy"] = df["close"] < (df["close"].max() * 0.55)

            # 买入
            '''
            df["buy"] = (((df["two"].shift(2) <= df["five"].shift(2)) & \
                        (df["two"].shift(1) > df["five"].shift(1))) | \
                        ((df["two"].shift(3) <= df["five"].shift(3)) & \
                         (df["two"].shift(1) > df["five"].shift(2))) | \
                        ((df["two"].shift(1) <= df["five"].shift(1)) & \
                         (df["two"] > df["five"])) | \
                        ((df["five"].shift(2) <= df["ten"].shift(2)) & \
                        (df["five"].shift(1) > df["ten"].shift(1))) | \
                        ((df["five"].shift(3) <= df["ten"].shift(3)) & \
                         (df["five"].shift(2) > df["ten"].shift(2))) | \
                        ((df["five"].shift(1) <= df["ten"].shift(1)) & \
                         (df["five"] > df["ten"]))) & \
                        ((df["vol"] > 1.5 * df["ten_volume"]) |
                         (df["vol"].shift(1) > 1.8 * df["ten_volume"])| \
                         (df["vol"].shift(2) > 1.8 * df["ten_volume"])| \
                         (df["vol"].shift(3) > 1.8 * df["ten_volume"])) &\
                        (df["close"] > df["fifty"])
            '''
            signals = df[df["buy"]]
            # 查询总市值
            marketvalue = pro.daily_basic(ts_code=get_code(code), trade_date=datetime.now().strftime('%Y%m%d'))
            mv = marketvalue['total_mv'].values.tolist()
            for i in range(len(mv)):
                df['mv'] = float(round(mv[i] / 10000, 2))

            if len(signals) > 0:
                # 今天之前30天的策略
                timeDay = datetime.now() - timedelta(days=10);
                appointTime = list(signals.index);
                minmv = df[(df.index == max(list(signals.index)))]["mv"].values[0]
                if (max(appointTime) > timeDay.strftime("%Y%m%d")) & (minmv < 30):
                    print(code, name['name'], max(list(signals.index)),
                          df[(df.index == max(list(signals.index)))]["mv"].values[0])
                    # new = pd.DataFrame({"code": code, "name": name['name'], "industry": name['industry'], \
                    #                     "pe": pe, "date": max(list(signals.index)),\
                    #                     "close":df[(df.index==max(list(signals.index)))]["close"].tolist(),\
                    #                     "five":df[(df.index==max(list(signals.index)))]["five"].tolist(), \
                    #                     "ten": df[(df.index == max(list(signals.index)))]["ten"].tolist(), \
                    #                     "day_one_hundred_twenty": \
                    #                     df[(df.index == \
                    #                         max(list(signals.index)))]["day_one_hundred_twenty"].tolist()}, index=[0])
                    # strategy_stocks = strategy_stocks.append(new, ignore_index=True)
                    # df.round(2)
                    # print(code, name['name'], name['industry'],"pe %s "% pe, max(list(signals.index)),\
                    #       "收盘价%s"% df[(df.index==max(list(signals.index)))]["close"].tolist(), \
                    #       "2日%s" % df[(df.index == max(list(signals.index)))]["two"].tolist(), \
                    #       "5日%s"% df[(df.index==max(list(signals.index)))]["five"].tolist(),\
                    #       "10日%s"% df[(df.index==max(list(signals.index)))]["ten"].tolist(),\
                    #       "50日%s"% df[(df.index==max(list(signals.index)))]["fifty"].tolist(),
                    #       "120日%s" % df[(df.index == max(list(signals.index)))]["day_one_hundred_twenty"].tolist())
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
    strategy_stocks.index = strategy_stocks.pop('date')
    print("策略选出标的为 \n%s" % strategy_stocks.sort_values(by=['pe'], ascending=[True]))
