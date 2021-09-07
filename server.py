# -*- coding: utf-8 -*-
import pandas as pd
from pyfiles.com_lib.tools import *
from pyfiles.backtest.back_test import BackTest
from pyfiles.data_client import DataClient, MySqlServer
from pyfiles.strategies.single_indicator import SingleIndicator
from pyfiles.com_lib.exceptions import *
from typing import List
import json
import time
import os


class Server(object):
    mysql = MySqlServer()
    data_client = DataClient()
    basic_info = BasicInfo(mysql)
    
    def k_data(self, sec_code: str, **kwargs):
        """
        :param sec_code:
        :param kwargs:
        :return: k线数据：[开盘, 收盘, 最低, 最高]
        """
        # 存储绘制k线图的数据
        kdata = dict()
        # 配置参数
        start_date = kwargs.get("start_date", '2018-01-01')
        end_date = kwargs.get("end_date", '2019-02-01')
        ma_lines = kwargs.get("ma", ['ma5', 'ma10', 'ma20', 'ma30'])
        fq = kwargs.get("fq", "D")
        # 获取并处理数据
        table_name = sec_code[:6] + '_' + fq_trans(fq)
        columns = ['trade_date', 'open', 'close', 'low', 'high', 'amount']
        columns.extend(ma_lines)
        query = "select %s from stock.%s where trade_date between '%s' and '%s';" \
                % (','.join(columns), table_name, start_date, end_date)
        data = self.mysql.query(query)
        for line in data.values:
            line[0] = to_date_str(line[0].date())
        # 设置数据格式
        kdata['kdata'] = data[['open', 'close', 'low', 'high']].values.tolist()
        kdata['date'] = data['trade_date'].values.tolist()
        kdata['volume'] = data['amount'].values.tolist()
        for ma in ma_lines:
            kdata[ma] = data[ma].values.tolist()
        #
        return kdata

    @staticmethod
    def get_profit_line():
        indicator = BackTest().back_test()
        res = dict()
        res['profit_line'] = indicator.float_profit_rate
        res['trade_date'] = indicator.trade_date
        res['basic_profit_line'] = indicator.basic_profit_rate
        res['sharpe_ratio'] = indicator.sharpe_ratio
        res['max_drawdown'] = indicator.max_drawdown_rate
        # print(res)
        return res

    def get_fina_data(self, sec_codes, **kwargs):
        start = time.clock()
        filters = kwargs.get("filters", {})
        trade_date = to_date(kwargs.get("trade_dt", '2019-12-31'))
        print("开始查询，筛选条件", filters)
        print("查询日期：%s" % to_date_str(trade_date))
        # print(filters)
        # sec_codes = ['000001.SZ', '000002.SZ']
        if filters.get("fina_indi") is not None:
            fina_data = self.data_client.get_fina_list(sec_codes=sec_codes, columns=[], year=trade_date.year,
                                                       quarter=get_quarter(trade_date), filters=filters['fina_indi'])
        else:
            fina_data = self.data_client.get_fina_list(sec_codes=sec_codes, columns=[], year=trade_date.year,
                                                       quarter=get_quarter(trade_date))
        stock_basic = self.data_client.stock_basic(list_status=None)
        stock_basic.set_index(keys='ts_code', inplace=True)
        # print(fina_data[['ts_code', 'roe']])
        fina_data['name'] = stock_basic.loc[fina_data['ts_code'], 'name'].values
        # print(stock_basic)
        if filters.get("kline") is not None:
            indicator = self.data_client.get_k_data(dt=to_date_str(trade_date), sec_codes=sec_codes,
                                                    columns=['ts_code', 'close', 'turnover_rate', 'pe', 'pb',
                                                             'total_mv', 'circ_mv'], filters=filters['kline'],
                                                    is_recur=False)
        else:
            indicator = self.data_client.get_k_data(dt=to_date_str(trade_date), sec_codes=sec_codes,
                                                    columns=['ts_code', 'close', 'turnover_rate', 'pe', 'pb',
                                                             'total_mv', 'circ_mv'], is_recur=False)
        end = time.clock()
        # print(len(fina_data['ts_code']))
        # print(len(indicator['ts_code']))
        res = pd.merge(fina_data, indicator, on='ts_code', how='inner')
        print("结果数： %d" % len(res))
        print("查询时间%s秒" % (end-start))
        # print(res[['ts_code', 'roe', 'pb']])
        return res

    def get_quant_data(self):
        """
        多空因子指标
        :return:
        """
        data = dict()
        quant_data = pd.read_csv('./data/quant.csv')
        # 当积分不足或其他情况导致无法获取数据时，从其他途径获取指数成分
        try:
            index_data = self.data_client.pro.index_daily(ts_code='399300.SZ', start_date='20201201',
                                                          end_date='20210205', fields="close")
        except Exception:
            pass
        # print(index_data)
        data['trade_date'] = quant_data['trade_date'].tolist()
        data['indicator_value'] = quant_data['value'].tolist()
        # data['index_data'] = index_data['close'].tolist()
        # print(data)
        return data

    def sec_filter(self, options: List[str]):
        # print(options)
        filters = dict()
        sec_pool_code = '399300.SZ'
        trade_dt = '2020-12-31'
        with open('./data/indicator_dict.json') as f:
            indi_dict = json.load(f)
        for option in options:
            words = option.split(' ')
            if words[0] == 'sec_pool':
                sec_pool_code = words[1]
            elif words[0] == 'trade_date':
                trade_dt = words[1]
            else:
                for key in indi_dict:
                    if indi_dict[key].get(words[0]) is not None:
                        self.add_option(key, words, filters)
                        break
        # print(filters)
        sec_pool = self.data_client.index_weight(index_code=sec_pool_code, trade_date=to_date(trade_dt))['con_code'].tolist()
        fina_data = self.get_fina_data(sec_pool, filters=filters)
        columns = fina_data.columns
        # print(fina_data)
        '''
        for key in filters:
            indicators = filters[key]
            for indicator in indicators:
                try:
                    print(columns.get_loc(indicator))
                except KeyError:
                    continue
        '''
        if len(fina_data) > 100:
            return fina_data.loc[:100]
        else:
            return fina_data

    def get_sec_pool(self, pool_list):
        sec_list = self.data_client.get_sec_pool(sec_pool='000016.SH')
        # print(sec_list['list_date'])
        return sec_list

    def backtest(self, kwargs: dict):
        print(kwargs)
        sec_pool = kwargs.get("sec_pool", dict())
        strategy = kwargs.get("stragety", None)
        start_dt = kwargs.get("start_date", None)
        end_dt = kwargs.get("end_date", None)
        first_in = kwargs.get("first_in", 100000)
        if strategy is None:
            raise ParamError("求指定回测策略")
        if strategy == 'multi_indicator':
            indicators = kwargs.get("indicators", [])
            if len(indicators) < 1:
                raise ParamError("多因子未指定指标")
        elif strategy == 'single_indicator':
            indicator = kwargs.get("indicator", None)
            if indicator is None:
                raise ParamError("单因子未指定指标")
            metrics = SingleIndicator(sec_pool=list(sec_pool.keys()), indicator=indicator,
                                      start_dt=start_dt, end_dt=end_dt, echo_info=2,
                                      max_position_num=1, first_in=first_in).back_test()
            return metrics
        else:
            raise ParamError("错误或未开发策略： %s" % strategy)

    @staticmethod
    def add_option(key: str, words: List[str], filters: dict):
        option_len = len(words)
        # print(key, words)
        if filters.get(key) is None:
            filters[key] = dict()
            filters[key][words[0]] = dict()
            filters[key][words[0]][words[1]] = words[2]
        else:
            filter_l1 = filters[key]
            if filter_l1.get(words[0]) is None:
                filter_l1[words[0]] = dict()
                filter_l1[words[0]][words[1]] = words[2]
            else:
                filter_l2 = filter_l1[words[0]]
                # print(filters)
                if filter_l2.get(words[1]) is None:
                    filter_l2[words[1]] = words[2]
                else:
                    pre_value = filter_l2[words[1]]
                    if words[1] == '>' and float(words[2]) > float(pre_value):
                        filter_l2[words[1]] = words[2]
                    if words[1] == '<' and float(words[2]) < float(pre_value):
                        filter_l2[words[1]] = words[2]


if __name__ == '__main__':
    print(os.getcwd())
    # k_data('000001.SZ')
    # 总字典
    # data_client = DataClient()
    # print(data_client.pro.index_weight(index_code='300005.SZ'))
    pass
