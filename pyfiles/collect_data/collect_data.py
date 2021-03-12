# -*- coding: utf-8 -*-
from opendatatools import swindex
from pyfiles.tools import *
import sqlalchemy as sa
import pymongo
import tushare as ts
import datetime
import time
from typing import List


def get_sw_index():
    """
    调用opendatatools库采集申万一级行业指数行情
    :return:
    """
    engine = sa.create_engine('mysql+mysqldb://root:qq16281091@localhost:3306/indexes?charset=utf8')
    indexes = ['801010', '801020', '801030', '801040', '801050',
               '801080', '801110', '801120', '801130', '801140',
               '801150', '801160', '801170', '801180', '801200',
               '801210', '801230', '801710', '801720', '801730',
               '801740', '801750', '801760', '801770', '801780',
               '801790', '801880', '801890']
    columns_order = ['date', 'index_code', 'index_name', 'open', 'close',
                     'high', 'low', 'change_pct', 'vol', 'amount']
    for i in range(0, len(indexes)):
        print(indexes[i] + ' start')
        data, msg = swindex.get_index_daily(indexes[i], start_date='1999-12-30',
                                            end_date='2020-9-18')
        data = data[columns_order]
        data.rename(columns={'date': 'trade_date'}, inplace=True)
        indicator, mm = swindex.get_index_dailyindicator(indexes[i], start_date='1999-12-30',
                                                         end_date='2020-9-18', freq='D')
        indicator = indicator[['avg_float_mv', 'date', 'dividend_yield_ratio', 'float_mv',
                               'pb', 'pe', 'turn_rate', 'turnover_pct', 'vwap']]
        indicator.rename(columns={'date': 'trade_date'}, inplace=True)
        data.set_index('trade_date', inplace=True)
        indicator.set_index('trade_date', inplace=True)
        res = data.merge(indicator, left_index=True, right_index=True, how='left')
        res.rename(columns={'change_pct': 'chg_pct', 'turn_rate': 'turnover_rate',
                   'vwap': 'avg_price'}, inplace=True)
        res.to_sql(name=indexes[i]+'_daily', con=engine, if_exists='append', index=True,
                   dtype={'trade_date': sa.DateTime()})
        engine.execute("alter table indexes.%s_daily add primary key(trade_date);" % indexes[i])
        print(indexes[i] + ' end')


def get_fina_data(attrs: List[str] = None):
    """
    从tushare接口获取财务数据并存入mongoDB数据库中

    :return:
    """
    client = pymongo.MongoClient(host='localhost', port=27017)
    db = client['fina_db']
    pro = ts.pro_api()
    data = pro.stock_basic(list_status='P', exchange="SSE", fields='ts_code,symbol,name,list_date')
    # 设置起始位置
    # start_index = data['ts_code'].tolist().index('300380.SZ')+1
    start_index = 0
    # 当表还未创建时，判断对应表是否已存在
    if attrs is None and 'fina_'+data['ts_code'][start_index][:6] in db.collection_names():
        print(data['ts_code'][start_index] + '已存在')
        return
    #
    for i in range(start_index, len(data)):
        code = data['ts_code'][i]
        #
        print(code + " start")
        if attrs is None:  # 向表中插入原始数据
            fina_data = pro.fina_indicator(ts_code=code)
            db['fina_' + code[:6]].insert_many(fina_data.to_dict(orient='record'))
        else:  # 向表中追加数据
            fina_data = pro.fina_indicator(ts_code=code, fields='end_date,'+','.join(attrs))
            for j in range(len(fina_data)):
                # print(fina_data.loc[j, fina_data.columns[1:]].to_dict())
                db['fina_'+code[:6]].update(spec={"ts_code": code, "end_date": fina_data.loc[j, 'end_date']},
                                            document={"$set": fina_data.loc[j, fina_data.columns[1:]].to_dict()})
        #
        print(code + " store completely")
        time.sleep(0.2)
    client.close()


def get_income_data():
    """
    调用tushare接口获取个股利润表数据存入mongoDB数据库中
    :return:
    """
    client = pymongo.MongoClient(host='localhost', port=27017)
    db = client['income_db']
    pro = ts.pro_api()
    basic_data = pro.stock_basic(list_status='L', exchange='', fields='ts_code,symbol,name,list_date')
    #
    # start_index = 201
    start_index = basic_data['ts_code'].tolist().index('603693.SH')+1
    # 判断对应表是否已存在
    if 'income_' + basic_data['ts_code'][start_index][:6] in db.collection_names():
        print(basic_data['ts_code'][start_index] + '已存在')
        return
    #
    for i in range(start_index, len(basic_data)):
        code = basic_data['ts_code'][i]
        print(code + ' start')
        #
        income_data = pro.income(ts_code=code)
        db['income_' + code[:6]].insert_many(income_data.to_dict(orient='record'))
        #
        print(code + ' stor completely')
        time.sleep(0.5)
    client.close()


def get_balance_data():
    """
    调用tushare接口获取资产负债表数据并存储到mongDB数据库中
    :return:
    """
    client = pymongo.MongoClient(host='localhost', port=27017)
    db = client['balance_db']
    pro = ts.pro_api()
    basic_data = pro.stock_basic(list_status='L', exchange='', fields='ts_code,symbol,list_date')
    #
    # start_index = 801
    start_index = basic_data['ts_code'].tolist().index('688078.SH')+1
    # 判断对应表是否已存在
    if 'balance_' + basic_data['ts_code'][start_index][:6] in db.collection_names():
        print(basic_data['ts_code'][start_index] + '已存在')
        return
    #
    for i in range(start_index, len(basic_data)):
        code = basic_data['ts_code'][i]
        print(code + ' start')
        #
        balance_data = pro.balancesheet(ts_code=code)
        db['balance_' + code[:6]].insert_many(balance_data.to_dict(orient='record'))
        #
        print(code + ' store completely')
        time.sleep(0.5)
    client.close()


def get_cashflow_data():
    """
    从tushare接口获取现金流量数据并存入mongoDB数据库中
    :return:
    """
    client = pymongo.MongoClient(host='localhost', port=27017)
    db = client['cashflow_db']
    pro = ts.pro_api()
    basic_data = pro.stock_basic(list_status='L', exchange='', fields='ts_code,symbol,list_date')
    #
    # start_index = 1501
    start_index = basic_data['ts_code'].tolist().index('603333.SH')+1
    # 判断对应表是否已存在
    if 'cashflow_' + basic_data['ts_code'][start_index][:6] in db.collection_names():
        print(basic_data['ts_code'][start_index] + '已存在')
        return
    #
    for i in range(start_index, len(basic_data)):
        code = basic_data['ts_code'][i]
        print(code + ' start')
        #
        cashflow_data = pro.cashflow(ts_code=code)
        db['cashflow_'+code[:6]].insert_many(cashflow_data.to_dict(orient='record'))
        #
        print(code + ' store completely')
        time.sleep(0.5)
    client.close()


def get_stock_k(code: str, start_date=None, freq='D'):
    """
    从tushare获取指定股票的k线数据并存入到Mysql数据库中，在原先数据的基础上添加每日指标数据
    :param code: 股票代码
    :param start_date: 数据的起始日期
    :param freq: 数据频率，'D','W','M','Y'分别表示日、周、月、年
    :return:
    """
    table_name = code[:6] + '_' + fq_trans(freq)
    conn = sa.create_engine("mysql+mysqldb://root:qq16281091@localhost:3306/stock?charset=utf8")
    #
    df = ts.pro_bar(ts_code=code, start_date=start_date, adj='qfq', ma=[5, 10, 20, 30, 60, 120, 250],
                    factors=['tor', 'vr'], adjfactor=True)
    if df is None:
        return
    if freq == 'D':
        indicator_df = ts.pro_api().daily_basic(ts_code=code, start_date=start_date)
        # print(indicator_df.drop(['ts_code', 'close', 'turnover_rate', 'volume_ratio'], axis=1))
        if indicator_df is not None and len(indicator_df) > 0:
            df = pd.merge(left=df, right=indicator_df.drop(['ts_code', 'close', 'turnover_rate', 'volume_ratio'], axis=1),
                          on='trade_date', how='left')
    # print(df.columns)
    df.to_sql(name=table_name, con=conn, if_exists='append', index=False,
              dtype={'trade_date': sa.DateTime()})
    #
    conn.execute("alter table " + table_name + " add primary key(trade_date);")


def get_index_k(code: str, start_date=None, freq='D'):
    """
    从tushare接口获取指定指数的k线数据并存入MySQL数据库中
    :param code: 指数代码
    :param start_date: 开始日期
    :param freq: 频率，同上
    :return:
    """
    table_name = code[:6] + '_' + fq_trans(freq)
    print(code + " start")
    #
    conn = sa.create_engine("mysql+mysqldb://root:qq16281091@localhost:3306/indexes?charset=utf8")
    df = ts.pro_bar(ts_code=code, asset='I', ma=[5, 10, 20, 30, 60, 120, 250])
    df.to_sql(name=table_name, con=conn, if_exists='append', index=False,
              dtype={'trade_date': sa.DateTime()})
    conn.execute("alter table " + table_name + " add primary key(trade_date);")
    #
    print(code + "store completely")


def stock_dk():
    """
    从tushare获取股票代表，对每支股分别调用get_stock_k函数向数据库中存数据
    :return:
    """
    ts.set_token(token="92c6ece658c377bcc32995a68319cf01696e1266ed60be0ae0dd0947")
    pro = ts.pro_api()
    data = pro.stock_basic(list_status='D', exchange="SSE", fields='ts_code,symbol,name,list_date')
    #
    start_index = 0
    # start_index = data['ts_code'].tolist().index('605179.SH') + 1
    for i in range(start_index, start_index + 300):
        code = data['ts_code'][i]
        start_date = data['list_date'][i]
        print(code + " start")
        #
        start_date = datetime.datetime.strptime(start_date, "%Y%m%d")
        start_date += datetime.timedelta(days=1)
        start_date = start_date.strftime("%Y%m%d")
        get_stock_k(code, start_date)
        #
        print(code + " store completely")


def index_dk():
    """
    指定要获取的指数列表，对每个指数分别调用get_index_k将数据存入数据库
    :return:
    """
    ts.set_token(token='92c6ece658c377bcc32995a68319cf01696e1266ed60be0ae0dd0947')
    pro = ts.pro_api()
    indexs = ['399300.SZ', '000009.SH', '000010.SH', '000016.SH', '399001.SZ', '399005.SZ', '399006.SZ', '399005.SZ',
              '000852.SH']
    # for code in indexs:
    #     init_index_k(code)
    get_index_k('000852.SH')


def get_backup_dk():
    """
    从tushare接口获取个股其他的每日指标，包括市值、行业等数据存入MongoDB数据库
    :return:
    """
    client = pymongo.MongoClient(host='localhost', port=27017)
    db = client['backup_daily_db']
    pro = ts.pro_api()
    basic_data = pro.stock_basic(list_status='L', exchange='', fields='ts_code,symbol,list_date')
    #
    # start_index = 0
    start_index = basic_data['ts_code'].tolist().index('603590.SH') + 1
    # 判断对应表是否已存在
    if 'backup_daily_' + basic_data['ts_code'][start_index][:6] in db.collection_names():
        print(basic_data['ts_code'][start_index] + '已存在')
        return
    #
    for i in range(start_index, start_index+500):
        code = basic_data['ts_code'][i]
        print(code + ' start')
        #
        df = pro.bak_daily(ts_code=code)
        df = df[df.columns[15:]]
        db['backup_daily_'+code[:6]].insert_many(df.to_dict(orient='record'))
        #
        print(code + ' store completely')
        time.sleep(0.5)


if __name__ == '__main__':
    ts.set_token('92c6ece658c377bcc32995a68319cf01696e1266ed60be0ae0dd0947')
    # get_sw_index()
    # get_fina_data()
    stock_dk()
