# -*- coding: utf-8 -*-
"""
    添加异常处理
"""
import MySQLdb as sql
from sqlalchemy import create_engine
import numpy as np
import datetime
import pandas as pd
import warnings
from typing import List, Iterable
import pymongo
import tushare as ts
from pyfiles.tools import *


class DataClient(object):
    connect = None
    cursor = None
    trade_cal = None
    mongo_client = None
    pro = None

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
        query = "select * from basic_info.trade_cal"
        self.cursor.execute(query)
        self.trade_cal = pd.DataFrame(np.array(self.cursor.fetchall()),
                                      columns=[col[0] for col in self.cursor.description])
        # 将datetime类型设置为索引，输出整个对象时只显示日期，实际仍是datetime类型
        self.trade_cal.set_index('cal_date', inplace=True)
        # print(self.trade_cal)
        ts.set_token('92c6ece658c377bcc32995a68319cf01696e1266ed60be0ae0dd0947')
        self.pro = ts.pro_api()

    def stock_basic(self, list_status: str = 'L', exchange: str = None) -> pd.DataFrame:
        """
        股票基本信息，数据采集自tushare stock_basic接口
        :param list_status: 上市状态 L上市， D退市，P暂停上市，默认为L
        :param exchange: 交易所，SSE上交所，SZSE深交所，默认为全选
        :return:
        """
        term = []
        if list_status is None and exchange is None:
            query = "select * from basic_info.stock_basic"
        else:
            if list_status is not None:
                term.append("list_status='%s'" % list_status)
            if exchange is not None:
                term.append("exchange='%s'" % exchange)
            query = "select * from basic_info.stock_basic where " + ' and '.join(term)
        self.cursor.execute(query)
        stock_basic = pd.DataFrame(np.array(self.cursor.fetchall()),
                                   columns=[col[0] for col in self.cursor.description])
        return stock_basic

    def index_basic(self, ts_code: str = None, name: str = None, market: str = None,
                    publisher: str = None, category: str = None) -> pd.DataFrame:
        """
        获取指数的基本信息，数据取自tushare index_basic接口，
        :param ts_code: 指数代码
        :param name: 指数名称
        :param market: 市场(MSCI,CSI,SSE,SZSE,CIC,SW,OTH)，默认为全选
        :param publisher: 发布商
        :param category: 指数类别
        :return:
        """
        term = []
        if ts_code is not None:
            term = term.append("ts_code='%s'" % ts_code)
        if name is not None:
            term = term.append("name='%s'" % name)
        if market is not None:
            term = term.append("market='%s'" % market)
        if publisher is not None:
            term = term.append("publisher='%s'" % publisher)
        if category is not None:
            term = term.append("category='%s'" % category)
        query = "select * from basic_info.index_basic"
        if len(term) > 0:
            query = query + ' where ' + ' and '.join(term)
        self.cursor.execute(query)
        index_basic = pd.DataFrame(np.array(self.cursor.fetchall()),
                                   columns=[col[0] for col in self.cursor.description])
        return index_basic

    def index_weight(self, index_code: str, trade_date: datetime.date) -> pd.DataFrame:
        """
        从tushare获取指定日期的指数成分，
          由于指数成分及权重是变化的，所以获取成分时需要指定日期，
          tushare的index_weight每月更新1至两次
        :param index_code: 指数代码
        :param trade_date: 交易日期
        :return:
        """
        # 日期区间从上个月的1日开始到交易日期，
        # 由于trade_date可能为1月，所以通过timedelta来获取开始日期
        start_date = trade_date - datetime.timedelta(days=31)
        end_date = datetime.date(trade_date.year, trade_date.month, trade_date.day)
        data = self.pro.index_weight(index_code=index_code,
                                     start_date=to_date_str(start_date, split=''),
                                     end_date=to_date_str(end_date, split=''))
        # 将获取数据的trade_date项去重后的第一个日期就是目标指数成分的日期
        target_date = data['trade_date'].drop_duplicates()[0]
        return data[data['trade_date'] == target_date]

    def get_pre_trade_dt(self, sec_code: str, dt: str) -> str:
        """
        获取指定证券在指定日期前的最后一个交易日
        :param sec_code: 证券代码
        :param dt: 指定的日期
        :return:
        """
        query = "select trade_date from %s_daily where trade_date < '%s'" % (sec_code[:6], dt)
        self.cursor.execute(query)
        dates = np.array(self.cursor.fetchall()).ravel()
        # 应先转化为str
        if to_date_str(dates[-1].date()) == dt:
            return to_date_str(dates[-2].date())
        return to_date_str(dates[-1].date())

    def get_back_trade_dt(self, sec_code: str, dt: str) -> str:
        """
        获取指定证券在指定日期后的第一个交易日
        :param sec_code: 指定证券代码
        :param dt: 指定的日期
        :return:
        """
        query = "select trade_date from %s_daily where trade_date > '%s'" % (sec_code[:6], dt)
        self.cursor.execute(query)
        dates = np.array(self.cursor.fetchall()).ravel()
        # 应先转化为str
        if to_date_str(dates[0].date()) == dt:
            return to_date_str(dates[1].date())
        return to_date_str(dates[0].date())

    def get_ma(self, days: int, dt: str, sec_code: str, fq: str) -> float:
        """
        计算均线
        :param days: 均值的天数
        :param dt: 日期
        :param sec_code: 证券代码
        :param fq: 均值频率，'D'表示日均线，’W'表示周均线，‘M'表示月均线，’Y‘表示年均线
        :return: 目标均值
        """
        table_name = sec_code[:6] + '_' + fq_trans(fq)
        #
        query = "select %s from stock.%s where trade_date='%s'" \
                % ('ma' + str(days), table_name, dt)
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
            return self.get_ma(days=days, dt=self.get_pre_trade_dt(sec_code=sec_code, dt=dt),
                               sec_code=sec_code, fq=fq)  # 返回上一个交易日的数据

    def get_price(self, dt: str, sec_code: str, price_type: str) -> float:
        """
        获取指定证券指定日期的指定类型价格
        :param dt: 指定日期
        :param sec_code: 指定证券代码
        :param price_type: 价格类型，有开盘价（high）、收盘价（close）、最高价（high）、最低价（low）
        :return:
        """
        # print(price_type)
        # print(sec_code)
        # print(dt)
        query = "select %s from stock.%s where trade_date='%s'" \
                % (price_type, sec_code[:6] + '_daily', dt)
        try:
            self.cursor.execute(query)
        except Exception as e:
            raise ParamError("未找到%s表，或价格类型（open/close/high/low）错误")
        res = np.array(self.cursor.fetchall())
        # print(res[0][0])
        if len(res) > 0 and len(res[0]) > 0:
            return res[0][0]
        else:
            return self.get_price(dt=self.get_pre_trade_dt(dt=dt, sec_code=sec_code),
                                  sec_code=sec_code, price_type=price_type)  # 返回前一交易日价格

    def get_volume(self, sec_code: str, start_dt: str, end_dt: str, freq: str) -> Iterable:
        """
        获取指定证券在指定日期范围内的交易量
        :param sec_code: 证券代码
        :param start_dt: 开始日期
        :param end_dt: 结束日期
        :param freq: 数据频率（D/W/M/Y）
        :return: list
        """
        table_name = sec_code + '_' + fq_trans(freq)
        query = "select amount from stock.%s where trade_date between '%s' and '%s'" \
                % (table_name, start_dt, end_dt)
        self.cursor.execute(query)
        volume = np.array(self.cursor.fetchall()).flatten().tolist()
        return volume

    def init_start_trade_date(self, start_dt: str, end_dt: str):
        """
        在回测开始前获取第一次交易的日期，包括第一个交易日以及该交易日前的最后一个交易日
        :param start_dt: 回测的开始日期
        :param end_dt: 回测的结束日期
        :return:
        """
        warnings.filterwarnings("ignore")
        # 以开始日期之后的第一个交易日为当前日期
        current_dt = self.trade_cal.loc[start_dt: end_dt][self.trade_cal['is_open'] == 1]
        current_date = to_date(current_dt.index[0])
        # 以开始日期之前的最后一个交易日为前一个日期
        previous_dt = self.trade_cal.loc[: start_dt][self.trade_cal['is_open'] == 1]
        previous_date = to_date(previous_dt.index[-1])
        #
        return current_date, previous_date

    def is_marketday(self, date: datetime.date) -> int:
        """
        判断一个日期是否是交易日
        :param date: 需要判断的日期
        :return: 0/1
        """
        return self.trade_cal.loc[to_date_str(date)]['is_open']

    def get_index_data(self, index_code: str, columns: List[str], start_dt: str,
                       end_dt: str, freq: str) -> pd.DataFrame:
        """
        获取指数在指定时间范围的行情数据，获取的数据类别由参数指定
        :param index_code: 指数代码
        :param columns: 需要获取的数据类别列表
        :param start_dt: 开始日期
        :param end_dt: 结束日期
        :param freq: 数据频率（D/W/M/Y）
        :return: dataframe
        """
        table_name = index_code[:6] + '_' + fq_trans(freq)
        query = "select %s from indexes.%s where trade_date between '%s' and '%s'" \
                % (','.join(columns), table_name, start_dt, end_dt)
        self.cursor.execute(query)
        data = pd.DataFrame(np.array(self.cursor.fetchall()), columns=[col[0] for col in self.cursor.description])
        return data[columns]

    def is_trade(self, sec_code: str, dt: str) -> bool:
        """
        判断指定证券在指定日期是否交易
        :param sec_code: 证券代码
        :param dt: 日期
        :return: True/False
        """
        query = "select trade_date from %s_daily where trade_date='%s'" % (sec_code[:6], dt)
        self.cursor.execute(query)
        re = np.array(self.cursor.fetchall())
        if len(re) == 0:
            return False
        else:
            return True

    def get_fina_report(self, sec_code: str, year: int, quarter: int) -> pd.DataFrame:
        """
        获取某支证券在某次财报
        ** 当前实现方法可以考虑直接通过year,quarter参数值直接获得报告期，进而获取相应财报
        :param sec_code: 目标证券代码
        :param year: 财报年
        :param quarter: 财报季
        :return:
        """
        # 获取今年到下一年一季度的所有财报
        first_day = datetime.date(year, 1, 1)
        last_day = datetime.date(year + 1, 3, 31)  # 考虑quarter为4的情况
        query = {"end_date": {"$gte": to_date_str(first_day, split=''),
                              "$lte": to_date_str(last_day, split='')}}
        res = self.mongo_client['fina_db']['fina_'+sec_code[:6]].find(query, {'_id': 0})
        # 将获取的数据按报告期递增排序，按季度quarter值来取相应数据
        df = pd.DataFrame(list(res)).sort_values(by='end_date').reset_index(drop=True)
        if len(df) < quarter:
            raise ParamError(sec_code + " 季度错误")
        else:
            if math.ceil(int(df.loc[quarter-1, 'end_date'][4:6])/3) != quarter:
                # print(df[['ts_code', 'end_date', 'ann_date']])
                raise ParamError("%s%d年%d季度财报出现问题" % (sec_code, year, quarter))
            return df.loc[quarter-1]

    def get_fina_data(self, sec_code: str, columns: List[str], **kwargs) -> pd.DataFrame:
        """
        & 本方法是通过日期区间来获取财报数据，获取指定日期范围内的所有目标数据，
          get_fina_report是获取一期财报的数据
        获取指定证券在指定时间范围内的财务数据，财务数据的类别由columns参数决定
        :param sec_code: 指定证券代码
        :param columns: 指定的账务数据类别，key为指定的数据名称，value为1表示选中
        :return:
        """
        start_dt = kwargs.get("start_dt", '1970-01-01')
        end_dt = kwargs.get("end_dt", datetime.datetime.now().date().isoformat())
        limit = kwargs.get("limit", 10)
        # year = kwargs.get("year", None)
        # quarter = kwargs.get("quarter", None)
        attrs = dict()
        # 设置从mongoGO数据库获取的数据属性
        for attr in columns:
            attrs[attr] = 1
        if '_id' not in attrs:
            attrs['_id'] = 0
        # 获取财报发布日在指定的日期区间内财报数据并返回
        query = {"ann_date": {"$gte": to_date_str(to_date(start_dt), split=''),
                              "$lte": to_date_str(to_date(end_dt), split='')}}
        res = self.mongo_client['fina_db']['fina_' + sec_code[:6]].find(query, attrs).limit(limit)
        df = pd.DataFrame(list(res))
        # 更改日期格式，原格式（YYYYMMDD）更改为（YYYY-MM-DD）
        if 'end_date' in df.columns:
            for i in range(len(df)):
                dt = df['end_date'][i]
                df.loc[i, 'end_date'] = "%s-%s-%s" % (dt[: 4], dt[4: 6], dt[6: 8])
        return df

    def get_fina_list(self, sec_codes: List[str], columns: List[str], **kwargs):
        """
        该方法用于获取证券列表在指定日期之间的最新一期财报或指定年度与季度的财务数据
        该方法调用get_fina_report以及get_fina_data来获取数据，并将获取的数据转化为特定格式
        :param sec_codes: 证券代码列表
        :param columns: 需要的财务数据属性
        :return:
        """
        fina_data = []
        end_dt = kwargs.get("end_dt", datetime.datetime.now().date().isoformat())
        year = kwargs.get("year", None)
        quarter = kwargs.get("quarter", None)
        # 以列表以及字典的形式分别存储需要的财务数据属性，分别用于两个财务函数
        t_columns = []
        attrs = dict()
        for attr in columns:
            t_columns.append(attr)
            attrs[attr] = 1
        if '_id' not in attrs:
            attrs['_id'] = 0
        if 'ts_code' not in attrs:
            attrs['ts_code'] = 1
            t_columns.append('ts_code')
        # 如果设置了year和quarter参数，则优先使用该参数
        if year is not None and quarter is not None:
            for sec_code in sec_codes:
                res = self.get_fina_report(sec_code=sec_code, year=year, quarter=quarter)[t_columns].to_dict()
                fina_data.append(res)
            return pd.DataFrame(fina_data)
        query = {"ann_date": {"$lte": to_date_str(to_date(end_dt), split='')}}
        # print(sec_codes)
        for sec_code in sec_codes:
            res = self.mongo_client['fina_db']['fina_'+sec_code[:6]].find(query, attrs).limit(1)
            # print(list(res))
            fina_data.extend(list(res))
        return pd.DataFrame(fina_data)
        # 由于dataframe在动态改变大小时效率不高，所以以最后将dict列表一次性转化为dataframe

    def get_fina_date_range(self, sec_codes: str or List[str], year: int, quarter: int):
        """
        获取各个股票在某年某季度财报发布日期到下一季度财报发布日期的范围，
        比如quarter为2，那么返回的日期范围为2季度发布日到3季报发布日的前一天
        普通情况为按季度的顺序公布，应注意特殊情况，即年报与下一年一季报的公布顺序。
        ** 当前还未考虑年报与下一年一季报公布日期的特殊情况，还未将end_date提前一天
        :param quarter: 季度
        :param year: 年
        :param sec_codes: 证券代码或证券代码代表
        :return:
        """
        # 根据year和quarter参数值设置日期范围
        first_day = datetime.date(year, 1, 1)
        last_day = datetime.date(year+1, 3, 31)  # 考虑quarter为4的情况
        #
        if isinstance(sec_codes, six.string_types):
            sec_codes = [sec_codes]
        dt_range = pd.DataFrame(columns=['sec_code', 'start_date', 'end_date'])
        dt_range['sec_code'] = sec_codes
        dt_range.set_index('sec_code', inplace=True)
        for sec_code in sec_codes:
            query = {"end_date": {"$gte": to_date_str(first_day, split=''),
                                  "$lte": to_date_str(last_day, split='')}}
            res = self.mongo_client['fina_db']['fina_'+sec_code[:6]].find(query, {'_id': 0})
            # print(list(res))
            df = pd.DataFrame(list(res)).sort_values(by='end_date').reset_index(drop=True)
            # print(df[['ann_date', 'end_date']])
            # 在设置区间日期时，应考虑数据的正确性，具体是通过财报个数与季度来判断
            if len(df) < quarter:
                raise ParamError(sec_code + " 季度错误")
            elif len(df) == quarter:
                dt_range.loc[sec_code, 'start_date'] = chg_dt_format(df['ann_date'][quarter-1])
                dt_range.loc[sec_code, 'end_date'] = (datetime.datetime.now().date() - datetime.timedelta(days=1))\
                    .isoformat()
            else:
                dt_range.loc[sec_code, 'start_date'] = chg_dt_format((df['ann_date'][quarter-1]))
                dt_range.loc[sec_code, 'end_date'] = (datetime.datetime.strptime(df['ann_date'][quarter], "%Y%m%d")
                                                      - datetime.timedelta(days=1)).isoformat()
                if dt_range.loc[sec_code, 'start_date'] > dt_range.loc[sec_code, 'end_date']:
                    print("%s start_date: %s, end_date: %s"
                          % (sec_code, dt_range.loc[sec_code, 'start_date'], dt_range.loc[sec_code, 'end_date']))
        return dt_range

    def get_price_list(self, dt: str, sec_codes: List[str], price_type):
        """
        获取一系列证券的价格
        :param dt:
        :param sec_codes:
        :param price_type:
        :return:
        """
        res = pd.DataFrame()
        res.set_index(sec_codes)
        for code in sec_codes:
            price = self.get_price(dt=dt, sec_code=code, price_type=price_type)
            res.loc[code][price_type] = price
        return res

    def get_pe(self, dt: str, sec_code: str, pe_type: str) -> float:
        """
        获取指定个股的市盈率，市盈市的种类分为3种，静态、动态以及滚动市盈率，由dtype参数指定
        ** 当前还未考虑年报还未发布的情况
        :param dt:
        :param sec_code:
        :param pe_type: 分为'S'，'D'，'T'分别表示静态、动态以及滚动
        :return:
        """
        price = self.get_price(dt=dt, sec_code=sec_code, price_type='close')
        if pe_type == 'S':
            # 需要获取去年年报的eps
            fina_end_dt = datetime.date(to_date(date=dt).year, 1, 1).isoformat()
            s_eps = self.get_fina_data(sec_code=sec_code, columns=['end_date', 'eps'], end_dt=fina_end_dt, limit=1)
            # print(s_eps)
            try:
                s_eps.loc[0, 'eps']
            except Exception:
                print(sec_code + "异常")
            return float_precision(price/s_eps.loc[0, 'eps'], 2)
        elif pe_type == 'D':
            # 动态，需要估计今年的eps值，估计的方法是利用最新季报来估计全年，比如一季报eps*4
            fina_data = self.get_fina_data(sec_code=sec_code, columns=['end_date', 'eps'], end_dt=dt, limit=4)
            quarter = get_quarter(to_date(fina_data.loc[0, 'end_date']))
            return float_precision(price/(fina_data.loc[0, 'eps']/quarter*4), 2)
        elif pe_type == 'T':
            # 使用过去12个月的eps
            fina_data = self.get_fina_data(sec_code=sec_code, columns=['end_date', 'eps'], end_dt=dt, limit=5)
            if get_quarter(to_date(fina_data.loc[0, 'end_date'])) == 4:
                return float_precision(price/fina_data.loc[0, 'eps'], 2)
            else:
                eps = fina_data.loc[0, 'eps'] + fina_data.loc[3, 'eps'] - fina_data.loc[4, 'eps']
                return float_precision(price/eps, 2)
        else:
            raise ParamError("pe type error(S/D/T)")

    def get_ps(self, dt: str, sec_code: str) -> float:
        """
        计算指定证券在指定日期时的市净率ps，
        计算方法：当日的股价/最新一季财报每股净资产bps
        :param dt:
        :param sec_code:
        :return:
        """
        price = self.get_price(dt=dt, sec_code=sec_code, price_type='close')
        fina_data = self.get_fina_data(sec_code=sec_code, columns=['end_date', 'bps'], end_dt=dt, limit=1)
        return float_precision(price/fina_data.loc[0, 'bps'], 2)

    def get_pe_list(self, dt: str, sec_codes: List[str], pe_type: List[str]) -> pd.DataFrame:
        """
        调用get_pe方法为一系列股票获取指定类型的市盈率
        :param dt:
        :param sec_codes:
        :param pe_type:
        :return:
        """
        columns = list(map(lambda x: 'pe_' + str(x), pe_type))
        res = pd.DataFrame(columns=columns)
        res['sec_code'] = sec_codes
        res.set_index('sec_code', inplace=True)
        # print(res)
        for column in pe_type:
            for code in sec_codes:
                res.loc[code, 'pe_'+column] = self.get_pe(dt=dt, sec_code=code, pe_type=column)
        return res

    def get_ps_list(self, dt: str, sec_codes: List[str]) -> pd.DataFrame:
        res = pd.DataFrame(columns=['sec_code', 'ps'])
        res['sec_code'] = sec_codes
        res.set_index('sec_code', inplace=True)
        for sec_code in sec_codes:
            res.loc[sec_code, 'ps'] = self.get_ps(dt=dt, sec_code=sec_code)
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


# data_client = DataClient()
