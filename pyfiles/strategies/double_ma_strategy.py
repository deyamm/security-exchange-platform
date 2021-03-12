# -*- coding: utf-8 -*-
"""
    双均线策略，选定两条均线，当短期均线上穿长期均线时买入，下穿时卖出
"""
from pyfiles.utils import *
import math
from pyfiles.api import *


class DoubleMAStrategy(Strategy):

    def __init__(self, kwargs):
        super().__init__(kwargs=kwargs)
        # 对应两条均线对应
        self.data_client = DataClient()
        self.account = AccountInfo(data_client=self.data_client)
        self.g = GlobalVariable()
        self.short_ma_day = 5
        self.long_ma_day = 10

    def set_params(self):
        # 股池
        self.g.sec_pool = ['000001.SZ']
        # 股池中个股数量
        self.g.N = 1
        self.g.period = 1

    def set_variables(self):
        # 设置基准指数
        self.account.metrics.set_basic_profit_rate(index_code='399005',
                                                   start_dt=to_date_str(self.account.run_paras['start_date']),
                                                   end_dt=to_date_str(self.account.run_paras['end_date']),
                                                   freq='D')
        return

    def set_backtest(self):
        return

    def before_trade_start(self):
        return

    def handle_data(self):
        for sec_code in self.g.sec_pool:
            if self.data_client.is_trade(sec_code=sec_code, dt=to_date_str(self.account.current_date)):
                short_ma = self.data_client.get_ma(days=self.short_ma_day, dt=to_date_str(self.account.previous_date),
                                                   sec_code=sec_code, fq='D')
                long_ma = self.data_client.get_ma(days=self.long_ma_day, dt=to_date_str(self.account.previous_date),
                                                  sec_code=sec_code, fq='D')
                operate_price = self.data_client.get_price(dt=to_date_str(self.account.current_date), sec_code=sec_code,
                                                           price_type='open', not_exist='last')
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
