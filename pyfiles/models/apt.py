# -*- coding: utf-8 -*-
"""
    套利定价模型（APT），一项资产的价格由不同因素驱动，不同因素会有其对应的beta系数，
    即多元线性回归。
    1. 从反映不同方面的财务因子挑取部分因子
    2. 检查因子有效性
        方法：
    3. 去除冗余因子
        方法：

    问题：不同因子值的数值刻度不同，应想办法统一
"""
from pyfiles.utils import *
from pyfiles.strategies.single_indicator import SingleIndicator
from pyfiles.data_client import DataClient
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from sklearn.linear_model import LinearRegression
from multiprocessing import Pool, Manager


class APT(object):
    indicators = []

    def __init__(self, **kwargs):
        self.indicators = kwargs.get("indicators", ['eps', 'roe', 'revenue_ps', 'ebit_of_gr', 'fcff_ps'])
        self.index_code = kwargs.get("index_code", None)
        self.sec_pool = kwargs.get("sec_pool", [])
        self.start_date = to_date(kwargs.get("start_date", "2018-01-01"))
        self.end_date = to_date(kwargs.get("end_date", datetime.datetime.now().date().isoformat()))
        #
        if len(self.sec_pool) == 0 and self.index_code is not None:
            self.sec_pool = self.data_client.get_sec_pool(sec_pool=sec_pool, start_date=self.start_date)
        self.indicator_name = ['基本每股收益', '净资产收益率', '每股营业收入', '息税前利润/营业总收入', '每股企业自由现金流量']
        self.data_client = DataClient()
        self.model = LinearRegression()

    def correlation_check(self, **kwargs):
        """
        相关性分析
        :return:
        """
        quarter = kwargs.get("quarter", 1)
        year = kwargs.get("year", 2018)
        fina_data = self.data_client.get_fina_list(sec_codes=self.sec_pool, columns=self.indicators,
                                                   year=year, quarter=quarter)
        fina_data.set_index('ts_code', inplace=True)
        # print(fina_data.corr())
        corr_matrix = fina_data.corr()
        corr_fig = plt.figure()
        sns.heatmap(corr_matrix, annot=True, vmax=1, vmin=-1, cmap='Oranges')
        corr_fig.show()
        # print(fina_data)

    def data_handle(self, **kwargs):
        """
        多元线性回归，自变量为各个因子值，因变量为一段时间的收益率
        以财报为时间节点， 取当期因子值，以及该财报公布日至下期财报公布日之间的收益率作为一组观测值，
        以沪深300为股票池，获取每支股票一年4份财报的数据，共有4*300=1200组观测值
        :return:
        """
        quarter = kwargs.get("quarter", 1)
        year = kwargs.get("year", 2018)
        repo_nums = kwargs.get("repo_nums", 4)
        test_days = kwargs.get("test_days", None)
        echo_info = kwargs.get("echo_info", 1)
        data_set = pd.DataFrame()
        for i in range(repo_nums):
            indicator_df = self.data_client.get_fina_list(sec_codes=self.sec_pool, columns=self.indicators,
                                                          year=year, quarter=quarter)
            indicator_df.set_index('ts_code', inplace=True)
            # 获取该期财报至下期的日期范围
            dt_range = self.data_client.get_fina_date_range(sec_codes=self.sec_pool, quarter=quarter, year=year)
            # print(indicator_df)
            # 计算股票中各支股票在该范围内的收益率
            # res_queue = Manager().Queue()
            # pro_pool = Pool(10)
            if echo_info >= variables.ECHO_INFO_BE:
                print("apt: %d年%d季度开始" % (year, quarter))
            for sec_code in self.sec_pool:
                # print(sec_code)
                if test_days is None:
                    end_dt = dt_range.loc[sec_code, 'end_date']
                else:
                    end_dt = chg_dt(dt=dt_range.loc[sec_code, 'start_date'], days=test_days,
                                    direction='front', is_trade_day=True)
                indicator_df.loc[sec_code, 'profit_rate'] = self.data_client.get_profit_rate(
                    sec_code=sec_code, start_dt=dt_range.loc[sec_code, 'start_date'], end_dt=end_dt, is_index=False, by='price')
                # pro_pool.apply_async(cal_profit_rate, (dt_range.loc[sec_code, 'start_date'],
                #                                        end_dt, [sec_code],
                #                                        'roe', echo_info, 2, res_queue, ), error_callback=call_back)
            # pro_pool.close()
            # pro_pool.join()
            # while res_queue.qsize() > 0:
            #     res = res_queue.get()
            # 组合数据，[因子值，收益率]，在循环结束后将所有的观测值合并到一个dataframe中
            # print(indicator_df)
            data_set = data_set.append(indicator_df)
            if echo_info >= variables.ECHO_INFO_BE:
                print("apt: %d年%d季度完成" % (year, quarter))
            year, quarter = chg_quarter(year, quarter)
        # 划分训练集与测试集，调用sklearn库中的线性回归库训练
        data_set.dropna(axis=0, how='any', inplace=True)
        data_set.reset_index(inplace=True)
        data_set.to_csv("../../data/data.csv", index=False)
        # print(data_set)
        return data_set

    def regression(self, **kwargs):
        # data_set = self.data_handle()
        data_set = pd.read_csv("../../data/data.csv")
        # print(data_set)
        # 划分训练集与测试集
        split_line = int(len(data_set) * 0.8)
        train_x = data_set[self.indicators].loc[:split_line]
        test_x = data_set[self.indicators].loc[split_line:]
        train_y = data_set['profit_rate'].loc[:split_line]
        test_y = data_set['profit_rate'][split_line:]
        # print(train_x)
        # print(test_x)
        self.model.fit(train_x, train_y)
        predict_y = self.predict(test_x)
        # predict_y = self.model.predict(test_x)
        print(sum(np.abs(predict_y-test_y)) / len(predict_y))

    def predict(self, indicators: pd.DataFrame):
        if isinstance(indicators, pd.DataFrame) is False:
            print("参数类型不符合，只接受DataFrame")
        need_indicators = set(self.indicators)
        columns = set(indicators.columns.tolist())
        if need_indicators == columns.intersection(need_indicators):
            return self.model.predict(indicators[self.indicators])
        else:
            print("数据指标有缺失，可能导致结果出错")
            return None


# 多进程执行的函数
def cal_profit_rate(start_dt: str, end_dt: str, sec_pool: List[str], indicator: str, echo_info: int, rate_cal_method,
                    q):
    # print("start" + ','.join(sec_pool))
    if rate_cal_method == 1:
        rate = SingleIndicator(start_dt=start_dt, end_dt=end_dt, sec_pool=sec_pool,
                               indicator=indicator, echo_info=echo_info)\
            .back_test().period_profit_rate()
    elif rate_cal_method == 2 or rate_cal_method == 3:
        if rate_cal_method == 2:
            by = 'price'
        else:
            by = 'pct'
        rate = DataClient().get_profit_rate(sec_code=sec_pool[0], start_dt=start_dt, end_dt=end_dt, by=by)
    else:
        rate = None
        raise ParamError("rate cal method error(1/2/3)")
    # print("end" + ','.join(sec_pool))
    q.put([sec_pool[0], rate])


if __name__ == '__main__':
    APT().regression()



