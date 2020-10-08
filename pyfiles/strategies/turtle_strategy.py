# -*- coding: utf-8 -*-
"""
    编写策略，以海龟策略为例，将总资金分为指定份数，该数为股池中个股数量
    每天开盘后，如果前一天的收盘价高于前一天的20天均线，则将一份资金全部买入该股
    如果前一天收盘价低于前一天20天均线，则将该股全部卖出。
"""
from pyfiles.api import *
from pyfiles.data_client import data_client
# from pyfiles.utils import *
import math


# 策略初始化
class TurtleStrategy(Strategy):
    account = None
    g = None

    def __init__(self, account: AccountInfo, g: GlobalVariable):
        super().__init__()
        self.account = account
        self.g = g

    def initialize(self):
        # 设置回测范围
        self.account.set_paras(start_date='2018-01-01', end_date='2019-02-01')
        # 资金账户
        self.account.portfolio = Portfolio(100000)
        # 指标
        self.account.metrics = Metrics(self.account.portfolio.inout_cash, 0)
        # 初始化设置
        self.set_params()
        self.set_variables()
        self.set_backtest()

    # 设置策略参数
    def set_params(self):
        self.g.context = ['000001.SZ', '000002.SZ', '000006.SZ', '000007.SZ', '000009.SZ']  # 股票池
        # self.g.context = ['000006.SZ']
        # self.g.tc = 15  # 调仓频率
        self.g.N = 5  # 股池数目
        # self.g.N = 1
        self.g.benchmark_days = 20

    # 设置中间变量
    def set_variables(self):
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
        for sec_code in self.g.context:
            if data_client.is_trade(code=sec_code, date=to_date_str(account.current_dt)):
                ma = data_client.get_ma(self.g.benchmark_days, to_date_str(self.account.previous_dt), sec_code, 'D')
                price = data_client.get_price(to_date_str(self.account.previous_dt), sec_code, 'close')
                operate_price = data_client.get_price(to_date_str(self.account.current_dt), sec_code, 'open')
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
