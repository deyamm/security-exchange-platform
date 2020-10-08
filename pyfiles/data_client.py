# -*- coding: utf-8 -*-
import MySQLdb as sql
from sqlalchemy import create_engine
import numpy as np
import datetime
import pandas as pd
import warnings
from typing import List
import pymongo
from pyfiles.tools import *


class DataClient(object):
    connect = None
    cursor = None
    trade_cal = None
    mongo_client = None

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
        self.mongo_client = pymongo.MongoClient(host='localhost', port=27017)

        # 将整个交易日历存储下来
        query = "select * from trade_cal.trade_cal"
        self.cursor.execute(query)
        self.trade_cal = pd.DataFrame(np.array(self.cursor.fetchall()),
                                      columns=[col[0] for col in self.cursor.description])
        # 将datetime类型设置为索引，输出整个对象时只显示日期，实际仍是datetime类型
        self.trade_cal.set_index('cal_date', inplace=True)
        # print(self.trade_cal)

    def get_pre_trade_day(self, sec_code: str, date: str) -> str:
        """
        获取指定证券在指定日期前的最后一个交易日
        :param sec_code: 证券代码
        :param date: 指定的日期
        :return:
        """
        query = "select trade_date from %s_daily where trade_date < '%s'" % (sec_code[:6], date)
        self.cursor.execute(query)
        dates = np.array(self.cursor.fetchall()).ravel()
        # 应先转化为str
        if to_date_str(dates[-1].date()) == date:
            return to_date_str(dates[-2].date())
        return to_date_str(dates[-1].date())

    def get_back_trade_day(self, sec_code: str, date: str) -> str:
        """
        获取指定证券在指定日期后的第一个交易日
        :param sec_code: 指定证券代码
        :param date: 指定的日期
        :return:
        """
        query = "select trade_date from %s_daily where trade_date > '%s'" % (sec_code[:6], date)
        self.cursor.execute(query)
        dates = np.array(self.cursor.fetchall()).ravel()
        # 应先转化为str
        if to_date_str(dates[0].date()) == date:
            return to_date_str(dates[1].date())
        return to_date_str(dates[0].date())

    def get_ma(self, days: int, date: str, sec_code: str, fq: str) -> float:
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

    def get_price(self, date: str, sec_code: str, price_type: str) -> float:
        """
        获取指定证券指定日期的指定类型价格
        :param date: 指定日期
        :param sec_code: 指定证券代码
        :param price_type: 价格类型，有开盘价（high）、收盘价（close）、最高价（high）、最低价（low）
        :return:
        """
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

    def get_volume(self, sec_code: str, start_date: str, end_date: str, freq: str) -> List[float]:
        """
        获取指定证券在指定日期范围内的交易量
        :param sec_code: 证券代码
        :param start_date: 开始日期
        :param end_date: 结束日期
        :param freq: 数据频率（D/W/M/Y）
        :return: list
        """
        table_name = sec_code + '_' + fq_trans(freq)
        query = "select amount from stock.%s where trade_date between '%s' and '%s'" \
                % (table_name, start_date, end_date)
        self.cursor.execute(query)
        volume = np.array(self.cursor.fetchall()).flatten().tolist()
        return volume

    def init_start_trade_date(self, start_date: str, end_date: str) -> str:
        """
        在回测开始前获取第一次交易的日期，包括第一个交易日以及该交易日前的最后一个交易日
        :param start_date: 回测的开始日期
        :param end_date: 回测的结束日期
        :return:
        """
        warnings.filterwarnings("ignore")
        # 以开始日期之后的第一个交易日为当前日期
        current_dt = self.trade_cal.loc[start_date: end_date][self.trade_cal['is_open'] == 1]
        current_dt = to_date(current_dt.index[0])
        # 以开始日期之前的最后一个交易日为前一个日期
        previous_dt = self.trade_cal.loc[: start_date][self.trade_cal['is_open'] == 1]
        previous_dt = to_date(previous_dt.index[-1])
        #
        return current_dt, previous_dt

    def is_marketday(self, date: datetime) -> int:
        """
        判断一个日期是否是交易日
        :param date: 需要判断的日期
        :return: 0/1
        """
        return self.trade_cal.loc[to_date_str(date)]['is_open']

    def get_index_data(self, index_code: str, columns: List[str], start_date: str,
                       end_date: str, freq: str) -> pd.DataFrame:
        """
        获取指数在指定时间范围的行情数据，获取的数据类别由参数指定
        :param index_code: 指数代码
        :param columns: 需要获取的数据类别列表
        :param start_date: 开始日期
        :param end_date: 结束日期
        :param freq: 数据频率（D/W/M/Y）
        :return: dataframe
        """
        table_name = index_code[:6] + '_' + fq_trans(freq)
        query = "select %s from indexes.%s where trade_date between '%s' and '%s'" \
                % (','.join(columns), table_name, to_date_str(start_date), to_date_str(end_date))
        self.cursor.execute(query)
        data = pd.DataFrame(np.array(self.cursor.fetchall()), columns=[col[0] for col in self.cursor.description])
        return data[columns]

    def is_trade(self, sec_code: str, date: str) -> bool:
        """
        判断指定证券在指定日期是否交易
        :param sec_code: 证券代码
        :param date: 日期
        :return: True/False
        """
        query = "select trade_date from %s_daily where trade_date='%s'" % (sec_code[:6], date)
        self.cursor.execute(query)
        re = np.array(self.cursor.fetchall())
        if len(re) == 0:
            return False
        else:
            return True

    def get_fina_data(self, sec_code: str, columns: List[str], **kwargs) -> pd.DataFrame:
        """
        获取指定证券在指定时间范围内的财务数据，财务数据的类别由columns参数决定
        :param sec_code: 指定证券代码
        :param columns: 指定的账务数据类别，key为指定的数据名称，value为1表示选中
        :return:
        """
        start_date = kwargs.get("start_date", '1970-01-01')
        end_date = kwargs.get("end_date", datetime.datetime.now().date().isoformat())
        limit = kwargs.get("limit", 10)
        attrs = dict()
        #
        for attr in columns:
            attrs[attr] = 1
        if '_id' not in attrs:
            attrs['_id'] = 0
        #
        query = {"end_date": {"$gte": to_date_str(to_date(start_date), split=''),
                              "$lte": to_date_str(to_date(end_date), split='')}}
        res = self.mongo_client['fina_db']['fina_' + sec_code[:6]].find(query, attrs).limit(limit)
        df = pd.DataFrame(list(res))
        # 更改日期格式，原格式（YYYYMMDD）更改为（YYYY-MM-DD）
        for i in range(len(df)):
            dt = df['end_date'][i]
            df.loc[i, 'end_date'] = "%s-%s-%s" % (dt[: 4], dt[4: 6], dt[6: 8])
        return df

    def get_price_list(self, date: str, sec_codes: List[str], price_type):
        res = pd.DataFrame()
        res.set_index(sec_codes)
        for code in sec_codes:
            price = self.get_price(date=date, sec_code=code, price_type=price_type)
            res.loc[code][price_type] = price
        return res

    def get_pe(self, date: str, sec_code: str, pe_type: str) -> float:
        """
        获取指定个股的市盈率，市盈市的种类分为3种，静态、动态以及滚动市盈率，由dtype参数指定
        :param date:
        :param sec_code:
        :param pe_type: 分为'S'，'D'，'T'分别表示静态、动态以及滚动
        :return:
        """
        price = self.get_price(date=date, sec_code=sec_code, price_type='close')
        if pe_type == 'S':
            # 需要获取去年年报的eps
            fina_end_date = datetime.date(to_date(date=date).year, 1, 1).isoformat()
            s_eps = self.get_fina_data(sec_code=sec_code, columns=['end_date', 'eps'], end_date=fina_end_date, limit=1)
            # print(s_eps)
            return float_precision(price/s_eps.loc[0, 'eps'], 2)
        elif pe_type == 'D':
            # 动态，需要估计今年的eps值，估计的方法是利用最新季报来估计全年，比如一季报eps*4
            fina_data = self.get_fina_data(sec_code=sec_code, columns=['end_date', 'eps'], end_date=date, limit=4)
            quarter = get_quarter(to_date(fina_data.loc[0, 'end_date']))
            return float_precision(price/(fina_data.loc[0, 'eps']/quarter*4), 2)
        elif pe_type == 'T':
            # 使用过去12个月的eps
            fina_data = self.get_fina_data(sec_code=sec_code, columns=['end_date', 'eps'], end_date=date, limit=5)
            if get_quarter(to_date(fina_data.loc[0, 'end_date'])) == 4:
                return float_precision(price/fina_data.loc[0, 'eps'], 2)
            else:
                eps = fina_data.loc[0, 'eps'] + fina_data.loc[3, 'eps'] - fina_data.loc[4, 'eps']
                return float_precision(price/eps, 2)
        else:
            raise ParamError("pe type error(S/D/T)")

    def get_pe_list(self, date: str, sec_codes: List[str], pe_type: List[str]):
        """
        调用get_pe方法为一系列股票获取指定类型的市盈率
        :param date:
        :param sec_codes:
        :param pe_type:
        :return:
        """
        res = pd.DataFrame(columns=pe_type)
        res['sec_code'] = sec_codes
        res.set_index('sec_code', inplace=True)
        # print(res)
        for column in res.columns:
            for code in sec_codes:
                res.loc[code, column] = self.get_pe(date=date, sec_code=code, pe_type=column)
        return res

    def __del__(self):
        self.cursor.close()
        self.connect.close()
        self.mongo_client.close()


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
