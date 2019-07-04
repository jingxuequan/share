from datetime import datetime, timedelta

import numpy
import pandas as pd
import tushare as ts
import os.path
import json


def get_list(start_date, end_date):
    day_two = 2
    # 5日
    day_five = 5
    # 10日
    day_ten = 10
    # 50日
    day_fifty = 50
    # 120日
    day_one_hundred_twenty = 120
    # 250日
    day_year = 250

    all_stocks = ts.get_stock_basics()["name"]

    # 收益率列表
    pf_list = []
    cnt = 0
    for code, name in all_stocks.iteritems():
        try:
            # df = api.daily_basic( ts_code=get_code(code), adj='qfq', start_date=start_date, end_date=end_date)
            df = ts.get_k_data(code, start=start_date, end=end_date, ktype="D", autype="qfq")  # 读日K行情数据
            # 上市时间大于4年的不看
            if len(df) > 1000:
                continue

            df.index = df.pop("date")

            # 最近50日的收益率
            profit = int((df["close"][-1] / df["close"][-day_fifty] - 1.0) * 100)

            # 2日线
            df["two"] = df['close'].rolling(day_two).mean()
            df["two"] = round(df["two"], 2)
            # 5日线
            df["five"] = df['close'].rolling(day_five).mean()
            df["five"] = round(df["five"], 2)
            # 10日线
            df["ten"] = df['close'].rolling(day_ten).mean()
            df["ten"] = round(df["ten"], 2)
            # 50日最高
            df['fifty'] = round(df['close'].rolling(day_fifty).max(), 2)
            # 120日线
            df["day_one_hundred_twenty"] = round(df['close'].rolling(day_one_hundred_twenty).mean(), 2)
            # 年线 250日
            df["day_year"] = round(df['close'].rolling(day_year).mean(), 2)

            # 是否满足反转条件 日线收盘价站上年线； 一月内曾创50日新高；收盘价站上年线的天数大于3，小于30 最高价距离120日内的最高价不到10 %；
            df["buy"] = (df["close"] > df["day_year"]) & \
                        (df["close"].rolling(30).max() >= df['fifty']) & \
                        (df["close"].rolling(30).min() < df["day_year"]) & \
                        (df["close"].rolling(2).mean() > df["day_year"]) & \
                        (df["close"].rolling(30).max() / df["day_one_hundred_twenty"].max() >= 0.9)
            signals = df[df["buy"]]

            if len(signals):
                rev = True
                date = min(list(signals.index))
            else:
                rev = False
                date = ""

            pf_list.append(dict(code=code, pf=profit, name=name, revs=rev, date=date))
            cnt += 1
        except Exception as e:
            print("%s 出错,错误详情:[%s]" % (code, e))
            continue
    return pf_list


def get_strategy(start_date, end_date, date):
    """
    陶博士月线翻转策略
    月线反转3.0版本的技术指标公式的几个条件是：
    (1)日线收盘价站上年线；
    (2)一月内曾创50日新高；
    (3)50日的RPS大于85；
    (4)收盘价站上年线的天数大于3，小于30；
    (5)最高价距离120日内的最高价不到10%；
    """
    ts.set_token('9303ab9ddece253dc96ac6f4662f22a1d0d92579f1d18368f87aaf65')
    api = ts.pro_api()
    # 取收益最高的15%，计算收益排名的均值
    cmp_percent = 0.15

    end_date_format = (end_date.replace("-", ""))
    pf_list = []
    if (os.path.isfile("strategy/" + end_date_format)):
        with open("strategy/" + end_date_format, "r", encoding="utf-8") as dt:
            for line in dt.readlines():
                line = line.strip('\n')
                pf_list.append(eval(line))
    else:
        pf_list = get_list(start_date, end_date)
        with open("strategy/" + end_date_format, 'a', encoding='utf-8') as f:
            for item in pf_list:
                f.write("%s\n" % item)
    pf_list.sort(key=lambda x: x["pf"], reverse=True)  # 先按时间内的收益率排名（从高往低）
    for idx, doc in enumerate(pf_list):
        doc["rank"] = idx  # 记录下每只个股在时间内的收益率排名

    num_cands = int(len(pf_list) * cmp_percent)  # 用于统计的最高（和最低）收益的股票个数
    top_cands = pf_list[:num_cands]  # 时间内最高收益的股票信息列表

    for t_idx, t_doc in enumerate(top_cands):
        # 是否月线反转
        if t_doc['revs']:
            # 判断是否为港资持仓
            appear_date = (t_doc['date']).replace("-", "")
            name = t_doc['name']
            with open("date/" + appear_date, 'r', encoding='utf-8') as d:
                data_str = d.read()
                j = json.loads(data_str)
                df = pd.DataFrame(j, columns=['code', 'name', 'number', 'ratio'])
                curr = (df.loc[df['name'] == name])
                if len(curr) == 0:
                    continue
                number = float(str(curr['number'].values[0]).replace(",", ""))
                if (number >= 300000):
                    timeDay = datetime.now() - timedelta(days=date)
                    if (t_doc['date'] >= timeDay.strftime("%Y-%m-%d")):
                        print(t_doc['name'], t_doc['rank'], t_doc['date'])
            # df = pro.daily_basic(ts_code=get_code(t_doc["code"]), trade_date=(t_doc['date']).replace("-", ""),
            #                      fields='ts_code,trade_date,turnover_rate,volume_ratio,pe,pb')
            # print(df)


def get_forecast():
    # 获取业绩 如果有业绩则 大于等于30最小增长率为筛选条件
    ts.set_token('9303ab9ddece253dc96ac6f4662f22a1d0d92579f1d18368f87aaf65')
    pro = ts.pro_api()
    forecast = pro.forecast(period='20190331')
    for index, name in forecast.iterrows():
        if (name['p_change_min'] > 50):
            print("code: %s " % name['ts_code'], name['end_date'], name['type'], "最小值: %s " % name['p_change_min'],
                  name['last_parent_net'],
                  name['summary'], name['change_reason'])
        else:
            print(name['ts_code'], name['end_date'], name['type'], name['p_change_min'], name['last_parent_net'],
                  name['summary'])

def get_code(code):
    if code[2:] == '60':
        return code + '.SH'
    else:
        return code + '.SZ'


if __name__ == "__main__":
    # strategy_stocks = get_strategy("2018-01-01", datetime.now().strftime('%Y-%m-%d'),5)
    strategy_stocks = get_strategy("2018-01-01", '2019-05-24', 10)

    # 获取业绩预告
    # get_forecast()
