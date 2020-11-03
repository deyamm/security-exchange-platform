# -*- coding: utf-8 -*-
import six
import datetime
from pyfiles.exceptions import *
import json
import math
import pandas as pd
import numpy as np
import MySQLdb as sql
from typing import List


# from pyfiles.utils import *

class MySQL(object):

    def __init__(self):
        host = 'localhost'
        port = 3306
        user = 'root'
        passwd = 'qq16281091'
        db = 'stock'
        charset = 'utf8'
        self.connect = sql.connect(host=host, port=port, user=user, passwd=passwd, db=db, charset=charset)
        self.cursor = self.connect.cursor()

    def query(self, query: str):
        self.cursor.execute(query)
        data = np.array(self.cursor.fetchall())
        df = pd.DataFrame(data, columns=[col[0] for col in self.cursor.description])
        return df

    def get_cursor(self):
        return self.cursor

    def __del__(self):
        self.cursor.close()
        self.connect.close()

# 检测是否为字符串
def is_str(s):
    return isinstance(s, six.string_types)


def to_date_str(date, split='-') -> str:
    """
    将表示时间的datetime对象转化为字符串
    :param date: 所要转换为字符串的对象
    :param split: 日期字符串的分隔符
    :return: 日期字符串
    """
    if isinstance(date, six.string_types):
        return date
    elif isinstance(date, datetime.datetime):
        return date.strftime("%Y" + split + "%m" + split + "%d %H:%M:%S")
    elif isinstance(date, datetime.date):
        return date.strftime("%Y" + split + "%m" + split + "%d")
    else:
        raise ParamError("datetime error")


def to_date(date, split='-'):
    """
    将时间字符串转换为datetime的date对象，即只取日期部分
    :param date: 所要转换的日期字符串
    :param split: 该日期字符串中所用的分隔符，适用于只使用一种分隔符的字符串
    :return: date对象
    """
    if is_str(date):
        if ':' in date:
            date = date[:8 + 2 * len(split)]
        return datetime.datetime.strptime(date, '%Y' + split + '%m' + split + '%d').date()
    elif isinstance(date, datetime.datetime):
        return date.date()
    elif isinstance(date, datetime.date):
        return date
    elif date is None:
        return None
    else:
        raise ParamError("type error")


def float_precision(num: float, precision: int) -> float:
    """
    将浮点数精确到指定位数
    :param num: 精确的浮点数
    :param precision: 指定的小数位数
    :return:
    """
    return float(format(num, '.%df' % precision))


# 将数据频率转换为表名后缀
def fq_trans(fq: str):
    t_fq = fq.upper()
    if t_fq == 'D':
        return 'daily'
    elif t_fq == 'W':
        return 'weekly'
    elif t_fq == 'M':
        return 'monthly'
    elif t_fq == 'Y':
        return 'yearly'
    else:
        raise ParamError("数据频率错误（D/W/M/Y）")


# 属性名解释
def attr_explain(attr_name: str):
    with open('../../data/attr_info.json') as f:
        name_dict = json.load(f)
    print(name_dict)
    return name_dict[attr_name]


# 根据日期获取对应季度
def get_quarter(date: datetime.date) -> int:
    return math.ceil(date.month/3)


#
def cal_stock_amount(price, cash) -> int:
    return math.floor(cash / (price * 100)) * 100


def corr_check(corr_matrix: pd.DataFrame, threshold: float) -> List[str]:
    columns = corr_matrix.columns.tolist()
    redundance_indicator = []
    for i in range(len(columns)):
        for j in range(i + 1, len(columns)):
            # sprint(corr_matrix.loc[columns[i], columns[j]])
            if abs(corr_matrix.loc[columns[i], columns[j]]) >= threshold and columns[j] not in redundance_indicator:
                redundance_indicator.append(columns[j])
    # print(redundance_indicator)
    return redundance_indicator


def chg_dt_format(dt: str, cur_split: str = '', tar_split: str = '-') -> str:
    """
    改变日期字符串的格式
    :param dt:
    :param cur_split:
    :param tar_split:
    :return:
    """
    dt = dt[:4] + tar_split + dt[4 + len(cur_split): 6 + len(cur_split)] \
        + tar_split + dt[6 + len(cur_split) * 2:]
    return dt


def chg_dt(dt: str, days: int, direction: str, is_trade_day=False) -> str:
    """
    将指定日期字符串向前或向后移动一定天数，可以指定移动的是否是交易日，并返回结果日期的字符串
    :param is_trade_day:
    :param dt:
    :param days:
    :param direction:
    :return:
    """
    cur_date = datetime.datetime.strptime(date_string=dt, format="%Y-%m-%d")
    if is_trade_day:
        cal_date = MySQL().query("select cal_date, is_open from basic_info.cal_date where is_open=1")
        for i in range(len(cal_date)):
            if isinstance(cal_date[i]['cal_date'], datetime.datetime):
                cal_date[i]['cal_date'] = cal_date[i]['cal_date'].strftime("%Y-%m-%d")
        if direction == 'front':
            dts = cal_date.loc[dt:].index.tolist().sort()
        elif direction == 'back':
            dts = cal_date.loc[:dt].index.tolist().sort(reverse=True)
        else:
            raise ParamError("参数错误(front/back)")
        return dts[days-1]
    else:
        if direction == 'front':
            return (cur_date + datetime.timedelta(days=days)).isoformat()
        elif direction == 'back':
            return (cur_date - datetime.timedelta(days=days)).isoformat()
        else:
            raise ParamError("参数错误(front/back)")