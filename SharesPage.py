import operator
import re
import json

import urllib3
import pandas as pd
import requests
from datetime import datetime, time
from datetime import timedelta
import matplotlib.pyplot as plt
import os.path
import tushare as ts

import dr_tao_strategy


def getOnePage(url, d):
    urllib3.disable_warnings()
    response = requests.post(url, data=d, verify=False)
    if response.status_code == 200:
        return response.text
    return None


def parseOnePage(html, name):
    return html.loc[(html['name'] == name)]


def get_process_data(webHtml, sh_html, day):
    if (len(webHtml) != 0):
        sz_pattern = re.compile(
            r'<div class="mobile-list-heading">股份代号:</div>.*?<div class="mobile-list-body">(.*?)</div>.*?</td>.*?<div class="mobile-list-heading">股份名称:</div>.*?<div class="mobile-list-body">(.*?)</div>.*?</td>.*?<td class="col-shareholding">.*?<div class="mobile-list-heading">于中央结算系统的持股量:</div>.*? <div class="mobile-list-body">(.*?)</div>.*?</td>.*?<td class="col-shareholding-percent">.*?<div class="mobile-list-heading">占于深交所上市及交易的A股总数的百分比:</div>.*?<div class="mobile-list-body">(.*?)</div>'
            , re.S
        )
        sz_details = re.findall(sz_pattern, webHtml)
    if (len(sh_html) != 0):
        sh_pattern = re.compile(
            r'<div class="mobile-list-heading">股份代号:</div>.*?<div class="mobile-list-body">(.*?)</div>.*?</td>.*?<div class="mobile-list-heading">股份名称:</div>.*?<div class="mobile-list-body">(.*?)</div>.*?</td>.*?<td class="col-shareholding">.*?<div class="mobile-list-heading">于中央结算系统的持股量:</div>.*? <div class="mobile-list-body">(.*?)</div>.*?</td>.*?<td class="col-shareholding-percent">.*?<div class="mobile-list-heading">占于上交所上市及交易的A股总数的百分比:</div>.*?<div class="mobile-list-body">(.*?)</div>'
            , re.S
        )
        sh_details = re.findall(sh_pattern, sh_html)
        sz_details.extend(sh_details)

    # 获取的数据为空
    if (len(sz_details) == 0):
        print("日期[%s] 匹配的数据为空!" % day)
        return sz_details
    # 写入文件
    with open("date/" + day, 'a', encoding='utf-8') as f:
        f.write(json.dumps(sz_details, ensure_ascii=False) + '\n')

    return sz_details;


def write_to_file(name, dataFrame, day):
    with open(name, 'a', encoding='utf-8') as f:
        # 把dataframe 转换为 字典
        model = dataFrame.to_json(orient='records', force_ascii=False)
        dicts = json.loads(model)
        with open(name, "r", encoding="utf-8", errors='replace') as ct:
            context = ct.read()
            # 判断是否已经写入当日数据,已经写过的不再写入
            if (context.find(day) > 0):
                return

        for dict in dicts:
            dict['day'] = day
            f.write(str(dict) + '\n')


def chart(dir, name):
    plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
    plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号
    # x轴
    x = []
    # y轴
    y = []

    with open(dir + name, "r", encoding="utf-8") as sn:
        list_file = []
        # 获取数据 加工后设置到dataframe中
        try:
            for line in sn.readlines():
                line = line.strip('\n')
                # 读取的内容转为字典 目前是str
                list_file.append(eval(line))
            json_arr = json.dumps(list_file, ensure_ascii=False)
            j = json.loads(json_arr)
            df = pd.DataFrame.from_dict(j)
            df.index = df.pop('day')
            df['ratio'] = df['ratio'].map(lambda x: float(x[:-1])).astype('float64')
            df.plot()
            plt.show()

        except Exception as e:
            print("读取文件 %s 出错,错误详情:[%s]" % (sn, e))


def main(days, dir, name, today, all):
    for day in days:
        # 抓取数据的url 深圳
        url = 'https://sc.hkexnews.hk/TuniS/www.hkexnews.hk/sdw/search/mutualmarket_c.aspx?t=sz'
        # 上海
        sh_url = 'https://sc.hkexnews.hk/TuniS/www.hkexnews.hk/sdw/search/mutualmarket_c.aspx?t=sh'
        # 抓取数据的post 请求参数
        d = {'today': today, 'sortBy': 'stockcode', 'sortDirection': 'asc',
             'btnSearch': '搜寻',
             'txtShareholdingDate': day[0:4] + '/' + day[4:6] + '/' + day[6:8],
             '__VIEWSTATEGENERATOR': 'EC4ACD6F',
             '__VIEWSTATE': '/wEPDwUJNjIxMTYzMDAwZGQ79IjpLOM+JXdffc28A8BMMA9+yg==',
             '__EVENTVALIDATION': '/wEdAAdtFULLXu4cXg1Ju23kPkBZVobCVrNyCM2j+bEk3ygqmn1KZjrCXCJtWs9HrcHg6Q64ro36uTSn/Z2SUlkm9HsG7WOv0RDD9teZWjlyl84iRMtpPncyBi1FXkZsaSW6dwqO1N1XNFmfsMXJasjxX85jz8PxJxwgNJLTNVe2Bh/bcg5jDf8='}

        # 判断文件是否存在 网站文件
        if (os.path.isfile("date/" + day)):
            with open("date/" + day, "r", encoding="utf-8") as dt:
                all_str = dt.read()
        else:
            webHtml = getOnePage(url, d)
            sh_html = getOnePage(sh_url, d)
            # 获取到的网页进行数据处理,不然数据太多了
            with open("date/" + day, "a", encoding="utf-8") as dt:
                html_str = get_process_data(webHtml, sh_html, day)
                all_str = html_str
        # 判断获取的数据是否为空
        if (len(all_str) == 0):
            print("获取到的数据为空 当日不再查询[%s]" % day)
            continue

        # 判断文件类型 网页爬取的数据直接就是list 不用转
        if type(all_str).__name__ == 'list':
            j = all_str
        else:
            # 把获取到的string 转为 json 再转 dataframe
            j = json.loads(all_str)

        html = pd.DataFrame(j, columns=['code', 'name', 'number', 'ratio'])
        html.index = html.pop('code')

        if (os.path.isfile(dir)):
            with open(dir, "r", encoding="utf-8") as ct:
                context = ct.read()
                if (context.find(day) > 0):
                    continue

        # 查询文件内容返回字典
        if all:
            items = parseOnePage(html, name)
            # 写入文件
            write_to_file('shares/' + name, items, day)
        else:
            for root, dirs, files in os.walk(dir):
                for subName in files:
                    items = parseOnePage(html, subName)
                    write_to_file('shares/' + subName, items, day)


# 获取日期
def get_date(day, now):
    api = dr_tao_strategy.get_tushare_api()
    if now:
        timeDay = datetime.now().strftime("%Y%m%d")
    else:
        timeDay = (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")

    df = api.query('trade_cal', start_date='20200101', end_date=timeDay, is_open=1)
    date_list = df['cal_date'].sort_values(ascending=False).values.tolist()

    return date_list[:day]


def opendate(n, date12):
    cal_dates = ts.trade_cal()
    stocklist = []
    for i in cal_dates.index:
        str_date = cal_dates.loc[i]['calendarDate']
        isOpen = cal_dates.loc[i]['isOpen']
        if not isOpen:
            continue
        date = datetime.datetime.strptime(str_date, '%Y-%m-%d').date()  # 获取格式为2019-02-22
        date1 = date.strftime("%Y%m%d")  # 处理日期格式为20190222
        stocklist.append(date1)

    start = int(stocklist.index(date12) - n + 1)  # 往前倒推n天
    end = int(stocklist.index(date12) + 1)  # 结束日期
    opendate = stocklist[start:end]
    return opendate


def get_float(param):
    if len(param) == 0:
        return

    return round(float(param.replace(",", "")), 2)


def get_sz_shares_number(days, day_interval, ratio):
    '''
    获取深交所当日与昨日买入的数量差
    :param days: string[] 日期列表
    :param day_interval: string 打印的日期范围
    :param ratio: int   增加的比例大小范围
    :return:
    '''
    print(" ---获取港仔买入数量大于 %d%% 数据" % (ratio * 100))
    allData = pd.DataFrame(columns=('code', 'name', 'number', 'ratio', 'day'))

    gName = None

    days.sort()
    for day in days[-2:]:
        with open("date/" + day, "r", encoding="utf-8") as nf:
            # 获取数据 加工后设置到dataframe中
            data_str = nf.read()
            j = json.loads(data_str)
            df = pd.DataFrame(j, columns=['code', 'name', 'number', 'ratio'])
            df['day'] = day
            allData = allData.append(df)

    allData.index = allData.pop('code')

    for index, name in allData.iterrows():

        subDf = allData.loc[index]
        subDf.index = subDf.pop('day')
        try:
            result_df = subDf.loc[:, ["number", "name", "ratio"]]

            result_df['ratio'] = result_df['ratio'].map(lambda x: float(x[:-1])).astype('float64')

            result_df["diff"] = round((result_df['ratio'] - result_df['ratio'].shift(1)), 2)

            # 今天与昨天差额 是否大于比例
            if ratio > 0:
                result_df["flag"] = result_df["diff"] >= ratio
            else:
                result_df["flag"] = result_df["diff"] <= ratio

            signals = result_df[result_df["flag"]]

            if len(signals) > 0:
                # 今天之前的数据
                timeDay = datetime.now() - timedelta(days=day_interval);
                appointTime = list(signals.index);

                if (max(appointTime) >= timeDay.strftime("%Y%m%d")):
                    if not gName:
                        gName = signals[(signals.index == max(appointTime))]["name"].tolist()
                    elif operator.eq(gName, signals[(signals.index == max(appointTime))]["name"].tolist()):
                        return
                    print(" 入选日期:%s" % max(appointTime), \
                          " 名称:%s" % signals[(signals.index == max(appointTime))]["name"].tolist(), \
                          " 港资持有比例%s" % signals[(signals.index == max(appointTime))]["ratio"].tolist(), \
                          " 上一日持有比例%s" % result_df[result_df.index == days[-2]]["ratio"].tolist(), \
                          " 当日增量%s" % signals[(signals.index == max(appointTime))]["diff"].tolist())

        except Exception as e:
            print("%s 出错,错误详情:[%s]" % (index, e))
            continue


def get_sz_shares_average_incremental(days, day_roll, day_interval, ratio, proportion):
    '''
    获取平均增量
    :param days: 日期列表
    :param day_roll:    统计多少天数据
    :param day_interval:  多少天前的数据
    :param ratio:   平均增量
    :return:
    '''
    allData = pd.DataFrame(columns=('code', 'name', 'number', 'ratio', 'day'))

    gName = None

    for day in days:
        with open("date/" + day, "r", encoding="utf-8") as nf:
            # 获取数据 加工后设置到dataframe中
            data_str = nf.read()
            j = json.loads(data_str)
            df = pd.DataFrame(j, columns=['code', 'name', 'number', 'ratio'])
            df['day'] = day
            allData = allData.append(df)

    allData.index = allData.pop('code')

    for index, name in allData.iterrows():

        subDf = allData.ix[index]
        subDf.index = subDf.pop('day')

        try:
            result_df = subDf.loc[:, ["number", "name", "ratio"]]

            result_df['ratio'] = result_df['ratio'].map(lambda x: float(x[:-1])).astype('float64')

            result_df["diff"] = round((result_df['ratio'] - result_df['ratio'].shift(1)), 3)
            result_df["diff_ave"] = round(result_df['diff'].rolling(day_roll).mean(), 3)

            # 前20日平均增量 港资持股小于1%
            result_df["flag"] = (result_df["diff_ave"] > ratio) & \
                                (result_df['ratio'] < proportion)
            # 近3天平均 增加量
            result_df["three_mean"] = round(result_df['diff'].rolling(3).mean(), 3)

            signals = result_df[result_df["flag"]]

            if len(signals) > 0:
                # 今天之前的数据
                timeDay = datetime.now() - timedelta(days=day_interval);
                appointTime = list(signals.index);
                if (max(appointTime) >= timeDay.strftime("%Y%m%d")):
                    if not gName:
                        gName = signals[(signals.index == max(appointTime))]["name"].tolist()
                    elif operator.eq(gName, signals[(signals.index == max(appointTime))]["name"].tolist()):
                        return

                    print(" 入选日期:%s" % max(appointTime), \
                          " 名称:%s" % signals[(signals.index == max(appointTime))]["name"].tolist(), \
                          " 港资持有比例%s" % signals[(signals.index == max(appointTime))]["ratio"].tolist(), \
                          " 3日平均增量%s" % signals[(signals.index == max(appointTime))]["three_mean"].tolist(), \
                          " 当日增量%s" % signals[(signals.index == max(appointTime))]["diff"].tolist(), \
                          " %s日平均增量 %s" % (day_roll, signals[(signals.index == max(appointTime))]["diff_ave"].tolist()))

        except Exception as e:
            print("%s 出错,错误详情:[%s]" % (index, e))
            continue


def get_pre_incremental(dir, day):
    '''
     获取目录下文件上一日增量
    :param dir: 目录
    :param day: 日期平均增量
    :return:
    '''
    plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
    plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号

    for root, dirs, files in os.walk(dir):
        for subName in files:
            with open(dir + subName, "r", encoding="utf-8") as sn:
                if (subName.find('DS_Store') > 0):
                    continue
                list_file = []
                # 获取数据 加工后设置到dataframe中
                try:
                    for line in sn.readlines():
                        line = line.strip('\n')
                        # 读取的内容转为字典 目前是str
                        list_file.append(eval(line))
                    json_arr = json.dumps(list_file, ensure_ascii=False)
                    j = json.loads(json_arr)
                    df = pd.DataFrame.from_dict(j)
                    df.index = df.pop('day')
                    df['ratio'] = df['ratio'].map(lambda x: float(x[:-1])).astype('float64')
                    df["diff"] = round((df['ratio'] - df['ratio'].shift(1)), 2)
                    # 近5天平均 增加量
                    df["five_mean"] = round(df['diff'].rolling(day).mean(), 3)
                    df.sort_index(ascending=True)
                    # 获取最大索引
                    print("日期: %s " % df[-1:].index.tolist(),
                          "名称: %s " % df[-1:]['name'].tolist(),
                          "港资持有数量: %s " % df[-1:]['number'].tolist(),
                          "港资持有比例: %s " % df[-1:]['ratio'].tolist(),
                          "较前一日增量: %s " % (df[-1:]['diff'].tolist()),
                          "%s日平均增量: %s " % (day, df[-1:]['five_mean'].tolist()))
                except Exception as e:
                    print("读取文件 %s 出错,错误详情:[%s]" % (sn, e))


if __name__ == "__main__":
    days = get_date(20, False)
    name = "亚光科技"
    # 如果重新生成文件则设置为True 并且对时间进行排序,每日增量拉取设置为False
    # days.sort()
    main(days, "shares/", name, datetime.now().strftime("%y%m%d"), False)
    get_pre_incremental("shares/", 5)

    chart("shares/", name)
    get_sz_shares_number(days, 5, 0.3)
