# -*- coding: utf-8 -*-
import pandas as pd
from pyfiles.com_lib import *
from pyfiles.backtest.back_test import BackTest
from pyfiles.data_client import DataClient, MySqlServer
from pyfiles.strategies.single_indicator import SingleIndicator
from typing import List
from opendatatools import swindex
import json
import time
import os


class Server(object):
    mysql = MySqlServer()
    data_client = DataClient()
    basic_info = BasicInfo(mysql)

    def k_data(self, sec_code: str, **kwargs):
        """
        获取指定证券的k线数据，
        作为可选参数，可以指定开始日期、结束日期、均线、行情数据频率
        :param sec_code: 目标证券代码
        :param kwargs: 可选参数
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
        """
        以默认的设置进行回测并获取结束
        :return: dict，包括收益率曲线、交易日期、基准收益率曲线、夏普比率、最大回测
        """
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
        """
        根据筛选条件，从所给证券列表中符合筛选条件的行情数据
        :param sec_codes: 所提供的证券列表
        :param kwargs: 可选参数，包括筛选条件、交易日期，筛选条件可以为空
        :return: 符合筛选条件的证券行情数据
        """
        start = time.clock()
        filters = kwargs.get("filters", {})
        trade_date = to_date(kwargs.get("trade_dt", '2019-12-31'))
        print("开始查询，筛选条件", filters)
        print("查询日期：%s" % to_date_str(trade_date))
        # print(filters)
        # sec_codes = ['000001.SZ', '000002.SZ']
        # 根据财务筛选条件获取财务数据
        if filters.get("fina_attr") is not None:
            fina_data = self.data_client.get_fina_list(sec_codes=sec_codes, columns=[], year=trade_date.year,
                                                       quarter=get_quarter(trade_date), filters=filters['fina_attr'])
        else:
            fina_data = self.data_client.get_fina_list(sec_codes=sec_codes, columns=[], year=trade_date.year,
                                                       quarter=get_quarter(trade_date))
        # 获取证券名称
        stock_basic = self.data_client.stock_basic(list_status=None)
        stock_basic.set_index(keys='ts_code', inplace=True)
        # print(fina_data[['ts_code', 'roe']])
        fina_data['name'] = stock_basic.loc[fina_data['ts_code'], 'name'].values
        # print(stock_basic)
        # 获取符合条件的行情数据
        if filters.get("kline_attr") is not None:
            indicator = self.data_client.get_k_data(dt=to_date_str(trade_date), sec_codes=sec_codes,
                                                    columns=['ts_code', 'close', 'turnover_rate', 'pe', 'pb',
                                                             'total_mv', 'circ_mv'], filters=filters['kline_attr'],
                                                    is_recur=False)
        else:
            indicator = self.data_client.get_k_data(dt=to_date_str(trade_date), sec_codes=sec_codes,
                                                    columns=['ts_code', 'close', 'turnover_rate', 'pe', 'pb',
                                                             'total_mv', 'circ_mv'], is_recur=False)
        end = time.clock()
        # print(len(fina_data['ts_code']))
        # print(len(indicator['ts_code']))
        # 将财务数据与行情数据搜狗拼音
        res = pd.merge(fina_data, indicator, on='ts_code', how='inner')
        # res['close'] = round(res['close'], 2)
        print("结果数： %d" % len(res))
        print("查询时间%s秒" % (end - start))
        res['close'] = round(res['close'], 2)
        # print(res[['ts_code', 'close']])
        return res

    def get_quant_data(self):
        """
        多空因子指标
        :return:
        """
        data = dict()
        quant_data = pd.read_csv(PRO_PATH + '/data/quant.csv')
        # 当积分不足或其他情况导致无法获取数据时，从其他途径获取指数成分
        quant_data.sort_values(by='trade_date', inplace=True)
        # quant_data['trade_date'] = quant_data['trade_date'].map(lambda x: chg_dt_format(x, '/', '-'))
        # quant_data[['trade_date', 'value']].to_csv(PRO_PATH + '/data/quant.csv', index=False)
        # print(quant_data)
        start_dt = to_date(quant_data.loc[0, 'trade_date'], '-').isoformat()
        end_dt = to_date(quant_data.loc[len(quant_data) - 1, 'trade_date'], '-').isoformat()
        # print(start_dt, end_dt)
        index_data = self.data_client.get_index_data(index_code='399300.SZ', columns=['close'],
                                                     start_dt=start_dt, end_dt=end_dt, freq='D')
        # print(index_data)
        data['trade_date'] = quant_data['trade_date'].tolist()
        data['indicator_value'] = quant_data['indicator_value'].tolist()
        data['index_data'] = index_data['close'].tolist()
        # print(data)
        return data

    @staticmethod
    def get_heatmap_data(is_save: bool = False):
        """
        热力图数据、散点图数据
        申万一级行业涨跌幅、换手率与交易量，
        数据格式：4or5 * n，n为申万一级行业个数，
        每个数组中[x轴(换手率),y轴(涨跌幅),面积(交易量),行业名称,(可选)]
        :param is_save:
        :return:
        """
        data = dict()
        #
        index_list, msg = swindex.get_index_list()
        days_delta = 30
        end_date = datetime.date.today()
        start_date = end_date - datetime.timedelta(days=days_delta)
        l1_industry = index_list[index_list['section_name'] == '一级行业'].set_index(keys='index_code')
        l1_codes = l1_industry.index.tolist()
        #
        data['trade_date'] = None
        data['industry'] = l1_industry['index_name'].tolist()
        data['heatmap'] = []
        data['scatter'] = []
        #
        for i in range(0, len(l1_codes)):
            kdaily, msg = swindex.get_index_daily(index_code=l1_codes[i], start_date=start_date.isoformat(),
                                                  end_date=end_date.isoformat())
            daily_indi, msg = swindex.get_index_dailyindicator(index_code=l1_codes[i], start_date=start_date.isoformat(),
                                                               end_date=end_date.isoformat(), freq='D')
            daily_data = pd.merge(left=kdaily,
                                  right=daily_indi.drop(['index_code', 'index_name', 'close', 'chg_pct', 'volume'], axis=1),
                                  on='date', how='left')
            daily_data.sort_values(by='date', inplace=True)
            daily_data.reset_index(drop=True, inplace=True)
            # 热力图纵轴索引
            daily_data['ver_range'] = [i] * len(daily_data)
            # 热力图横轴索引
            daily_data['hor_range'] = range(0, len(daily_data))
            # 单日涨跌
            daily_data[['turn_rate', 'change_pct', 'vol']] = daily_data[['turn_rate', 'change_pct', 'vol']].astype('float')
            # 累计涨跌
            daily_data['change_sum'] = round(daily_data['change_pct'].cumsum(), 2)
            if data['trade_date'] is None:
                data['trade_date'] = daily_data['date'].map(lambda x: to_date_str(x, only_date=True)).tolist()
            # data[l1_codes[i]] = dict()
            # data[l1_codes[i]]['index_name'] = l1_industry.loc[l1_codes[i], 'index_name']
            # 热力图数据
            heatmap_data = daily_data[['hor_range', 'ver_range', 'change_pct', 'change_sum']].values.tolist()
            data['heatmap'].extend(heatmap_data)
            # 散点图
            scatter_data = [daily_data.loc[len(daily_data)-1, ['turn_rate', 'change_pct', 'vol', 'index_name']].values.tolist()]
            data['scatter'].extend(scatter_data)
        if is_save:
            with open(PRO_PATH + '/data/heatmap.json', 'w') as f:
                json.dump(data, f, indent=1, ensure_ascii=False)
        return data

    def sec_filter(self, options: List[str]):
        """
        将网页中设置的筛选条件处理为可以由数据库处理的格式
        :param options: 网页中设置的筛选条件
        :return: dict
        """
        # print(options)
        filters = dict()
        sec_pool_code = '399300.SZ'
        trade_dt = '2020-12-31'
        with open('./data/attribute_dict.json') as f:
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
        sec_pool = self.data_client.index_weight(index_code=sec_pool_code, trade_date=to_date(trade_dt))[
            'con_code'].tolist()
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

    @staticmethod
    def backtest(kwargs: dict):
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
        """
        向filters参数中添加可以由数据库处理的筛选条件
        :param key: 条件类别，包括行情类、财务数据类等
        :param words: 初步处理的字符串筛选条件列表，一个words列表代表一个筛选条件
        :param filters: 处理后的筛选条件字典
        :return:
        """
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

    def search_fund(self, code, decided):
        # print(code)
        fund_basic = self.basic_info.fund_basic
        if decided is False:
            searched_list = fund_basic[fund_basic.ts_code.str.startswith(code)]
            # print(len(searched_list['ts_code']))
            return searched_list.set_index('ts_code')['name'][:20].to_dict()
        else:
            searched_fund = fund_basic[fund_basic['ts_code'] == code].fillna('null').to_dict(orient='records')[0]
            return searched_fund

    def analyse_fund(self, fund_list):
        fund_portfolio = self.data_client.get_funds_portfolio(fund_list=fund_list)
        return fund_portfolio


if __name__ == '__main__':
    print(os.getcwd())
    # k_data('000001.SZ')
    # 总字典
    # data_client = DataClient()
    # print(data_client.pro.index_weight(index_code='300005.SZ'))
    pass
