# -*- coding: utf-8 -*-
"""
    因子有效性检验，检验方法有：
    1. 因子IC值检验
        IC（information coefficient）即信息系数，代表预测值和实现值之间的相关性，
        分为normal IC和rank IC，
            normal IC求法为t期因子值与t+1期收益的相关系数，但有数据服从正态分布的前提
            rank IC在求相关系数时，采用秩相关系数，即t期因子值的排序值与t+1期因子收益的排序值之间的相关系数
    2. 回归法检验
    3. 分层法检验
    4. 因子的逻辑性及普适性检验


    问题：获取指数成分的日期
"""
import traceback
from typing import List
from pyfiles.data_client import DataClient
from pyfiles.exceptions import *
from pyfiles.strategies.single_indicator import SingleIndicator
from pyfiles.tools import *
from pyfiles.utils import *
import six
import datetime
import time
from multiprocessing import Process, Pool, Manager


class ValidationCheck(object):
    sec_pool = None
    indicator = None
    start_date: datetime.date = None
    end_date: datetime.date = None
    data_client = None

    def __init__(self, indicator: str, sec_pool: str or List[str], **kwargs):
        self.indicator = indicator
        self.data_client = DataClient()
        #
        self.year = kwargs.get("year", 2019)
        self.quarter = kwargs.get("quarter", 1)
        #
        self.end_date = to_date(kwargs.get("end_date", datetime.datetime.now().date()))
        self.start_date = to_date(kwargs.get("start_date", datetime.date(self.year, 1, 1)))
        # 调仓周期
        self.period = kwargs.get("period", 20)
        # 回测的天数
        self.test_days = kwargs.get("test_days", 20)
        if isinstance(sec_pool, six.string_types) and sec_pool in self.data_client.index_basic()['ts_code'].tolist():
            self.sec_pool = self.data_client.index_weight(
                index_code=sec_pool, trade_date=self.start_date)['con_code'].tolist()
        elif isinstance(sec_pool, list):
            self.sec_pool = sec_pool
        else:
            raise ParamError("sec_pool error")
        # print(self.sec_pool)

    def ic_value_check(self, value_type: str = 'rank', parallel: bool = False, **kwargs):
        # 回测的天数
        test_days = kwargs.get("test_days", self.test_days)
        if value_type == 'rank':
            # 获取因子排序值
            fina_data = self.data_client.get_fina_list(sec_codes=self.sec_pool, columns=[self.indicator],
                                                       year=self.year, quarter=self.quarter)
            # print(fina_data)
            # 如果指标是按递增顺序排序，则需要将正值与负值分开排序再合并
            # fina_date_pos = fina_data[fina_data[self.indicator] >= 0].sort_values(by=self.indicator)
            # fina_data_neg = fina_data[fina_data[self.indicator] < 0].sort_values(by=self.indicator, ascending=False)
            # fina_data = pd.concat([fina_date_pos, fina_data_neg])
            fina_data.sort_values(by=self.indicator, ascending=False, inplace=True)
            fina_data.set_index('ts_code', inplace=True)
            fina_data['indicator_rank'] = range(len(fina_data))
            dt_range = self.data_client.get_fina_date_range(sec_codes=self.sec_pool, year=self.year, quarter=self.quarter)
            # 调用回测函数获取收益率
            #
            time_start = time.time()
            # 由于每支股票的报告日期不同，所以应该确定对各自的回测日期范围，根据季度来
            if parallel is False:
                for sec_code in self.sec_pool:
                    profit_rate = SingleIndicator(start_dt=dt_range.loc[sec_code, 'start_date'],
                                                  end_dt=dt_range.loc[sec_code, 'end_date'], sec_pool=[sec_code],
                                                  indicator=self.indicator).back_test().period_profit_rate()
                    fina_data.loc[sec_code, 'profit_rate'] = profit_rate
            else:
                res_queue = Manager().Queue()
                pro_pool = Pool(10)
                # couter = 0
                for sec_code in self.sec_pool:
                    # print(sec_code)
                    pro_pool.apply_async(cal_profit_rate,
                                         (dt_range.loc[sec_code, 'start_date'], dt_range.loc[sec_code, 'end_date'],
                                          [sec_code], self.indicator, res_queue,), error_callback=call_back)
                pro_pool.close()
                pro_pool.join()
                print('有效数据个数 ' + str(res_queue.qsize()))
                while res_queue.qsize() > 0:
                    res = res_queue.get()
                    fina_data.loc[res[0], 'profit_rate'] = res[1]
            #
            # print(fina_data)
            time_end = time.time()
            fina_data.sort_values(by='profit_rate', ascending=False, inplace=True)
            fina_data['profit_rate_rank'] = range(len(fina_data))
            if parallel:
                t = 'p_'
            else:
                t = 'np_'
            fina_data.to_csv('../../logs/' + t + 'res.csv')
            print("本次ic值计算用时%fs" % (time_end-time_start))
            # print(fina_data)
            return fina_data['indicator_rank'].corr(fina_data['profit_rate_rank'])
        elif value_type == 'normal':
            fina_data = self.data_client.get_fina_list(sec_codes=self.sec_pool, columns=[self.indicator],
                                                       year=self.year, quarter=self.quarter)
            # print(fina_data)
            # 如果指标是按递增顺序排序，则需要将正值与负值分开排序再合并
            # fina_date_pos = fina_data[fina_data[self.indicator] >= 0].sort_values(by=self.indicator)
            # fina_data_neg = fina_data[fina_data[self.indicator] < 0].sort_values(by=self.indicator, ascending=False)
            # fina_data = pd.concat([fina_date_pos, fina_data_neg])
            fina_data.set_index('ts_code', inplace=True)
            dt_range = self.data_client.get_fina_date_range(sec_codes=self.sec_pool,
                                                            year=self.year, quarter=self.quarter)
            time_start = time.time()
            if parallel is False:
                for sec_code in self.sec_pool:
                    profit_rate = SingleIndicator(start_dt=dt_range.loc[sec_code, 'start_date'],
                                                  end_dt=dt_range.loc[sec_code, 'end_date'], sec_pool=[sec_code],
                                                  indicator=self.indicator).back_test().period_profit_rate()
                    fina_data.loc[sec_code, 'profit_rate'] = profit_rate
            else:
                res_queue = Manager().Queue()
                pro_pool = Pool(10)
                for sec_code in self.sec_pool:
                    pro_pool.apply_async(cal_profit_rate, (dt_range.loc[sec_code, 'start_date'],
                                                           dt_range.loc[sec_code, 'end_date'], [sec_code],
                                                           self.indicator, res_queue, ), error_callback=call_back)
                pro_pool.close()
                pro_pool.join()
                print("有效数据个数 " + str(res_queue.qsize()))
                while res_queue.qsize() > 0:
                    res = res_queue.get()
                    fina_data.loc[res[0], 'profit_rate'] = res[1]
            time_end = time.time()
            print("本次ic值计算用时%fs" % (time_end-time_start))
            return fina_data[self.indicator].corr(fina_data['profit_rate'])
        else:
            raise ParamError("ic type error(rank/normal)")


def cal_profit_rate(start_dt: str, end_dt: str, sec_pool: List[str], indicator: str, q):
    # print("start" + ','.join(sec_pool))
    rate = SingleIndicator(start_dt=start_dt, end_dt=end_dt, sec_pool=sec_pool, indicator=indicator)\
        .back_test().period_profit_rate()
    # print("end" + ','.join(sec_pool))
    q.put([sec_pool[0], rate])


def call_back(value):
    print(value)


if __name__ == '__main__':
    ic_value = ValidationCheck(indicator='roe', sec_pool='399300.SZ',
                               year=2019, quarter=2).ic_value_check(value_type='rank', parallel=True)
    print("ic_value: %f" % ic_value)