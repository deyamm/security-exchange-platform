# -*- coding: utf-8 -*-
# 在初始化数据的基础上，向数据库中更新数据
from pyfiles.data_client.collect_data import *
from pyfiles.com_lib import *
from pyfiles.data_client.database_client import *
import sqlalchemy as sa
import datetime
import tushare as ts
import numpy as np


class UpdateDataClient(object):

    def __init__(self, **kwargs):
        self.mysql = MySqlServer()
        #
        self.mongo = MongoClient()
        #
        self.sql_orm = DataClientORM()
        #
        self.mas = [5, 10, 20, 30, 60, 120, 250]
        #
        self.pro = TushareClient().get_pro()

    def update_daily_k(self, sec_code: str, start_dt: str = None, end_dt: str = None):
        """
        :param sec_code:
        :param start_dt:
        :param end_dt:
        :return:
        """
        print(sec_code + " update start")
        # 获取新的数据
        try:
            query = "select trade_date from stock.%s_daily" % sec_code[:6]
            dates = np.sort(self.mysql.query(query, return_type='np').ravel())
            if start_dt is None:
                start_dt = chg_dt(to_date_str(dates[-1], only_date=True), 1, 'front')
            # 如果不指定结束日期，则将当前日期作为最后一天
            if end_dt is None:
                end_dt = datetime.datetime.now().date().isoformat()
            df = ts.pro_bar(ts_code=sec_code, start_date=start_dt, end_date=end_dt,
                            adj='qfq', ma=self.mas, factors=['tor', 'vr'], adjfactor=True)
        except Exception:
            df = ts.pro_bar(ts_code=sec_code, adj='qfq', ma=self.mas, factors=['tor', 'vr'],
                            adjfactor=True)
        # print(start_dt)
        # print(end_dt)
        # print(df)
        # 如果有新数据，则直接扩展到MySQL数据库中
        if df is not None:
            df.to_sql(name=sec_code[:6]+'_daily', con=self.sql_orm.engine, if_exists='append', index=False,
                      dtype={'trade_date': sa.DateTime()})
        else:
            df = pd.DataFrame()
        print(sec_code + " update completely, %d lines updated" % len(df))

    def execute_query(self, client_num: int, query: str):
        """
        该成员方法用于执行本地数据库的查询语句，并将数据以适合的方式返回，
        对于不同的数据库，该成员方法会分别调用相应的接口
        :param client_num:
        :param query:
        :return:
        """
        if client_num == 1:  # MySQLdb
            df = self.mysql.query(query)
            return df
        elif client_num == 2:  # mongo
            pass
        elif client_num == 3:  # sql engine
            pass
        else:
            raise ParamError("client number error(1/2/3)")

    def get_last_dt(self, ts_code: str, asset: str = 'E'):
        """
        获取数据库中指定资产最后数据的日期
        :param ts_code:
        :param asset:
        :return:
        """
        table_name = ts_code[:6] + '_' + fq_trans('D')
        if asset == 'I':
            query = "select trade_date from indexes.%s" % table_name
        elif asset == 'E':
            query = "select trade_date from stock.%s" % table_name
        else:
            raise ParamError("frequency error")
        dates = self.mysql.query(query).sort_values(by=['trade_date'])
        # print(dates)
        last_day = to_date_str(dates.loc[len(dates) - 1, 'trade_date'])
        return last_day

    def update_index_k(self, index_code: str, start_dt: str = None, end_dt: str = None):
        if start_dt is None:
            start_dt = self.get_last_dt(ts_code=index_code, asset='I')
        if end_dt is None:
            end_dt = datetime.date.today().isoformat()
        index_data = ts.pro_bar(api=self.pro, ts_code=index_code, asset='I', ma=[5, 10, 20, 30, 60, 120, 250])
        index_data.sort_values(by=['trade_date'], inplace=True)
        table_name = index_code[:6] + '_' + fq_trans('D')
        #
        added_data = index_data[index_data['trade_date'] > chg_dt_format(start_dt, '-', '')]
        added_data.to_sql(name=table_name, con=self.sql_orm.engine, schema='indexes', if_exists='append', index=False,
                          dtype={'trade_date': sa.DateTime()})
        print(index_code + " update successfully")


def daily_update():
    """
    每次更新的内容：
            1. 将未录入的数据加入数据库中
            2. 如果最新日期的复权因子发生变动，用复权因子更新整张表的价格
            3. 计算新加入数据的均线数据
    :return:
    """
    update_data_client = UpdateDataClient()
    ts_client = TushareClient()
    stock_basic = ts_client.pro.stock_basic()
    # 向数据库中添加新的数据
    start_index = 0
    for i in range(start_index, 1):
        # 向数据库中添加新的行情数据
        # time.sleep(0.05)
        # update_data_client.update_daily_k(sec_code=stock_basic['ts_code'][i])
        k_data = update_data_client.execute_query(1, "select * from stock.%s_daily" % stock_basic['ts_code'][i][:6])
        # print(k_data)
        latest_adj_factor = k_data.loc[len(k_data)-1, 'adj_factor']
        # t = k_data[k_data['ma5'] == np.nan]
        # 获取原表中数据的结束位置。
        # 由于新添加的数据中，前一定数量的均值数据是缺失的，
        # 再加上原表中同样有相同数量的缺失值，所以筛选出缺失的5日均值中，第5个位置的索引即是新添加数据开始的位置，
        # 因此，原表数据的结束位置就可以确定
        old_data_index = k_data[np.isnan(k_data['ma5'].fillna(value=np.nan))]['ma5'].index.tolist()[4] - 1
        adjust_rate = k_data.loc[old_data_index, 'adj_factor'] / latest_adj_factor
        update_data(k_data, adjust_rate)
        k_data.to_csv("../../logs/update.csv", index=False)
        # print(k_data.loc[3999])


def update_data(k_data, adjust_rate):
    """
    更新复权数据，包括每天的价格、均值以及计算新加入数据的均值缺失值
    :param k_data:
    :param adjust_rate:
    :return:
    """
    flag = 0
    for j in range(len(k_data)):
        k_data.loc[j, 'change'] = float_precision(k_data.loc[j, 'change'], 2)
        if k_data.loc[j, 'ma5'] is None and j >= 4:
            flag = 1
        if flag == 0:  # 根据复权因子更新数据库中的价格
            k_data.loc[j, 'pre_close'] = float_precision(k_data.loc[j, 'pre_close'] * adjust_rate, 4)
            k_data.loc[j, 'change'] = float_precision(k_data.loc[j, 'change'] * adjust_rate, 4)
            k_data.loc[j, 'open'] = float_precision(k_data.loc[j, 'open'] * adjust_rate, 4)
            k_data.loc[j, 'high'] = float_precision(k_data.loc[j, 'high'] * adjust_rate, 4)
            k_data.loc[j, 'low'] = float_precision(k_data.loc[j, 'low'] * adjust_rate, 4)
            k_data.loc[j, 'close'] = float_precision(k_data.loc[j, 'pre_close'] + k_data.loc[j, 'change'], 4)
            if j >= 4:
                k_data.loc[j, 'ma5'] = float_precision(k_data.loc[j, 'ma5'] * adjust_rate, 4)
            if j >= 9:
                k_data.loc[j, 'ma10'] = float_precision(k_data.loc[j, 'ma10'] * adjust_rate, 4)
            if j >= 19:
                k_data.loc[j, 'ma20'] = float_precision(k_data.loc[j, 'ma20'] * adjust_rate, 4)
            if j >= 29:
                k_data.loc[j, 'ma30'] = float_precision(k_data.loc[j, 'ma30'] * adjust_rate, 4)
            if j >= 59:
                k_data.loc[j, 'ma60'] = float_precision(k_data.loc[j, 'ma60'] * adjust_rate, 4)
            if j >= 119:
                k_data.loc[j, 'ma120'] = float_precision(k_data.loc[j, 'ma120'] * adjust_rate, 4)
            if j >= 249:
                k_data.loc[j, 'ma250'] = float_precision(k_data.loc[j, 'ma250'] * adjust_rate, 4)
        else:  # 计算新加入数据的均线值
            mas = ['5', '10', '20', '30', '60', '120', '250']
            for ma in mas:
                if k_data.loc[j, 'ma' + ma] is None and j >= int(ma):
                    k_data.loc[j, 'ma' + ma] = cal_ma(int(ma), k_data.loc[j, 'close'], k_data.loc[j - 1, 'ma' + ma],
                                                      k_data.loc[j - int(ma), 'close'])
                if k_data.loc[j, 'ma_v_' + ma] is None and j >= int(ma):
                    k_data.loc[j, 'ma_v_' + ma] = cal_ma(int(ma), k_data.loc[j, 'vol'], k_data.loc[j - 1, 'ma_v_' + ma],
                                                         k_data.loc[j - int(ma), 'vol'])


if __name__ == '__main__':
    daily_update()
    # print(1)
