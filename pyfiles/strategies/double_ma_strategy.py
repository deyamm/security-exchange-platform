# -*- coding: utf-8 -*-
"""
    双均线策略，选定两条均线，当短期均线上穿长期均线时买入，下穿时卖出
"""
from pyfiles.utils import *
import math
from pyfiles.api import *


class DoubleMAStrategy(Strategy):
    account = None
    g = None

    def __init__(self, account: AccountInfo, g: GlobalVariable):
        super().__init__()
        self.account = account
        self.g = g
        # 对应两条均线对应
        self.short_ma_day = 5
        self.long_ma_day = 10

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

    def set_params(self):
        # 股池
        self.g.context = ['000001.SZ']
        # 股池中个股数量
        self.g.N = 1

    def set_variables(self):
        return

    def set_backtest(self):
        return

    def before_trade_start(self):
        return

    def handle_data(self):
        for sec_code in self.g.context:
            if data_client.is_trade(code=sec_code, date=to_date_str(self.account.current_dt)):
                short_ma = data_client.get_ma(days=self.short_ma_day, date=to_date_str(self.account.previous_dt),
                                              sec_code=sec_code, fq='D')
                long_ma = data_client.get_ma(days=self.long_ma_day, date=to_date_str(self.account.previous_dt),
                                             sec_code=sec_code, fq='D')
                operate_price = data_client.get_price(date=to_date_str(self.account.current_dt), sec_code=sec_code,
                                                      price_type='open')
                # 买入
                if short_ma > long_ma:
                    position = self.account.has_position(sec_code)
                    # 如果无该持仓
                    if position is None:
                        amount = math.floor(self.account.portfolio.inout_cash
                                            / (self.g.N * operate_price * 100)) * 100
                    else:  # 如果有该持仓
                        amount = math.floor(position.available_cash
                                            / (operate_price * 100)) * 100
                    if amount > 0:
                        order(self.account, self.g, sec_code, operate_price, amount, 'B')
                # 卖出
                if short_ma < long_ma:
                    order(self.account, self.g, sec_code, operate_price, self.account.get_sec_amount(sec_code), 'S')
            else:
                continue

    def after_trade_end(self):
        return
