import urllib.request
import re
import urllib.parse
import xlwt
import datetime
import os
import csv
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import getopt
import sys
import platform
import traceback
import zipfile
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email import encoders
from email.header import Header
import threading
import shutil
import math


stock_dict = {"300182": "捷成股份", "600362": "江西铜业"}

head_list = ["日期", "股票代码", "名称", "收盘价", "最高价", "最低价", "开盘价", "前收盘", "涨跌额", "涨跌幅",
                     "换手率", "成交量", "成交金额", "总市值", "流通市值"]

delisted = ["000013", "000015", "000024", "000033", "000047", "000405", "000406", "000412", "000508", "000515"
    , "000522", "000527", "000535", "000542", "000549", "000556", "000562", "000569", "000578", "000583"
    , "000588", "000594", "000602", "000618", "000621", "000653", "000658", "000660", "000675", "000689"
    , "000699", "000730", "000748", "000763", "000765", "000769", "000787", "000805", "000817", "000827"
    , "000832", "000866", "000956", "300186", "600001", "600002", "600003", "600005", "600065", "600087"
    , "600092", "600102", "600181", "600205", "600253", "600263", "600286", "600296", "600472", "600553"
    , "600625", "600627", "600631", "600646", "600656", "600659", "600669", "600670", "600672", "600700"
    , "600709", "600752", "600762", "600772", "600786", "600788", "600799" ,"600813", "600832", "600840"
    , "600852", "600878", "600899", "600991", "601268", "601299", "000991", "002720", "031005", "031007"
    , "038011", "038014", "038015", "038016", "038017", "300361", "300646", "601206", "603680", "002525"
    , "002257", "000002", "600349", "002710"]

# def downback(a,b,c):
#    ''''
#    a:已经下载的数据块
#    b:数据块的大小
#    c:远程文件的大小
#   '''
#    per = 100.0 * a * b / c
#    if per > 100 :
#        per = 100
#    print('%.2f%%' % per)

# 600开头的是上证A股 00开头的是是深证A股 300开头的是创业板 002开头的是深证A股中小企业股票

stock_index_list = [
    "000001", # sh000001 上证指数
    "399001", # sz399001 深证成指
    "000300", # sh000300 沪深300
    "399005", # sz399005 中小板指
    "399006", # sz399006 创业板指
    "000003", # sh000003 B股指数
]

def getChinaStockIndexInfo(stockCode):
    try:
        exchange = "sz" if (int(stockCode) // 100000 == 3) else "sh"
        #http://hq.sinajs.cn/list=s_sh000001
        dataUrl = "http://hq.sinajs.cn/list=s_" + exchange + stockCode
        stdout = urllib.request.urlopen(dataUrl)
        stdoutInfo = stdout.read().decode('gb2312')
        tempData = re.search('''(")(.+)(")''', stdoutInfo).group(2)
        stockInfo = tempData.split(",")
        #stockCode = stockCode,
        info_dict = {"stock_name":stockInfo[0], "stock_end":stockInfo[1], "stock_sz": stockInfo[2],
                     "stock_fd":stockInfo[3], "stock_je":str(int(stockInfo[5]) / 10000)}
        print("{0} {1} 涨跌幅：{2} 成交额：{3}亿".format(stockInfo[0], stockInfo[1],
                                                stockInfo[2],str(int(stockInfo[5]) / 10000)))
        logging.debug("{0} {1} 涨跌幅：{2} 成交额：{3}亿".format(stockInfo[0], stockInfo[1],
                                                stockInfo[2],str(int(stockInfo[5]) / 10000)))
        return info_dict
    except Exception as e:
        print("Exception: " + str(e))
        return None


def get_code_list():
    """
    获取获取所有股票代码，返回股票代码列表
    """
    url = 'http://quote.eastmoney.com/stocklist.html'
    code_list = []
    html = urllib.request.urlopen(url).read()
    html = html.decode('gbk')
    s = r'<li><a target="_blank" href="http://quote.eastmoney.com/\S\S(.*?).html">'
    pat = re.compile(s)
    codes = pat.findall(html)
    print(codes)
    for item in codes:
        if item[0] == '6' or item[0] == '3' or item[0] == '0':
            code_list.append(item)

    valid_list = [item for item in code_list if item not in delisted]
    return valid_list


def get_all_history_data(path, stock_code=None):
    """
    获取股票所有日常交易的数据并保存
    path:数据存放目录
    stock_code: 股票代码
    """
    if path is None:
        dst_dir = 'E:\\guduqiusuo\\Exchange\\股票数据\\'
    else:
        dst_dir = path
    end_date = datetime.datetime.today().strftime('%Y%m%d')
    code_list = []
    if stock_code is None:
        code_list = get_code_list()
    else:
        code_list[0] = stock_code
    for item in code_list:
        print('正在获取%s股票数据...' % item)
        if item[0] == '6':
            url = 'http://quotes.money.163.com/service/chddata.html?code=0' + item + '&end=' + end_date + \
                  '&fields=TCLOSE;HIGH;LOW;TOPEN;LCLOSE;CHG;PCHG;TURNOVER;VOTURNOVER;VATURNOVER;TCAP;MCAP'
        else:
            url = 'http://quotes.money.163.com/service/chddata.html?code=1' + item + '&end=' + end_date + \
                  '&fields=TCLOSE;HIGH;LOW;TOPEN;LCLOSE;CHG;PCHG;TURNOVER;VOTURNOVER;VATURNOVER;TCAP;MCAP'
        try:
            urllib.request.urlretrieve(url, dst_dir + item + '.csv')  # 可以加一个参数dowmback显示下载进度
        except Exception as e:
            print("url retrieve error:{0}".format(e))
            continue


def analyze_stock(sourcepath,  result_dir, startday=None, date_range=30):
    """
    分析Exchange数据：包括分析比得到:
    1、最近涨幅最大的股票列表；
    2、最近跌幅最大的股票列表；
    3、振幅最大的股票列表；
    4、最近连续3天、5天涨或跌的股票
    5、最近连续3天涨并且涨幅超过8%
    6、最近连续5天涨并且涨幅超过12%
    7、最近连续3天跌并且跌幅超过8%
    8、最近连续5天跌并且跌幅超过12%
    9、最近30天、60天股价相对比较低，误差5%以内
    10、获取流通市值最少的50股票
    source: Exchange数据目录
    result_dir: 分析结果保存路径
    startday: 开始日期,例如'2017-02-01
    endday:结束日期,例如'2017-03-28'
    """
    # 中文显示有问题，暂时用英文代替
    # 日期、股票代码、名称、收盘价、最高价、最低价、开盘价、前收盘、涨跌额、涨跌幅、换手率、成交量、成交金额、总市值、流通市值
    namelist = ["date", "code", "name", "TCLOSE", "HIGH", "LOW", "TOPEN", "LCLOSE", "CHG", "PCHG", "TURNOVER",
                "VOTURNOVER", "VATURNOVER", "TCAP", "MACP"]
    folders = os.listdir(sourcepath)
    ana_list = []
    prince_list = []
    negative3_list = []
    negative5_list = []
    positive3_list = []
    positive5_list = []
    close_lowest30_list = []
    close_lowest60_list = []
    close_lowest90_list = []

    low_lowest30_list = []
    low_lowest60_list = []

    suspended_list = []         # 停牌股列表

    up10_3days_list = []        # 3天都红且涨幅超过10%
    up15_5days_list = []        # 3天都红且涨幅超过15%
    down10_3days_list = []      # 3天都绿且跌幅超过10%
    down15_5days_list = []      # 5天都绿且跌幅超过15%

    macp_list = []              # 流通市值
    outsanding_list = []        # 流通股数
    second_new_list = []
    index_info_list = []

    for code in stock_index_list:
        info_dict = getChinaStockIndexInfo(code)
        index_info_list.append({code:info_dict["stock_end"]})
        
    for name in folders:
        fullname = os.path.join(sourcepath, name)
        print("正在分析{0}".format(name))
        try:
            df = pd.read_csv(fullname, encoding='gbk', names=namelist, header=0, error_bad_lines=False)
            df_valid = df.replace(["None", "0.0"], [np.nan, np.nan]).dropna(axis=0, how='any')
            rows = df_valid.shape[0]
            if rows == 0:
                continue

            stock_code = df_valid.iloc[0, 1]
            
            # 排除发行10天的新股
            if rows < 10:
                continue

            if rows > 20:
                dict = {"stockcode": df_valid.iloc[0, 1], "stockname": df_valid.iloc[0, 2],
                        "market_value": df.iloc[0, 14]}
                macp_list.append(dict)

                num = int((int(df.iloc[0, 14])/float(df_valid.iloc[0, 5])))
                dict = {"stockcode": df_valid.iloc[0, 1], "stockname": df_valid.iloc[0, 2], "outstanding":num}
                outsanding_list.append(dict)

            #if df_valid.iloc[0,3] == 0 and df_valid.iloc[0,4] ==0:
            #    continue

            lastday = datetime.datetime.strptime(df_valid.iloc[0, 0], "%Y-%m-%d")
            interval = (datetime.datetime.today() - lastday).days
            # 排除停牌股
            if interval < 5:
                current_low = float(df_valid.iloc[0, 5])
                min30_low = float(df_valid.iloc[0:30, 5].min())
                min60_low = float(df_valid.iloc[0:60, 5].min())

                current = float(df_valid.iloc[0, 3])
                current_count = math.ceil(float(df_valid.iloc[0, 14]) / current)
                issue_price = float(df_valid.iloc[rows - 1, 7])
                issue_count = math.ceil(float(df_valid.iloc[rows - 1, 14]) / float(df_valid.iloc[rows - 1, 3]))
                current_price = current * (current_count/issue_count)
                if df_valid.shape[0] <= 180:
                    dict = {"stockcode": df_valid.iloc[0, 1], "stockname": df_valid.iloc[0, 2],
                            "market_value": df_valid.iloc[0, 14], "outstanding": num,"current_price":current,
                            "current_price2":"{0:3.2f}".format(current_price), "issue_price":issue_price,
                            "price_ratio": "{0:3.2f}".format(current_price/issue_price)}
                    second_new_list.append(dict)

                if (current_low - min30_low)/min30_low <= 0.02:
                    dict = {"stockcode": df.iloc[0, 1], "stockname": df.iloc[0, 2], "lowest": min30_low,
                            "current": current_low, "diff": "{0:3.2f}".format(current_low - min30_low)}
                    low_lowest30_list.append(dict)

                if (current_low - min60_low)/min60_low <= 0.02:
                    dict = {"stockcode": df.iloc[0, 1], "stockname": df.iloc[0, 2], "lowest": min60_low,
                            "current": current_low, "diff": "{0:3.2f}".format(current_low - min60_low)}
                    low_lowest60_list.append(dict)

                current_close = float(df_valid.iloc[0, 3])
                min30_close = float(df_valid.iloc[0:30, 3].min())
                min60_close = float(df_valid.iloc[0:60, 3].min())
                min90_close = float(df_valid.iloc[0:90, 3].min())
                #if -1 != fullname.find("603998"):
                #    print(df_valid, file=r"F:\guduqiusuo\Exchange\分析结果\2017-08-18\603998.txt")
                # (current_close-min30_close)/min30_close
                if current_close-min30_close <= 0.1 :
                    dict = {"stockcode": df.iloc[0, 1], "stockname": df.iloc[0, 2], "lowest": min30_close,
                            "current_close": current_close, "diff":"{0:3.2f}".format(current_close-min30_close)}
                    close_lowest30_list.append(dict)

                if current_close-min60_close <= 0.2:
                    dict = {"stockcode": df.iloc[0, 1], "stockname": df.iloc[0, 2], "lowest": min60_close,
                            "current_close": current_close, "diff":"{0:3.2f}".format(current_close - min60_close)}
                    close_lowest60_list.append(dict)

                if (current_close-min90_close)/min90_close <= 0.02 or current_close-min90_close <= 0.2:
                    dict = {"stockcode": df.iloc[0, 1], "lowest": min90_close, "current_close": current_close,
                            "diff":"{0:3.2f}".format(current_close-min90_close)}
                    close_lowest90_list.append(dict)

                # 排除一些次新股
                if len(df_valid.index) >= 1:
                    dict = {"stockcode": df_valid.iloc[0, 1], "price": df_valid.iloc[0, 7].item()}
                    prince_list.append(dict)

                if rows > 30:
                    if float(df_valid.iloc[0:3, 8].max()) < 0:
                        range = float(df_valid.iloc[0:3, 3].min())/float(df_valid.iloc[0:3, 3].max())
                        dict = {"stockcode": df.iloc[0, 1], "stockname":df.iloc[0, 2],
                                "range":float("{0:4.3f}".format(range))}
                        negative3_list.append(dict)
                        if range < 0.9:
                            down10_3days_list.append(dict)
                            print("3天跌幅超过10%:{0} {1}".format(df_valid.iloc[0, 1], df_valid.iloc[0, 2]))
                            #logging.debug("3天跌幅超过10%:{0}".format(df_valid.iloc[0, 3]))

                    if float(df_valid.iloc[0:5, 8].max()) < 0:
                        range = float(df_valid.iloc[0:3, 3].min()) / float(df_valid.iloc[0:3, 3].max())
                        dict = {"stockcode": df_valid.iloc[0, 1], "stockname":df.iloc[0, 2],
                                "range":float("{0:4.3f}".format(range))}
                        negative5_list.append(dict)
                        if float(df_valid.iloc[0:3, 3].min())/float(df_valid.iloc[0:3, 3].max()) < 0.8:
                            down15_5days_list.append(dict)
                            print("5天跌幅超过15%:{0} {1}".format(df_valid.iloc[0, 1], df_valid.iloc[0, 2]))
                            #logging.debug("5天跌幅超过15%:{0}".format(df_valid.iloc[0, 1]))

                    if float(df_valid.iloc[0:3, 8].min()) > 0:
                        range = float(df_valid.iloc[0:3, 3].max())/float(df_valid.iloc[0:3, 3].min())
                        dict = {"stockcode": df.iloc[0, 1], "stockname":df.iloc[0, 2],
                                "range":float("{0:4.3f}".format(range))}
                        positive3_list.append(dict)
                        if float(df_valid.iloc[0:3, 3].max())/float(df_valid.iloc[0:3, 3].min()) > 1.10:
                            up10_3days_list.append(dict)
                            print("3天涨幅超过10%:{0} {1}".format(df_valid.iloc[0, 1], df_valid.iloc[0, 2]))
                            #logging.debug("3天涨幅超过10%:{0}".format(df_valid.iloc[0, 1]))

                    if float(df_valid.iloc[0:5, 8].min()) > 0:
                        range = float(df_valid.iloc[0:3, 3].max()) / float(df_valid.iloc[0:3, 3].min())
                        dict = {"stockcode": df_valid.iloc[0, 1], "stockname":df.iloc[0, 2],
                                "range":float("{0:4.3f}".format(range))}
                        positive5_list.append(dict)
                        if float(df_valid.iloc[0:3, 3].max())/float(df_valid.iloc[0:3, 3].min()) > 1.20:
                            up15_5days_list.append(dict)
                            print("5天涨幅超过10%:{0} {1}".format(df_valid.iloc[0, 1], df_valid.iloc[0, 2]))
                            #logging.debug("5天涨幅超过15%:{0}".format(df_valid.iloc[0, 1]))

                    df_valid_range = df_valid.head(30).loc[:, ["TOPEN", "TCLOSE", "HIGH", "LOW", "LCLOSE"]]
                    s_low = pd.to_numeric(df_valid_range["LOW"], downcast="float")
                    s_high = pd.to_numeric(df_valid_range["HIGH"], downcast="float")
                    s_open = pd.to_numeric(df_valid_range["TOPEN"], downcast="float")
                    s_lclose = pd.to_numeric(df_valid_range["LCLOSE"], downcast="float")
                    s_tclose = pd.to_numeric(df_valid_range["TCLOSE"], downcast="float")
                    df_valid_range['CHG_LOW'] = (s_low - s_open) / s_open * 100
                    df_valid_range['CHG_HIGH'] = (s_high - s_open) / s_open * 100
                    df_valid_range['CHG_RANGE'] = (s_high - s_low) / s_open * 100
                    #s0 = df_valid_range.iat[range-1, 0]
                    s1 = df_valid_range.iloc[30-1, 0]
                    price_per = float("{0:3.2f}".format((s_tclose.max() - s1)/s1 * 100))
                    chg_range = float("{0:3.2f}".format(df_valid_range['CHG_RANGE'].mean()))
                    ana_list.append((stock_code, price_per, chg_range))
            else:
                logging.debug("判断stockcode{0}为停牌".format(df_valid.iloc[0, 1]))
                suspended_list.append(df_valid.iloc[0, 1])
                continue

        except Exception as e:
            print("fullname:{0}, exception:{1}".format(fullname, e))
            traceback.print_exc()
            continue

    try:
        result_df = pd.DataFrame(ana_list, columns=["名称", "股价变化", "幅度变化"])

        df0 = pd.DataFrame(macp_list).sort_values(by="market_value", ascending=True)[0:50]
        full_path = result_dir + r"\流通市值最低50.csv"
        df0.to_csv(full_path)

        df1 = pd.DataFrame(outsanding_list).sort_values(by="outstanding", ascending=True)[0:50]
        full_path = result_dir + r"\流通量最低50.csv"
        df1.to_csv(full_path)

        df2 = pd.DataFrame(second_new_list).sort_values(by="price_ratio", ascending=True)
        full_path = result_dir + r"\次新股.csv"
        df2.to_csv(full_path)

        df3 = result_df.sort_values(by="幅度变化", ascending=True)[0:50]
        full_path = result_dir + r"\幅度变化表Top50.csv"
        df3.to_csv(full_path)


        df4 = result_df.sort_values(by="股价变化", ascending=True)[0:50]
        full_path = result_dir + r"\股价变化表Top50.csv"
        df4.to_csv(full_path)

        df5 = pd.DataFrame(prince_list).sort_values(by="price", ascending=True)
        df51 = df5[df5["price"] <=5]
        full_path = result_dir + r"\5元以下股票.csv"
        df51.to_csv(full_path)

        df52 = df5[(df5["price"]>5) & (df5["price"]<8)].sort_values(by="price", ascending=True)
        full_path = result_dir + r"\5至8元股票.csv"
        df52.to_csv(full_path)

        if len(down10_3days_list) > 1:
            df6 = pd.DataFrame(down10_3days_list).sort_values(by="range", ascending=True)
            full_path = result_dir + r"\连续3天负增长且跌幅超过10.csv"
            df6.to_csv(full_path)

        if len(down15_5days_list) > 1:
            df7 = pd.DataFrame(down15_5days_list).sort_values(by="range", ascending=True)
            full_path = result_dir + r"\连续5天负增长且跌幅超过15.csv"
            df7.to_csv(full_path)

        if len(up10_3days_list) > 1:
            df8 = pd.DataFrame(up10_3days_list).sort_values(by="range", ascending=True)
            full_path = result_dir + r"\连续3天正增长且涨幅超过10.csv"
            df8.to_csv(full_path)

        if len(up15_5days_list) > 1:
            df9 = pd.DataFrame(up15_5days_list).sort_values(by="range", ascending=True)
            full_path = result_dir + r"\连续5天正增长且涨幅超过10.csv"
            df9.to_csv(full_path)

        df10 = pd.DataFrame(close_lowest30_list).sort_values(by="diff", ascending=True)
        full_path = result_dir + r"\30天收盘最低价分析.csv"
        df10.to_csv(full_path)

        df11 = pd.DataFrame(close_lowest60_list).sort_values(by="diff", ascending=True)
        full_path = result_dir + r"\60天收盘最低价分析.csv"
        df11.to_csv(full_path)

        df12 = pd.DataFrame(close_lowest90_list).sort_values(by="diff", ascending=True)
        full_path = result_dir + r"\90天收盘最低价分析.csv"
        df12.to_csv(full_path)

        df13 = pd.DataFrame(low_lowest30_list).sort_values(by="diff", ascending=True)
        full_path = result_dir + r"\30天最低价分析.csv"
        df13.to_csv(full_path)

        df14 = pd.DataFrame(low_lowest60_list).sort_values(by="diff", ascending=True)
        full_path = result_dir + r"\60天最低价分析.csv"
        df14.to_csv(full_path)

    except Exception as e:
        traceback.print_exc()
        print("exception:{0}".format(e))



# pd.merge(df1, df2, right_index=True, how='outer')
def update_stock(code_list=None, dir_path=None):
    if code_list is None:
        code_list = get_code_list()
    if dir_path is None or dir_path == "":
        def_path = r"E:\guduqiusuo\Exchange\股票数据"
    else:
        def_path = dir_path

    index = 0
    for item in code_list:
        try:
            index = index+1
            start_date = None
            if datetime.datetime.now().hour < 15:
                end_date = (datetime.datetime.today() - datetime.timedelta(days=-1)).strftime('%Y%m%d')
            else:
                end_date = datetime.datetime.today().strftime('%Y%m%d')
            csv_path = dir_path + "\\" + item + ".csv"
            print("正在更新{0}的交易信息".format(item))
            if item[0] == '6':
                url = 'http://quotes.money.163.com/service/chddata.html?code=0' + item + '&end=' + end_date + \
                      '&fields=TCLOSE;HIGH;LOW;TOPEN;LCLOSE;CHG;PCHG;TURNOVER;VOTURNOVER;VATURNOVER;TCAP;MCAP'
            else:
                url = 'http://quotes.money.163.com/service/chddata.html?code=1' + item  + '&end=' + end_date + \
                      '&fields=TCLOSE;HIGH;LOW;TOPEN;LCLOSE;CHG;PCHG;TURNOVER;VOTURNOVER;VATURNOVER;TCAP;MCAP'

            urllib.request.urlretrieve(url, csv_path)
        except Exception as e:
            print("url retrieve error:{0}".format(e))
            continue

def usage():
    print("usage: \r\n"
          "-g get all stock code history data by default, if no stock code specifed \r\n"
          "-u update some stock code data base on history data, if no history data, get all data \r\n"
          "-t get some stock today's exchange detail \r\n"
          "-c stock code \r\n"
          "-d directory to save stock exchange data \r\n"
          "example1: -g -d E:\stockdata \r\n"
          "example2：-t -c 300182 -d E:\stockdata \r\n"
          "example3: -g -c 300182 -d E:\stockdata \r\n")

def make_zip(source_dir, output_filename):
    '''
    打包压缩文件夹中的所有文件为zip文件（未压缩）
    @source_dir:需要压缩的文件夹路径
    @output_filename:输出的zip文件路径
    '''
    zipf = zipfile.ZipFile(output_filename, 'w')
    pre_len = len(os.path.dirname(source_dir))
    for parent, dirnames, filenames in os.walk(source_dir):
        for filename in filenames:
            pathfile = os.path.join(parent, filename)
            arcname = pathfile[pre_len:].strip(os.path.sep)   #相对路径
            zipf.write(pathfile, arcname)

    zipf.close()


def sendmail(subject, text, attachfile, toaddrs, fromaddr, smtpaddr, password):
    '''
    @subject:邮件主题
    @text:邮件内容
    @toaddrs:收信人的邮箱地址['******@139.com', '******@qq.com']
    @fromaddr:发信人的邮箱地址
    @smtpaddr:smtp服务地址，可以在邮箱看，比如163邮箱为smtp.163.com
    @password:发信人的邮箱密码
    '''
    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['From'] = fromaddr
    #msg['To'] = toaddrs[0]
    content = MIMEText(text, 'plain', 'utf-8')
    msg.attach(content)
    basename = os.path.basename(attachfile)
    fp = open(attachfile, 'rb')
    att = MIMEText(fp.read(), 'base64', 'utf-8')
    att["Content-Type"] = 'application/octet-stream'
    att.add_header('Content-Disposition', 'attachment', filename=('gbk', '', basename))
    encoders.encode_base64(att)
    msg.attach(att)
    # -----------------------------------------------------------
    try:
        s = smtplib.SMTP(smtpaddr)
        s.login(fromaddr, password)
        s.sendmail(fromaddr, toaddrs, msg.as_string())
    except Exception as e:
        traceback.print_exc()
        print("exception:{0}".format(e))

    print("邮件发送成功")
    s.close()

def get_info_from_file(file_path):
    content = open(file_path, 'r').read()
    data = content[22:len(content) - 1]
    data1 = data.replace("pages", '"pages"')
    data2 = data1.replace("data", '"data"')
    data_dict = eval(data2)
    data_list = data_dict["data"]
    new_list = []
    for item in data_list:
        item_list = item.split(",")
        item_dict = {"time":item_list[0], "price":item_list[1], "number":item_list[2], "type":item_list[3]}
        new_list.append(item_list)
    return  (data_dict["pages"], new_list)


def get_exchange_detail(ouput_dir):
    stock_dict = {"300182": "捷成股份", "600362": "江西铜业", "002253":"川大智胜", "600288": "大恒科技",
                  "000045": "深纺织A", "000014":"沙河股份"}
    stock_bound = {"300182":500, "600362":200, "002253":100, "600288":250, "000045":200, "000014":150}

    try:
        for item in stock_dict.keys():
            logging.debug("获取股票：{0}今日交易详细信息".format(item))

            exchange_list = []
            dir1 = ouput_dir + "\\" + item
            if not os.path.exists(dir1):
                os.makedirs(dir1)
            path = dir1 + "\\" + datetime.date.today().isoformat() + "_page1"
            if item[0] == '3' or item[0] == '0':
                url = "http://hqdigi2.eastmoney.com/EM_Quote2010NumericApplication/CompatiblePage.aspx?" \
                      "Type=OB&stk={0}2&page=1".format(item)
            elif item[0] == '6':
                url = "http://hqdigi2.eastmoney.com/EM_Quote2010NumericApplication/CompatiblePage.aspx?" \
                      "Type=OB&stk={0}1&page=1".format(item)
            urllib.request.urlretrieve(url, path)
            (pages, data) = get_info_from_file(path)
            os.remove(path)
            exchange_list.extend(data)
            for i in range(2, pages+1):
                url1 = "http://hqdigi2.eastmoney.com/EM_Quote2010NumericApplication/CompatiblePage.aspx?" \
                      "Type=OB&stk={0}2&page={1}".format(item, i)
                path1 = dir1 + "\\" + datetime.date.today().isoformat() + "_page" + str(i)
                urllib.request.urlretrieve(url1, path1)
                (pages1, data1) = get_info_from_file(path1)
                os.remove(path1)
                exchange_list.extend(data1)

            df = pd.DataFrame(exchange_list, columns=["time", "price", "number",  "exchange_type"])
            df['price'] = df['price'].astype('float32')
            df['number'] = df['number'].astype('int32')
            full_path = dir1 + "\\" + datetime.date.today().isoformat() + ".csv"
            df.to_csv(full_path)

            df1 = df[(df.exchange_type== "-1") & (df.number > stock_bound[item])]
            df2 = df[(df.exchange_type == "1") & (df.number > stock_bound[item])]
            buy = df2.number.sum()
            sell = df1.number.sum()
            amount = df['number'].sum()
            print("{0}总交易量：{1} {2}手以上卖单总量：{3} {2}手以上买单总量：{4}".format(stock_dict[item],
                                                                       amount,stock_bound[item], sell, buy))
            logging.debug("{0}总交易量：{1} {2}手以上卖单总量：{3} {2}手以上买单总量：{4}".format(stock_dict[item],
                                                                       amount,stock_bound[item], sell, buy))
    except Exception as e:
        print("exception description:{0}".format(e))


from multiprocessing import cpu_count
import logging

if __name__ == '__main__':
    ver = platform.python_version()
    if -1 != ver.find("3.6"):
        sys._enablelegacywindowsfsencoding()

    starttime = datetime.datetime.now()
    logging.basicConfig(filename="analysis.log",
                        filemode="w+",
                        format="%(asctime)s-%(levelname)s-:%(message)s",
                        datefmt="%Y-%m-%d %H:%M:%S %p",
                        level=logging.DEBUG)

    logging.debug("开始更新并分析")

    outdir = r"E:\guduqiusuo\Exchange\分析结果"
    sourcedir = r"E:\guduqiusuo\Exchange\股票数据"

    if not os.path.exists(outdir):
        os.mkdir(outdir)

    get_exchange_detail(outdir)

    stock_codes = get_code_list()
    print("总共有{0}支有效股票".format(len(stock_codes)))
    logging.debug("总共有{0}支有效股票".format(len(stock_codes)))

    if datetime.datetime.now().hour < 16:
        bupdate = False
    else:
        bupdate = True

    if bupdate:
        if os.path.exists(sourcedir):
            shutil.rmtree(sourcedir)
        os.mkdir(sourcedir)

        print("开始更新")
        logging.debug("开始更新")
        cpus = 1 # cpu_count()
        interval = int(len(stock_codes) / cpus)
        stocks = []
        update_threads = []
        for i in range(0, cpus):
            if i < cpu_count():
                stocks = stock_codes[i*interval:(i+1)*interval]
            else:
                stocks = stock_codes[i*interval:]
            t = threading.Thread(target=update_stock, args=(stocks, sourcedir))
            update_threads.append(t)

        for item in update_threads:
            item.start()

        for item in update_threads:
            item.join()

        print("更新完成")
        logging.debug("更新完成")

    endday = datetime.date.today().isoformat()
    startday = (datetime.date.today() - datetime.timedelta(days=60)).isoformat()
    outdir = r"E:\guduqiusuo\Exchange\分析结果" + "\\" + endday
    if not os.path.exists(outdir):
        os.makedirs(outdir)
    analyze_stock(sourcedir, outdir, startday, 60)

    print("分析完成")
    logging.debug("分析完成")

    bMail = True
    if bMail:
        zip_path = outdir + ".zip"
        make_zip(outdir, zip_path)
        print("压缩完成")
        logging.debug("压缩完成")

        sender = "yxtx1984@sina.com"
        smtp = "smtp.sina.com"
        psw = "yxtx19841201"
        receives = ["yxtx1984@163.com"]
        #receives = ["yxtx1984@163.com", "10664409@163.com", "38567689@qq.com"]
        message = endday + "分析结果"
        sendmail("分析结果", message, zip_path, receives, sender, smtp, psw)
        print("邮件成功发送")
        logging.debug("邮件成功发送")

    endtime = datetime.datetime.now()
    logging.debug("分析完成：{0}，耗时：{1}".format(endtime, (endtime-starttime).seconds))