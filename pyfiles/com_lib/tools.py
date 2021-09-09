# -*- coding: utf-8 -*-
import six
import datetime
from pyfiles.com_lib.exceptions import *
from pyfiles.com_lib.variables import *
import json
import math
import pandas as pd
from typing import List
# from pyfiles.utils import *


class BasicInfo(object):
    """
    存储证券基础信息，比如股票列表、指数列表、专业术语翻译等内容
    """
    stock_basic: pd.DataFrame = None
    index_basic: pd.DataFrame = None
    fund_basic: pd.DataFrame = None
    trade_cal: pd.DataFrame = None

    def __init__(self, mysql_client, **kwargs):
        self.stock_basic = mysql_client.query("select * from basic_info.stock_basic")
        self.index_basic = mysql_client.query("select * from basic_info.index_basic")
        self.fund_basic = mysql_client.query("select * from basic_info.fund_basic")
        self.trade_cal = mysql_client.query("select * from basic_info.trade_cal")

    def word_translate(self, word, word_type):
        if word_type == 'sec_code':  # 将证券名称转化为证券代码
            word_list = self.stock_basic[self.stock_basic['name'] == word]['ts_code'].tolist()
            if len(word_list) >= 1:
                return word_list[0]
            else:
                return "translate error"
        elif word_type == 'index_code':  # 将指数名称转化为指数代码
            word_list = self.index_basic[self.index_basic['name'] == word]['ts_code'].tolist()
            if len(word_list) >= 1:
                return word_list[0]
            else:
                return "translate error"
        elif word_type == 'noun':  # 将术语转化为该平台通用的英文字符串
            if word == '股池':
                return 'sec_pool'
        else:
            return 'undetermined'


class IndicatorDict(object):
    indicator_list = None
    indicator_dict = {}
    method_dict = {}

    def __init__(self):
        with open(PRO_PATH + '/data/indicator_dict.json') as f:
            self.indicator_list = json.load(f)
        for category in self.indicator_list:
            indicators = self.indicator_list[category]
            if category == 'method_name':
                for method in indicators:
                    self.method_dict[method] = indicators[method]
                    continue
            for indicator in indicators:
                self.indicator_dict[indicator] = {'category': category, 'name': indicators[indicator]}

    def echo_dict(self):
        print(json.dumps(self.indicator_dict, indent=1, ensure_ascii=False))
        print(json.dumps(self.method_dict, indent=1, ensure_ascii=False))

    def get_method_dict(self):
        return self.method_dict

    def classify(self, indicators: List[str]):
        res = {}
        for indicator in indicators:
            if indicator in self.indicator_dict:
                category = self.indicator_dict[indicator]['category']
                if category in res:
                    res[category].append(indicator)
                else:
                    res[category] = [indicator]
            else:
                print('IndicatorDict: ' + indicator + ' 尚未支持')
        return res


def is_str(s):
    """
    检测传入的参数对象是否为字符串
    :param s: 待检测的参数对象
    :return: true/false
    """
    return isinstance(s, six.string_types)


def to_date_str(date, split='-', only_date=False) -> str:
    """
    将表示时间的datetime或date对象转化为指定分隔符的日期字符串，
    当传入的参数为datetime类型对象时，可以选择只返回日期部分
    :param only_date:
    :param date: 所要转换为字符串的对象
    :param split: 日期字符串的分隔符
    :return: 日期字符串
    """
    if isinstance(date, six.string_types):
        return date
    elif isinstance(date, datetime.datetime):
        if only_date is True:
            return date.strftime("%Y" + split + "%m" + split + "%d")
        else:
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


def fq_trans(fq: str):
    """
    将代表行情频率的参数（D/W/M/Y）转换为相应频率行情数据的表名后缀
    :param fq: 代表频率的参数（日D/周W/月M/年Y）
    :return: 相应频率行情数据的表名后缀
    """
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


def get_quarter(date: datetime.date) -> int:
    """
    根据传入的日期，获取该日期所在的季度，该日期的格式具有要求
    :param date: 传入的日期
    :return: 季度
    """
    if isinstance(date, str):
        return 0
    elif isinstance(date, datetime.date):
        return math.ceil(date.month/3)
    else:
        raise ParamError("传入日期参数类型错误")


def cal_stock_amount(price, cash, accuracy=0.000001) -> int:
    """
    根据传入的证券购买价格以及可用金额，计算能够购买的最大股数，
    由于购买时必须以“手”为单位，以及浮点数的计算过程，为了保证结果的正确性，需要特别的计算（1手=100股）
    :param price: 证券的购买价格
    :param cash: 可用金额
    :param accuracy: 在浮点数计算过程中的精确度调整
    :return:
    """
    return math.floor(cash / (price * 100) + accuracy) * 100


def corr_check(corr_matrix: pd.DataFrame, threshold: float) -> List[str]:
    """
    相关性检验，根据传入的dataframe，计算每两个属性之间的相关性，
    并返回相关性高于指定值的属性名
    :param corr_matrix: 待计算的dataframe
    :param threshold: 指定的阈值
    :return: list，列表中各属性之间的相关性高于指定的值
    """
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
    优化方向：1. 当多个日期调整时，需要向数据库查询多次，需要优化为查询一次
            2. 目前查询的是根据市场交易日，需要添加根据个股的交易日来调整日期的功能
    :param is_trade_day:
    :param dt:
    :param days:
    :param direction:
    :return:
    """
    cur_date = datetime.datetime.strptime(dt, "%Y-%m-%d")
    if is_trade_day:
        if direction == 'front':
            reverse = True
            query = "select cal_date, is_open from basic_info.trade_cal where is_open=1 and cal_date >= '%s'" % dt
        elif direction == 'back':
            reverse = False
            query = "select cal_date, is_open from basic_info.trade_cal where is_open=1 and cal_date <= '%s'" % dt
        else:
            raise ParamError("参数错误(front/back)")
        cal_date = MySqlServer().query(query)
        for i in range(len(cal_date)):
            # print(cal_date.loc[0]['cal_date'])
            if isinstance(cal_date.loc[i]['cal_date'], datetime.datetime):
                cal_date.loc[i, 'cal_date'] = cal_date.loc[i, 'cal_date'].strftime("%Y-%m-%d")
        # ###需要对cal_date排序
        cal_date.sort_values(by='cal_date', ascending=reverse, inplace=True)
        # print(cal_date['cal_date'].tolist())
        dts = cal_date['cal_date'].tolist()
        # print(dts)
        return dts[days]
    else:
        if direction == 'front':
            return (cur_date + datetime.timedelta(days=days)).date().isoformat()
        elif direction == 'back':
            return (cur_date - datetime.timedelta(days=days)).date().isoformat()
        else:
            raise ParamError("参数错误(front/back)")


def call_back(value):
    print(value)


def chg_quarter(year: int, quarter: int):
    if quarter == 4:
        return year+1, 1
    else:
        return year, quarter+1


def cal_ma(ma_days: int, current_value: float, previous_ma: float, first_value: float):
    value = (previous_ma * ma_days - first_value + current_value) / ma_days
    return float_precision(value, 2)


def get_fina_end_date(year, quarter, return_type='str'):
    res = None
    if quarter == 1:
        res = datetime.date(year, 3, 31)
    elif quarter == 2:
        res = datetime.date(year, 6, 30)
    elif quarter == 3:
        res = datetime.date(year, 9, 30)
    elif quarter == 4:
        res = datetime.date(year, 12, 31)
    else:
        raise ParamError("季度参数错误，当前参数：%d" % quarter)
    if return_type == 'date':
        return res
    elif return_type == 'str':
        return to_date_str(date=res)


def get_mongo_symbol(symbol):
    mongo_dict = {
        '<': '$lt',
        '<=': '$lte',
        '>': '$gt',
        '>=': '$gte'
    }
    if mongo_dict.get(symbol) is not None:
        return mongo_dict[symbol]
    else:
        raise ParamError("mongo symbol error")


def get_option_query(filters, sql_type: str = 'mysql'):
    """
    该函数用于将字典格式的筛选条件根据目标数据库来转化为其支持的条件语句，
    其中mysql数据库返回的是字符串，mongoDB返回的是字典
    :param filters:
    :param sql_type:
    :return:
    """
    # print(filters, 'outer', sql_type)
    if sql_type == 'mysql':
        query = []
    elif sql_type == 'mongo':
        query = dict()
    else:
        query = None
    if isinstance(filters, str):
        return query
    if isinstance(filters, dict):
        for indicator in filters:
            # print(option, 'loop1')
            options = filters[indicator]
            for option in options:
                if sql_type == 'mysql':
                    query.append('%s%s%s' % (indicator, option, options[option]))
                elif sql_type == 'mongo':
                    if query.get(indicator) is None:
                        query[indicator] = dict()
                    query[indicator][get_mongo_symbol(option)] = float(options[option])
    if sql_type == 'mysql':
        return ' and '.join(query)
    elif sql_type == 'mongo':
        return query
    else:
        return None

