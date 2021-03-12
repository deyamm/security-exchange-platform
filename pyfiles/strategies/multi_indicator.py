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
from pyfiles.utils import *
from pyfiles.api import *
import pandas as pd
from pyfiles.models import apt


class MultiIndicator(Strategy):

    def __init__(self, **kwargs):
        super().__init__(kwargs=kwargs)
        self.data_client = DataClient()
        self.account = AccountInfo(data_client=self.data_client)
        self.g = GlobalVariable()
        self.model = None

    def set_params(self):
        self.g.N = 5
        self.g.sec_pool = ['000001.SZ', '000002.SZ', '000004.SZ', '000005.SZ', '000006.SZ',
                           '000007.SZ', '000008.SZ', '000009.SZ', '000010.SZ', '000011.SZ']
        self.g.period = 30
        """
        eps(每股收益), roa(总资产报酬率), profit_dedt(扣非净利润), roe(净资产收益率),
            roe_dt(扣非净资产收益率), op_of_gr(营业利润/营业总收入), netfrofit_margin(销售净利率),
            grossprofit_margin(销售毛利率), adminexp_of_gr(管理费用/营业总收入),
            salescash_to_gr(销售商品提供劳务收到的现金/营业收入), tr_yoy(营业总收入同比增长率)
        """
        self.g.indicator = ['end_date', 'eps', 'roa', 'profit_dedt', 'roe', 'roe_dt', 'op_of_gr',
                            'netfrofit_margin', 'grossprofit_margin', 'adminexp_of_gr',
                            'salescash_to_gr', 'tr_yoy']
        self.model = apt.APT()
        self.model.regression()

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
        # 设置日期，用前一天的数据计算指标，用当天开盘价进行交易
        previous_date = self.account.previous_date
        current_date = self.account.current_date
        # 清仓
        self.account.clear_position()
        # 从备选股池中选出市净率小的N只股票作为目标交买入
        ps_df = self.data_client.get_ps_list(dt=to_date_str(previous_date), sec_codes=self.g.sec_pool)
        ps_df.sort_values(by='ps', axis=0, inplace=True)
        target = ps_df.index[:self.g.N].tolist()
        for sec_code in target:
            price = self.data_client.get_price(dt=to_date_str(current_date), sec_code=sec_code, price_type='open')
            order(account=self.account, g=self.g, sec_code=sec_code, price=price, amount=1000, side='B')

    def after_trade_end(self):
        return

    def handle_indicator(self):
        indicator_df = pd.DataFrame(self.g.sec_pool, columns=['sec_code'])
        indicator_df.set_index('sec_code', inplace=True)
        ps_df = self.data_client.get_ps_list(dt=to_date_str(self.account.previous_date), sec_codes=self.g.sec_pool)
        pe_df = self.data_client.get_pe_list(dt=to_date_str(self.account.previous_date), sec_codes=self.g.sec_pool,
                                             pe_type=['T'])
        indicator_df = indicator_df.merge(ps_df, left_index=True, right_index=True, how='left')
        indicator_df = indicator_df.merge(pe_df, left_index=True, right_index=True, how='left')
        self.set_right(indicator_df)

    def set_right(self, indicator_df: pd.DataFrame):
        return
