# -*- coding: utf-8 -*-
"""
    回测过程
"""
from pyfiles.strategies.turtle_strategy import *
from pyfiles.tools import *
from pyfiles.data_client import data_client
from pyfiles.strategies.double_ma_strategy import *
from pyfiles.strategies.single_indicator import *
import time


def back_test():
    # 初始化策略信息
    strategy = SingleIndicator(AccountInfo(), GlobalVariable())
    strategy.initialize()
    account = strategy.account
    g = strategy.g
    #
    start_date = account.run_paras["start_date"]
    end_date = account.run_paras["end_date"]
    account.metrics.set_basic_profit_rate(index_code='399005', start_date=to_date_str(start_date),
                                          end_date=to_date_str(end_date), freq='D')
    #
    current_date = start_date
    account.set_cur_dt(cur_dt=current_date)
    account.previous_dt = current_date
    #
    print("回测开始，开始时间：%s，结束时间：%s，账户总资金：%f，股池个数：%d"
          % (to_date_str(start_date), to_date_str(end_date), account.portfolio.available_cash, g.N))
    time_start = time.time()
    # 首先在设定起始日期的基础上使得当前日期以及上一日期无为交易日
    current_date, account.previous_dt = data_client.init_start_trade_date(to_date_str(start_date),
                                                                          to_date_str(end_date))
    account.current_dt = current_date
    #
    counter = 0
    while current_date.__ne__(end_date):
        # print("current date: %s, end date: %s" % (to_date_str(current_date), to_date_str(end_date)))
        if data_client.is_marketday(account.current_dt):
            strategy.before_trade_start()
            if counter % g.period == 0:
                strategy.handle_data()
            strategy.after_trade_end()
            account.daily_update()
        #
        if data_client.is_marketday(current_date):
            account.previous_dt = current_date
        current_date = current_date + datetime.timedelta(days=1)
        account.set_cur_dt(cur_dt=current_date)
        counter = counter + 1
    # print(Account.metrics.float_profit)
    print("end")
    time_end = time.time()
    print("本次回测用时:%fs" % (time_end-time_start))
    account.metrics.cal_max_drawdown()
    return account.metrics

def test():
    sec_codes = ['000001.SZ', '000002.SZ', '000004.SZ', '000005.SZ', '000006.SZ',
                 '000007.SZ', '000008.SZ', '000009.SZ', '000010.SZ', '000011.SZ']
    res = data_client.get_pe_list(date='2018-12-20', sec_codes=sec_codes, pe_type=['S', 'T'])
    print(res)
    print(res.sort_values(by='S', axis=0).index[:5].tolist())


if __name__ == '__main__':
    back_test()