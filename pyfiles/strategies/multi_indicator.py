# -*- coding: utf-8 -*-
"""
    多因子线性回归
    核心问题是将各个指标数据标准化
    参考 https://www.joinquant.com/view/community/detail/89faa112f17f5d14f17e4df1fd82c0b6
    多因子策略
    选中因子：eps(每股收益), roa(总资产报酬率), profit_dedt(扣非净利润), roe(净资产收益率),
            roe_dt(扣非净资产收益率), op_of_gr(营业利润/营业总收入), netfrofit_margin(销售净利率),
            grossprofit_margin(销售毛利率), adminexp_of_gr(管理费用/营业总收入),
            salescash_to_gr(销售商品提供劳务收到的现金/营业收入), tr_yoy(营业总收入同比增长率)
    1. 删除冗余因子，通过计算两两之间的相关系数，在某个范围内的需要删除
    2. 实现策略
"""
from pyfiles.backtest.api import *
import pandas as pd
from pyfiles.models import apt


class MultiIndicator(Strategy):

    def __init__(self, **kwargs):
        super().__init__(kwargs=kwargs)
        self.data_client = DataClient()
        self.account = AccountInfo(data_client=self.data_client)
        self.g = GlobalVariable()
        self.model = None
        self.kwargs = kwargs
        self.initialize()

    def set_params(self):
        self.g.N = 5
        self.g.sec_pool = self.kwargs.get("sec_pool", [])
        self.g.period = 30
        """
        eps(每股收益), roa(总资产报酬率), profit_dedt(扣非净利润), roe(净资产收益率),
            roe_dt(扣非净资产收益率), op_of_gr(营业利润/营业总收入), netfrofit_margin(销售净利率),
            grossprofit_margin(销售毛利率), adminexp_of_gr(管理费用/营业总收入),
            salescash_to_gr(销售商品提供劳务收到的现金/营业收入), tr_yoy(营业总收入同比增长率)
        """
        self.g.indicators = self.kwargs.get("indicators", [])
        self.g.start_dt = self.kwargs.get("start_dt", '2016-01-01')
        self.g.end_dt = self.kwargs.get("end_dt", '2021-01-01')
        self.model = apt.APT(sec_pool=self.g.sec_pool, indicators=self.g.indicators,
                             start_dt=self.g.start_dt, end_dt=self.g.end_dt)

    def set_variables(self):
        # 设置基准指数
        self.account.metrics.set_basic_profit_rate(index_code='399005',
                                                   start_dt=to_date_str(self.account.run_paras['start_date']),
                                                   end_dt=to_date_str(self.account.run_paras['end_date']),
                                                   freq='D')
        return

    def set_backtest(self):
        retur

    def before_trade_start(self):
        return

    def handle_data(self):
        # 设置日期，用前一天的数据计算指标，用当天开盘价进行交易
        previous_date = self.account.previous_date
        current_date = self.account.current_date
        # 清仓
        self.account.clear_position()
        # 从备选股池中选出市净率小的N只股票作为目标交买入
        # fina_list = self.data_client.get_fina_list(sec_codes=self.g.sec_pool, )

    def after_trade_end(self):
        return

    def handle_indicator(self):
        pass

    def set_right(self, indicator_df: pd.DataFrame):
        return
