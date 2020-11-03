# -*- coding: utf-8 -*-
"""
    编写策略，以海龟策略为例，将总资金分为指定份数，该数为股池中个股数量
    每天开盘后，如果前一天的收盘价高于前一天的20天均线，则将一份资金全部买入该股
    如果前一天收盘价低于前一天20天均线，则将该股全部卖出。
"""
from pyfiles.api import *
from pyfiles.data_client import DataClient
# from pyfiles.utils import *
import math


# 策略初始化
class TurtleStrategy(Strategy):

    def __init__(self, **kwargs):
        super().__init__(kwargs=kwargs)
        self.data_client = DataClient()
        self.account = AccountInfo(data_client=self.data_client)
        self.g = GlobalVariable()

    # 设置策略参数
    def set_params(self):
        self.g.sec_pool = ['000001.SZ', '000002.SZ', '000006.SZ', '000007.SZ', '000009.SZ']  # 股票池
        # self.g.context = ['000006.SZ']
        # self.g.tc = 15  # 调仓频率
        self.g.N = 5  # 股池数目
        # self.g.N = 1
        self.g.benchmark_days = 20
        self.g.period = 1

    # 设置中间变量
    def set_variables(self):
        # 设置基准指数
        self.account.metrics.set_basic_profit_rate(index_code='399005',
                                                   start_dt=to_date_str(self.account.run_paras['start_date']),
                                                   end_dt=to_date_str(self.account.run_paras['end_date']),
                                                   freq='D')
        return

    # 设置回测条件
    def set_backtest(self):
        return

    # 开盘前处理的内容
    def before_trade_start(self):
        # print("before trading")
        return

    def handle_data(self):
        # print("handle data")
        for sec_code in self.g.sec_pool:
            if self.data_client.is_trade(sec_code=sec_code, dt=to_date_str(self.account.current_date)):
                ma = self.data_client.get_ma(self.g.benchmark_days, to_date_str(self.account.previous_date), sec_code, 'D')
                price = self.data_client.get_price(to_date_str(self.account.previous_date), sec_code, 'close')
                operate_price = self.data_client.get_price(to_date_str(self.account.current_date), sec_code, 'open')
                # print("证券代码：%s, 当前价格：%f， 前一天20天均线：%f。" % (code, price, ma))
                # 买入
                if price > ma:
                    position = self.account.has_position(sec_code)
                    if position is None:  # 如果无该持仓
                        trade_amount = cal_stock_amount(operate_price, self.account.portfolio.inout_cash / self.g.N)
                    else:  # 如果有该持仓
                        trade_amount = cal_stock_amount(operate_price, position.available_cash)
                    if trade_amount > 0:
                        order(self.account, self.g, sec_code, operate_price, trade_amount, 'B')
                # 卖出
                if price < ma:
                    order(self.account, self.g, sec_code, operate_price, self.account.get_sec_amount(sec_code), 'S')
            else:
                continue

    def after_trade_end(self):
        # print("after trading")
        return
