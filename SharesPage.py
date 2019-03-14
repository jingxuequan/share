import operator
import re
import json

import pandas as pd
import requests
from datetime import datetime, time
from datetime import timedelta
import matplotlib.pyplot as plt
import os.path


def getOnePage(url, d):
    response = requests.post(url, data=d)
    if response.status_code == 200:
        return response.text
    return None


'''
    获取当天拉取的某条数据
'''


def parseOnePage(html, name):
    return html.loc[(html['name'] == name)]


def get_process_data(webHtml, day):
    pattern = re.compile(
        r'<div class="mobile-list-heading">股份代号:</div>.*?<div class="mobile-list-body">(.*?)</div>.*?</td>.*?<div class="mobile-list-heading">股份名称:</div>.*?<div class="mobile-list-body">(.*?)</div>.*?</td>.*?<td class="col-shareholding">.*?<div class="mobile-list-heading">于中央结算系统的持股量:</div>.*? <div class="mobile-list-body">(.*?)</div>.*?</td>.*?<td class="col-shareholding-percent">.*?<div class="mobile-list-heading">占于深交所上市及交易的A股总数的百分比:</div>.*?<div class="mobile-list-body">(.*?)</div>'
        , re.S
    )
    details = re.findall(pattern, webHtml)

    # 获取的数据为空
    if (len(details) == 0):
        print("日期[%s] 匹配的数据为空!" % day)
        return details
    # 写入文件
    with open("date/" + day, 'a', encoding='utf-8') as f:
        f.write(json.dumps(details, ensure_ascii=False) + '\n')

    return details;


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


def chart(days, dir, name, today):
    plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
    plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号
    # x轴
    x = []
    # y轴
    y = []

    if (os.path.isfile(dir + name + ".txt")):
        with open(dir + name + ".txt", "r", encoding="utf-8") as nf:
            for line in nf.readlines():
                line_detail = json.loads(line.strip())
                # 判断当天有没有数据,如果有,则不更新
                for day in days:
                    if (line_detail['date'] == day):
                        x.append(day[4:8])
                        y.append(int(line_detail['number'].replace(',', '')))
                        continue
    num = len(x)
    plt.figure(figsize=(0.5 * num, 4.8))
    plt.plot(x, y)
    plt.plot(x, y, color='red')
    plt.title('share chart')
    plt.xlabel("date")
    plt.ylabel("number")
    plt.show()


def main(days, dir, name, today, all):
    for day in days:
        # 抓取数据的url
        url = 'http://sc.hkexnews.hk/TuniS/www.hkexnews.hk/sdw/search/mutualmarket_c.aspx?t=sz'
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
                html_str = dt.read()
        else:
            webHtml = getOnePage(url, d)
            # 获取到的网页进行数据处理,不然数据太多了
            with open("date/" + day, "a", encoding="utf-8") as dt:
                html_str = get_process_data(webHtml, day)

        # 判断获取的数据是否为空
        if (len(html_str) == 0):
            print("获取到的数据为空 当日不再查询[%s]" % day)

        # 判断文件类型 网页爬取的数据直接就是list 不用转
        if type(html_str).__name__ == 'list':
            j = html_str
        else:
            # 把获取到的string 转为 json 再转 dataframe
            j = json.loads(html_str)

        html = pd.DataFrame(j, columns=['code', 'name', 'number', 'ratio'])
        html.index = html.pop('code')

        if (os.path.isfile(dir)):
            with open(dir, "r", encoding="utf-8") as ct:
                context = ct.read()
                if (context.find(day) > 0):
                    continue

        # 查询文件内容返回字典
        if all:
            for root, dirs, files in os.walk(dir):
                for subName in files:
                    items = parseOnePage(html, subName)
                    write_to_file('shares/' + subName, items, day)
        else:
            items = parseOnePage(html, name)
            # 写入文件
            write_to_file('shares/' + name, items, day)


# 获取日期
def get_date(day):
    days = []
    while day > 0:
        timeDay = datetime.now() - timedelta(days=day);

        # 去除周末信息 0-6是星期一到星期日
        dayOfWeek = timeDay.weekday()
        if (5 != dayOfWeek and 6 != dayOfWeek):
            otherStyleTime = timeDay.strftime("%Y%m%d")
            days.append(otherStyleTime)
        day = day - 1
    return days


def get_float(param):
    if len(param) == 0:
        return

    return round(float(param.replace(",", "")), 2)


'''
获取深交所当日与昨日买入的数量差
Parameters
    ------
      days:string[]
                  日期列表
      day_interval:string
                  打印的日期范围
      ratio:int
                  增加的比例大小范围
'''


def get_sz_shares_number(days, day_interval, ratio):
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

            result_df["diff"] = round((result_df['ratio'] - result_df['ratio'].shift(1)), 2)

            # 今天与昨天差额 是否大于比例
            result_df["flag"] = result_df["diff"] >= ratio

            # 近5天平均 增加量
            result_df["five_mean"] = round(result_df['diff'].rolling(5).mean(), 2)

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
                          " 5日平均增量%s" % signals[(signals.index == max(appointTime))]["five_mean"].tolist(), \
                          " 当日增量%s" % signals[(signals.index == max(appointTime))]["diff"].tolist())

        except Exception as e:
            print("%s 出错,错误详情:[%s]" % (index, e))
            continue

    # return allData;


if __name__ == "__main__":
    days = get_date(30)
    main(days, "shares/", "以岭药业", datetime.now().strftime("%y%m%d"), True)
    # chart(days,"shares/",'鱼跃医疗 联化科技 华测检测',datetime.now().strftime("%Y%m%d"))
    get_sz_shares_number(days, 2, 0.3)
