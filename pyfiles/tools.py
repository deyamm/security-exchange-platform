# -*- coding: utf-8 -*-
import six
import datetime
from pyfiles.exceptions import *
# from pyfiles.utils import *

# 检测是否为字符串
def is_str(s):
    return isinstance(s, six.string_types)


# 将表示时间的datetime对象转化为字符串
def to_date_str(date):
    if date is None:
        return None
    if isinstance(date, six.string_types):
        return date
    if isinstance(date, datetime.datetime):
        return date.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(date, datetime.date):
        return date.strftime("%Y-%m-%d")


# 将时间字符串转换为datetime的date对象，即只取日期部分
def to_date(date):
    if is_str(date):
        if ':' in date:
            date = date[:10]
        return datetime.datetime.strptime(date, '%Y-%m-%d').date()
    elif isinstance(date, datetime.datetime):
        return date.date()
    elif isinstance(date, datetime.date):
        return date
    elif date is None:
        return None
    return ParamError("type error")

# 将浮点数精确到指定位数
def float_precision(num: float, precision: int):
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
    name_dict = dict()
    attrs = ['trade_date', 'ts_code', 'open', 'close', 'high', 'low', 'pre_close', 'change',
             'pct_chg', 'vol', 'amount', 'turnover_rate', 'volume_ratio', 'adj_factor',
             'cal_date', 'is_open', 'avg_float_mv', 'dividend_yield_ratio', 'float_mv',
             'pb', 'pe', 'turnover_pct', 'avg_price']
    explains = ['交易日期', '证券代码', '开盘价', '收盘价', '最高价', '最低价', '前一天收盘价', '涨跌额',
                '涨跌幅', '成交量（手/亿股）', '交易额（千元/亿元）', '换手率（%）', '量比', '复权因子',
                '交易日历日期', '是否为交易日', '平均流动市值', '股息率', '流动市值',
                '市净率', '市盈率', '成交额占比（%）', '平均价格']
    for i in range(len(attrs)):
        name_dict[attrs[i]] = explains[i]
    return name_dict[attr_name]