from datetime import datetime, timedelta

import pandas as pd
import tushare as ts
import os.path
import json
from dateutil.relativedelta import relativedelta

import SharesPage


def get_list(start_date, end_date):
    #  list_status L:上市
    all_stocks = get_tushare_api().stock_basic(list_status='L', fields='ts_code,name,industry')

    # 收益率列表
    pf_list = []
    cnt = 0
    for index, row in all_stocks.iterrows():
        try:
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

            # code = row['ts_code']
            # df = get_tushare_api().daily( ts_code=row['ts_code'], start_date=start_date, end_date=end_date)
            code = row['ts_code'][:-3]
            df = ts.get_k_data(code, start=start_date, end=end_date[0], ktype="D", autype="qfq")  # 读日K行情数据
            # 上市时间大于4年的不看
            if len(df) > 1000:
                continue

            df.index = df.pop("date")
            if (len(df) < day_ten):
                continue
            if (len(df) < day_fifty or len(df) < day_one_hundred_twenty or len(df) < day_year):
                day_fifty = day_one_hundred_twenty = day_year = len(df)


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
            # 50 日线
            df['fifty'] = df['close'].rolling(day_fifty).mean()
            df["fifty"] = round(df["fifty"], 2)
            # 50日最高
            df['fifty-max'] = df['close'].rolling(day_fifty).max()
            df['fifty-max'] = round(df['fifty-max'], 2)
            # 50 -1日最低
            df['forty-nine-min'] = round(df['close'].rolling(day_fifty).min(), 2)
            # 120日最高价
            df["day_one_hundred_twenty"] = round(df['close'].rolling(day_one_hundred_twenty).max(), 2)
            # 年线 250日
            df["day_year"] = round(df['close'].rolling(day_year).mean(), 2)

            # 是否满足反转条件 日线收盘价站上年线； 一月内曾创50日新高；收盘价站上年线的天数大于3，小于30
            # 50日内振幅小于42% ((最高价-最低价)/最低价) 且 昨天为1个半月内最高价；
            df["buy"] = (df["close"] > df["day_year"]) & \
                        (df["close"].rolling(30).max() >= df['fifty']) & \
                        (df["close"].rolling(3).mean() > df["day_year"]) & \
                        ((df["fifty-max"] - df['forty-nine-min']) / df['forty-nine-min'] <= 0.45) & \
                        (round(df["close"], 2) == df['fifty-max'])

            signals = df[df["buy"]]

            if len(signals):
                rev = True
                date = min(list(signals.index))
                # 反转日到现在的收益率
                rev_profit = round(float((df["close"][-1] / df.at[date, 'close'] - 1.0) * 100), 2)
            else:
                rev = False
                date = ""
                # 反转日到现在的收益率
                rev_profit = 0.0

            pf_list.append(dict(code=code, pf=profit, name=row['name'], industry=row['industry'], revs=rev, date=date,
                                rev_profit=rev_profit))
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
    api = get_tushare_api()
    # 取收益最高的15%，计算收益排名的均值  牛市选择50%
    cmp_percent = 0.50

    end_date_format = end_date[0]
    pf_list = []
    if (os.path.isfile("strategy/" + end_date_format)):
        with open("strategy/" + end_date_format, "r", encoding="utf-8") as dt:
            for line in dt.readlines():
                line = line.strip('\n')
                pf_list.append(eval(line))
            pf_list.sort(key=lambda x: x["pf"], reverse=True)  # 先按时间内的收益率排名（从高往低）
    else:
        pf_list = get_list(start_date, end_date)
        pf_list.sort(key=lambda x: x["pf"], reverse=True)  # 先按时间内的收益率排名（从高往低）
        with open("strategy/" + end_date_format, 'a', encoding='utf-8') as f:
            for item in pf_list:
                f.write("%s\n" % item)
    for idx, doc in enumerate(pf_list):
        doc["rank"] = idx  # 记录下每只个股在时间内的收益率排名

    num_cands = int(len(pf_list) * cmp_percent)  # 用于统计的最高（和最低）收益的股票个数
    top_cands = pf_list[:num_cands]  # 时间内最高收益的股票信息列表

    for t_idx, t_doc in enumerate(top_cands):
        # 是否月线反转
        if t_doc['revs']:
            # 反转日期
            appear_date = t_doc['date'].replace("-", "")
            # 判断日期是否为1个月内
            timeDay = datetime.now() - timedelta(days=30)
            str_date = timeDay.strftime("%Y%m%d")
            # 反转日期小于1个月前日期
            if (datetime.strptime(appear_date, '%Y%m%d') < datetime.strptime(str_date, '%Y%m%d')):
                continue
            name = t_doc['name']
            number = get_hk_number(appear_date, name)
            if (number >= 10000):
                timeDay = datetime.now() - timedelta(days=date)
                if (t_doc['date'] >= timeDay.strftime("%Y-%m-%d")):
                    # 获取当日涨幅
                    day_format = t_doc['date'].replace("-", "")
                    day_detail = api.daily(ts_code=get_code(t_doc['code']), start_date=day_format,
                                           end_date=day_format)
                    print(t_doc['code'], t_doc['name'], t_doc['rank'], t_doc['date'], t_doc['industry'],
                          "当日涨幅: %s " % day_detail['pct_chg'].tolist(), "反转日距今涨幅: %s " % t_doc['rev_profit'])


def get_hk_number(date, name):
    with open("date/" + date, 'r', encoding='utf-8') as d:
        data_str = d.read()
        j = json.loads(data_str)
        df = pd.DataFrame(j, columns=['code', 'name', 'number', 'ratio'])
        curr = (df.loc[df['name'] == name])
        if len(curr) == 0:
            return 0
        return float(str(curr['number'].values[0]).replace(",", ""))


def get_tushare_api():
    ts.set_token('9303ab9ddece253dc96ac6f4662f22a1d0d92579f1d18368f87aaf65')
    return ts.pro_api()


def get_forecast(date, min):
    '''
     获取业绩 如果有业绩则 大于等于min最小增长率为筛选条件
    :param date:    日期
    :param min:     最小增长值
    :return:
    '''
    pro = get_tushare_api()
    forecast = pro.forecast(period=date)
    for index, name in forecast.iterrows():
        if (name['p_change_min'] > min):
            print("code: %s " % name['ts_code'], name['end_date'], name['type'], "最小值: %s " % name['p_change_min'],
                  name['last_parent_net'],
                  name['summary'], name['change_reason'])
        else:
            print(name['ts_code'], name['end_date'], name['type'], name['p_change_min'], name['last_parent_net'],
                  name['summary'])


def get_code(code):
    if code[:2] == '60' or code[:2] == '68':
        return code + '.SH'
    else:
        return code + '.SZ'


if __name__ == "__main__":
    # 获取上个日期开始近5天的反转池
    get_strategy("2019-05-01", SharesPage.get_date(1, False), 50)

    # 获取业绩预告
    # get_forecast('20190331',50)
