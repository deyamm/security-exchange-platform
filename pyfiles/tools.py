# -*- coding: utf-8 -*-
import six
import datetime
from pyfiles.exceptions import *
import json
import math
# from pyfiles.utils import *

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
        return date.strftime("%Y"+split+"%m"+split+"%d %H:%M:%S")
    elif isinstance(date, datetime.date):
        return date.strftime("%Y"+split+"%m"+split+"%d")
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
            date = date[:8+2*len(split)]
        return datetime.datetime.strptime(date, '%Y'+split+'%m'+split+'%d').date()
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
def get_quarter(date: datetime) -> int:
    return date.month % 3 + 1

#
def cal_stock_amount(price, cash):
    return math.floor(cash / (price * 100)) * 100