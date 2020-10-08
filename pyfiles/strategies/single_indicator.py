# -*- coding: utf-8 -*-
"""
    多因子策略，动态市盈率，4个滚动季度的盈利/当日的总市值，
        对于股池中的个股，获取相应的因子数据并排序，取其前若干支股买入，
    经过调仓周期后，重复上述过程。
        对于多因子，将各个多因子按加权或打分的形势为每支股算出分数，
    取分数排名前若干股买入，经过调仓周期后，重复上述过程。
        因子权重或分数可以使用机器学习算法。
        之后还需要删除
"""
from pyfiles.utils import *
from pyfiles.api import *

class SingleIndicator(Strategy):
    account = None
    g = None

    def __init__(self, account: AccountInfo, g: GlobalVariable):
        super().__init__()
        self.account = account
        self.g = g

    def initialize(self):
        # 设置回测范围
        self.account.set_paras(start_date='2012-01-01', end_date='2019-02-01')
        # 资金账户
        self.account.portfolio = Portfolio(100000)
        # 指标
        self.account.metrics = Metrics(self.account.portfolio.inout_cash, 0)
        self.set_params()

    def set_params(self):
        self.g.N = 5  # 持仓个数
        # 股池，待选
        self.g.context = ['000001.SZ', '000002.SZ', '000004.SZ', '000005.SZ', '000006.SZ',
                          '000007.SZ', '000008.SZ', '000009.SZ', '000010.SZ', '000011.SZ']
        self.g.indicator = 'pe'
        # 调仓周期，限调用handle_data函数的间隔
        self.g.period = 15

    def set_variables(self):
        return

    def set_backtest(self):
        return

    def before_trade_start(self):
        return

    def handle_data(self):
        previous_dt = self.account.previous_dt
        current_dt = self.account.current_dt
        # 卖出所有持仓
        self.account.clear_position()
        # 获取pe数据
        indicator_df = data_client.get_pe_list(date=to_date_str(previous_dt), sec_codes=self.g.context,
                                               pe_type=['S', 'T'])
        # 升序排序
        indicator_df.sort_values(by='S', axis=0, inplace=True)
        # 买入个股
        target = indicator_df.index[:self.g.N].tolist()
        for sec_code in target:
            price = data_client.get_price(date=to_date_str(current_dt), sec_code=sec_code, price_type='open')
            order(account=self.account, g=self.g, sec_code=sec_code, price=price, amount=1000, side='B')
        return

    def after_trade_end(self):
        return

    def sort_indicator(self):
        """
        获取股池中各个股票的指标，并将其按特定方式排序
        该例中以市盈率pe为指标，首先需要获取调仓日的股票价格，
        之后获取该股的每股收益EPS，市盈率分为静态市盈率和动态市盈率以及滚动市盈率（TTM），
        静态市盈率为去年EPS，动态市盈率则为预估的今年EPS，滚动市盈率则为过去12个月的EPS，
        该例将3种市盈率都计算出并比较效果
        :return:
        """
        adjust_dt = self.account.current_dt
        # 股池中各支股票在调仓日的收盘价
        prices = data_client.get_price_list(to_date_str(adjust_dt), g.context, 'open')
        # 获取各个股票在调仓日3种市盈率对应的3种EPS

        return