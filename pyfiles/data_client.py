# -*- coding: utf-8 -*-
import MySQLdb as sql
from sqlalchemy import create_engine
import numpy as np
import datetime
import pandas as pd
import warnings
from typing import List
# from pyfiles.utils import *
from pyfiles.tools import *


class DataClient(object):
    connect = None
    cursor = None
    trade_cal = None

    def __init__(self, **kwargs):
        host = kwargs.get("host", 'localhost')
        port = kwargs.get("port", 3306)
        user = kwargs.get("user", 'root')
        passwd = kwargs.get("passwd", 'qq16281091')
        db = kwargs.get("db", 'stock')
        charset = kwargs.get("charset", 'utf8')
        # 建立连接
        self.connect = sql.connect(host=host, port=port, user=user, passwd=passwd, db=db, charset=charset)
        self.cursor = self.connect.cursor()

        # 将整个交易日历存储下来
        query = "select * from trade_cal.trade_cal"
        self.cursor.execute(query)
        self.trade_cal = pd.DataFrame(np.array(self.cursor.fetchall()),
                                      columns=[col[0] for col in self.cursor.description])
        # 将datetime类型设置为索引，输出整个对象时只显示日期，实际仍是datetime类型
        self.trade_cal.set_index('cal_date', inplace=True)
        # print(self.trade_cal)

    # 获取指定证券指定日期的前一交易日
    def get_pre_trade_day(self, sec_code: str, date: str):
        query = "select trade_date from %s_daily where trade_date < '%s'" % (sec_code[:6], date)
        self.cursor.execute(query)
        dates = np.array(self.cursor.fetchall()).ravel()
        # 应先转化为str
        if to_date_str(dates[-1].date()) == date:
            return to_date_str(dates[-2].date())
        return to_date_str(dates[-1].date())

    # 获取指定证券指定日期的后一交易日
    def get_back_trade_day(self, sec_code: str, date: str):
        query = "select trade_date from %s_daily where trade_date > '%s'" % (sec_code[:6], date)
        self.cursor.execute(query)
        dates = np.array(self.cursor.fetchall()).ravel()
        # 应先转化为str
        if to_date_str(dates[0].date()) == date:
            return to_date_str(dates[1].date())
        return to_date_str(dates[0].date())

    def get_ma(self, days: int, date: str, sec_code: str, fq: str):
        """
        计算均线
        :param days: 均值的天数
        :param date: 日期
        :param sec_code: 证券代码
        :param fq: 均值频率，'D'表示日均线，’W'表示周均线，‘M'表示月均线，’Y‘表示年均线
        :return: 目标均值
        """
        table_name = sec_code[:6] + '_' + fq_trans(fq)
        #
        query = "select %s from stock.%s where trade_date='%s'" \
                % ('ma' + str(days), table_name, date)
        # print(query)
        try:
            self.cursor.execute(query)
        except Exception as e:
            raise ParamError("未找到%s表，或不存在指定属性" % table_name)
        #
        res = np.array(self.cursor.fetchall())
        if len(res > 0) and len(res[0] > 0):
            return res[0][0]
        else:
            return self.get_ma(days=days, date=self.get_pre_trade_day(sec_code=sec_code, date=date),
                               sec_code=sec_code, fq=fq)  # 返回上一个交易日的数据

    def get_price(self, date: str, sec_code: str, price_type: str):
        query = "select %s from stock.%s where trade_date='%s'" \
                % (price_type, sec_code[:6] + '_daily', date)
        try:
            self.cursor.execute(query)
        except Exception as e:
            raise ParamError("未找到%s表，或价格类型（open/close/high/low）错误")
        res = np.array(self.cursor.fetchall())
        # print(res[0][0])
        if len(res) > 0 and len(res[0]) > 0:
            return res[0][0]
        else:
            return self.get_price(date=self.get_pre_trade_day(date=date, sec_code=sec_code),
                                  sec_code=sec_code, price_type=price_type)  # 返回前一交易日价格

    def get_volume(self, sec_code: str, start_date: str, end_date: str, freq: str):
        table_name = sec_code + '_' + fq_trans(freq)
        query = "select amount from stock.%s where trade_date between '%s' and '%s'" \
                % (table_name, start_date, end_date)
        self.cursor.execute(query)
        volume = np.array(self.cursor.fetchall()).flatten().tolist()
        return volume

    # 回测开始时确定指定范围内的第一个交易日和前一个交易日，前一个交易日不必在范围内
    def init_start_trade_date(self, start_date: str, end_date: str):
        warnings.filterwarnings("ignore")
        # 以开始日期之后的第一个交易日为当前日期
        current_dt = self.trade_cal.loc[start_date: end_date][self.trade_cal['is_open'] == 1]
        current_dt = to_date(current_dt.index[0])
        # 以开始日期之前的最后一个交易日为前一个日期
        previous_dt = self.trade_cal.loc[: start_date][self.trade_cal['is_open'] == 1]
        previous_dt = to_date(previous_dt.index[-1])
        #
        return current_dt, previous_dt

    # 判断是否是交易日
    def is_marketday(self, date: datetime):
        return self.trade_cal.loc[to_date_str(date)]['is_open']

    #
    def get_index_data(self, index_code: str, columns: List[str], start_date: str,
                       end_date: str, freq: str):
        table_name = index_code[:6] + '_' + fq_trans(freq)
        query = "select %s from indexes.%s where trade_date between '%s' and '%s'" \
                % (','.join(columns), table_name, to_date_str(start_date), to_date_str(end_date))
        self.cursor.execute(query)
        data = pd.DataFrame(np.array(self.cursor.fetchall()), columns=[col[0] for col in self.cursor.description])
        return data[columns]

    #
    def is_trade(self, code: str, date: str):
        query = "select trade_date from %s_daily where trade_date='%s'" % (code[:6], date)
        self.cursor.execute(query)
        re = np.array(self.cursor.fetchall())
        if len(re) == 0:
            return False
        else:
            return True

    def __del__(self):
        self.cursor.close()
        self.connect.close()


class DataClientORM(object):
    engine = None

    def __init__(self, **kwargs):
        host = kwargs.get("host", 'localhost')
        port = kwargs.get("port", 3306)
        user = kwargs.get("user", 'root')
        passwd = kwargs.get("passwd", 'qq16281091')
        db = kwargs.get("db", 'stock')
        charset = kwargs.get("charset", 'utf8')
        self.engine = create_engine("mysql://%s:%s@%s:%s/%s?%s" % (user, passwd, host, port, db, charset))


data_client = DataClient()
