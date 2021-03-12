# -*- coding: utf-8 -*-
"""
    多因子策略，动态市盈率，
        对于股池中的个股，获取相应的因子数据并排序，取其前若干支股买入，
    经过调仓周期后，重复上述过程。
        对于多因子，将各个多因子按加权或打分的形势为每支股算出分数，
    取分数排名前若干股买入，经过调仓周期后，重复上述过程。
        因子权重或分数可以使用机器学习算法。
        之后还需要删除无用因子

    当前问题:
        交易记录中显示两次
        年报获取问题
"""
from pyfiles.utils import *
from pyfiles.api import *
import six


class SingleIndicator(Strategy):

    def __init__(self, **kwargs):
        super().__init__(kwargs)
        self.data_client = DataClient()
        # 初始化账户
        self.account = AccountInfo(data_client=self.data_client)
        # 初始化全局变量
        self.g = GlobalVariable()
        # 设置参数
        self.kwargs = kwargs
        self.backtest_params = dict()
        # 初始化策略
        self.initialize()

    def set_params(self):
        # 股池，待选
        sec_pool = self.kwargs.get("sec_pool", '399300.SZ')
        if isinstance(sec_pool, six.string_types) and sec_pool in self.data_client.index_basic()['ts_code'].tolist():
            self.g.sec_pool = self.data_client.pro.index_weight(
                index_code=sec_pool, trade_date=to_date_str(self.account.current_date, split=''))['con_code'].tolist()
        elif isinstance(sec_pool, list):
            self.g.sec_pool = sec_pool
        else:
            raise ParamError("sec_pool error")
        # self.g.sec_pool = ['000001.SZ', '000002.SZ', '000004.SZ', '000005.SZ', '000006.SZ',
        #                    '000007.SZ', '000008.SZ', '000009.SZ', '000010.SZ', '000011.SZ']
        self.g.N = min(self.kwargs.get("max_position_num", 5), len(self.g.sec_pool))  # 持仓个数
        self.g.indicator = self.kwargs.get("indicator", None)
        # 调仓周期，限调用handle_data函数的间隔
        self.g.period = self.kwargs.get("period", 20)
        # 回测过程中的参数
        self.backtest_params['echo_info'] = self.kwargs.get("echo_info", 1)

    def set_variables(self):
        # 设置基准指数
        self.account.metrics.set_basic_profit_rate(index_code='399300.SZ',
                                                   start_dt=to_date_str(self.account.run_paras['start_date']),
                                                   end_dt=to_date_str(self.account.run_paras['end_date']),
                                                   freq='D', data_client=self.data_client)
        return

    def set_backtest(self):
        return

    def before_trade_start(self):
        return

    def handle_data(self):
        previous_date = self.account.previous_date
        current_date = self.account.current_date
        # 卖出所有持仓
        self.account.clear_position(echo_info=self.backtest_params['echo_info'])
        # 获取pe数据
        # indicator_df = self.data_client.get_pe_list(dt=to_date_str(previous_date), sec_codes=self.g.sec_pool,
        #                                        pe_type=['S', 'T'])
        indicator_df = self.data_client.get_fina_list(sec_codes=self.g.sec_pool, columns=[self.g.indicator],
                                                      end_dt=to_date_str(self.account.current_date)).set_index('ts_code')
        # 升序排序
        # print(indicator_df)
        indicator_df.sort_values(by=self.g.indicator, axis=0, inplace=True)
        # 买入个股
        target = indicator_df.index[:min(self.g.N, len(indicator_df))].tolist()
        # print(target)
        for sec_code in target:
            if self.data_client.is_trade(sec_code=sec_code, dt=to_date_str(current_date)):
                price = self.data_client.get_price(dt=to_date_str(current_date), sec_code=sec_code, price_type='open',
                                                   not_exist='last')
                position = self.account.has_position(sec_code=sec_code)
                if position is None:
                    cash = self.account.portfolio.inout_cash
                else:
                    cash = position.available_cash
                order(account=self.account, g=self.g, sec_code=sec_code, price=price,
                      amount=cal_stock_amount(price=price, cash=cash), side='B',
                      echo_info=self.backtest_params['echo_info'])
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
        adjust_dt = self.account.current_date
        # 股池中各支股票在调仓日的收盘价
        prices = self.data_client.get_price_list(to_date_str(adjust_dt), self.g.sec_pool, 'open')
        # 获取各个股票在调仓日3种市盈率对应的3种EPS
