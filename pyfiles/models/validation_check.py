# -*- coding: utf-8 -*-
"""
    因子有效性检验，检验方法有：
    1. 因子IC值检验
        IC（information coefficient）即信息系数，代表预测值和实现值之间的相关性，
        分为normal IC和rank IC，
            normal IC求法为t期因子值与t+1期收益的相关系数，但有数据服从正态分布的前提
            rank IC在求相关系数时，采用秩相关系数，即t期因子值的排序值与t+1期因子收益的排序值之间的相关系数
    2. 回归法检验
    3. 分层法检验
    4. 因子的逻辑性及普适性检验


"""
from pyfiles.strategies.single_indicator import SingleIndicator
from pyfiles.backtest.utils import *
from pyfiles.com_lib import variables
import datetime
import time
from multiprocessing import Pool, Manager


class ValidationCheck(object):
    sec_pool = None
    indicator = None
    start_date: datetime.date = None
    end_date: datetime.date = None
    data_client = None

    def __init__(self, indicator: str, sec_pool: str or List[str], **kwargs):
        self.indicator = indicator
        self.data_client = DataClient()
        #
        self.year = kwargs.get("year", 2019)
        self.quarter = kwargs.get("quarter", 1)
        #
        self.end_date = to_date(kwargs.get("end_date", datetime.datetime.now().date()))
        self.start_date = to_date(kwargs.get("start_date", datetime.date(self.year, 1, 1)))
        # 调仓周期
        self.period = kwargs.get("period", 20)
        # 回测的天数
        self.test_days = kwargs.get("test_days", None)
        self.sec_pool = self.data_client.get_sec_pool(sec_pool=sec_pool, start_date=self.start_date)
        # print(self.sec_pool)

    def ic_value_check(self, value_type: str = 'rank', parallel: bool = False, **kwargs):
        """
        收益率计算方法：
            1：调用加测函数
            2：通过股票价格和复权因子计算
            3：通过每天的涨跌幅
        :param value_type:
        :param parallel:
        :param kwargs:
        :return:
        """
        test_days = kwargs.get("test_days", self.test_days)
        quarter = kwargs.get("quarter", self.quarter)
        year = kwargs.get("year", self.year)
        echo_info = kwargs.get("echo_info", 1)
        save_res = kwargs.get("save_res", False)
        rate_cal_method = kwargs.get("rate_cal_method", 1)
        if value_type == 'rank':
            # 获取因子排序值
            fina_data = self.data_client.get_fina_list(sec_codes=self.sec_pool, columns=[self.indicator],
                                                       year=year, quarter=quarter)
            # print(fina_data)
            # 如果指标是按递增顺序排序，则需要将正值与负值分开排序再合并
            fina_data.set_index('ts_code', inplace=True)
            dt_range = self.data_client.get_fina_date_range(sec_codes=self.sec_pool, year=year, quarter=quarter)
            # print(dt_range.loc['603160.SH'])
            # 调用回测函数获取收益率
            #
            time_start = time.time()
            # 由于每支股票的报告日期不同，所以应该确定对各自的回测日期范围，根据季度来
            self.cal_profit_rates(fina_data=fina_data, dt_range=dt_range, parallel=parallel,
                                  test_days=test_days, rate_cal_method=rate_cal_method)
            #
            # print(fina_data)
            time_end = time.time()
            # *** 注意可能需要对结果进行数据处理，剔除无效值等
            # 删去带有Nan值的行
            fina_data.dropna(axis=0, how='any', inplace=True)
            # 对指标值和收益率分别排序
            fina_data = self.sort_indicator(fina_data, partition=False)
            fina_data['indicator_rank'] = range(len(fina_data))
            fina_data.sort_values(by='profit_rate', ascending=False, inplace=True)
            fina_data['profit_rate_rank'] = range(len(fina_data))
            # print(fina_data[['profit_rate', 'profit_rate_rank']])
            # 将结果存入文件
            if parallel:
                t = 'p_'
            else:
                t = 'np_'
            if save_res is True:
                fina_data[[self.indicator, 'profit_rate']].to_csv('../logs/res3.csv')
            if echo_info >= variables.ECHO_INFO_BE:
                print("本次ic值计算用时%fs" % (time_end-time_start))
            # print(fina_data)
            return fina_data['indicator_rank'].corr(fina_data['profit_rate_rank'])
        elif value_type == 'normal':
            fina_data = self.data_client.get_fina_list(sec_codes=self.sec_pool, columns=[self.indicator],
                                                       year=year, quarter=quarter)
            # print(fina_data)
            fina_data.set_index('ts_code', inplace=True)
            dt_range = self.data_client.get_fina_date_range(sec_codes=self.sec_pool,
                                                            year=year, quarter=quarter)
            time_start = time.time()
            self.cal_profit_rates(fina_data=fina_data, dt_range=dt_range, parallel=parallel,
                                  test_days=test_days, rate_cal_method=rate_cal_method)
            time_end = time.time()
            if echo_info >= variables.ECHO_INFO_BE:
                print("本次ic值计算用时%fs" % (time_end-time_start))
            if save_res is True:
                fina_data[[self.indicator, 'profit_rate']].to_csv('../logs/res3.csv')
            return fina_data[self.indicator].corr(fina_data['profit_rate'])
        else:
            raise ParamError("ic type error(rank/normal)")

    def ir_value_check(self, value_type: str = 'rank', parallel: bool = False, test_periods: int = 5, **kwargs):
        """
        求因子的IR值，信息比率，是超额收益的均值与标准差之比，IR=IC的多周期均值/IC的标准差
        :param test_periods: 周期数，每一周期为一个财报季
        :param value_type:
        :param parallel:
        :param kwargs:
        :return:
        """
        test_days = kwargs.get("test_days", self.test_days)
        quarter = kwargs.get("quarter", self.quarter)
        year = kwargs.get("year", self.year)
        echo_info = kwargs.get("echo_info", 1)
        ic_values = []
        for i in range(test_periods):
            ic = self.ic_value_check(value_type=value_type, parallel=parallel, year=year, quarter=quarter,
                                     test_days=test_days, echo_info=echo_info)
            ic_values.append(ic)
            if quarter == 4:
                quarter = 1
                year = year + 1
            else:
                quarter = quarter + 1
        # 计算多周期ic值的均值及标准差, np.mean与np.std返回的是numpy.float64类型，根据情况可以更改为float类型
        ic_avg = float(np.mean(ic_values))
        ic_std = float(np.std(ic_values, ddof=1))
        return float_precision(ic_avg/ic_std, 2)

    def cal_profit_rates(self, fina_data, dt_range, rate_cal_method=1, **kwargs):
        echo_info = kwargs.get("echo_info", 1)
        parallel = kwargs.get("parallel", False)
        test_days = kwargs.get("test_days", None)
        if parallel is False:
            for sec_code in self.sec_pool:
                # 获取结束日期，分为指定回测天数与不指定回测天数
                if test_days is None:
                    end_dt = dt_range.loc[sec_code, 'end_date']
                else:
                    end_dt = chg_dt(dt=dt_range.loc[sec_code, 'start_date'], days=test_days,
                                    direction='front', is_trade_day=True)
                if rate_cal_method == 1:
                    profit_rate = SingleIndicator(start_dt=dt_range.loc[sec_code, 'start_date'],
                                                  end_dt=end_dt, sec_pool=[sec_code], echo_info=echo_info,
                                                  indicator=self.indicator).back_test().period_profit_rate()
                    fina_data.loc[sec_code, 'profit_rate'] = profit_rate
                elif rate_cal_method == 2 or rate_cal_method == 3:
                    if rate_cal_method == 2:
                        by = 'price'
                    else:
                        by = 'pct'
                    fina_data.loc[sec_code, 'profit_rate'] = self.data_client.get_profit_rate(
                        sec_code=sec_code, start_dt=dt_range.loc[sec_code, 'start_date'], end_dt=end_dt,
                        is_index=False, by=by)
                else:
                    fina_data.loc[sec_code, 'profit_rate'] = None
                    raise ParamError("price cal method error(1/2/3)")
        else:
            res_queue = Manager().Queue()
            pro_pool = Pool(10)
            for sec_code in self.sec_pool:
                # 获取结束日期，分为指定回测天数与不指定回测天数
                if test_days is None:
                    end_dt = dt_range.loc[sec_code, 'end_date']
                else:
                    end_dt = chg_dt(dt=dt_range.loc[sec_code, 'start_date'], days=test_days,
                                    direction='front', is_trade_day=True)
                pro_pool.apply_async(cal_profit_rate, (dt_range.loc[sec_code, 'start_date'],
                                                       end_dt, [sec_code],
                                                       self.indicator, echo_info, rate_cal_method, res_queue,),
                                     error_callback=call_back)
            pro_pool.close()
            pro_pool.join()
            print("有效数据个数 " + str(res_queue.qsize()))
            while res_queue.qsize() > 0:
                res = res_queue.get()
                fina_data.loc[res[0], 'profit_rate'] = res[1]

    def sort_indicator(self, fina_data, partition=False):
        # 需要将正负分开排序再合并
        if partition:
            fina_date_pos = fina_data[fina_data[self.indicator] >= 0].sort_values(by=self.indicator)
            fina_data_neg = fina_data[fina_data[self.indicator] < 0].sort_values(by=self.indicator, ascending=False)
            fina_data = pd.concat([fina_date_pos, fina_data_neg])
        else:
            fina_data.sort_values(by=self.indicator, ascending=False, inplace=True)
        return fina_data


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
    validation_check = ValidationCheck(indicator='roe', sec_pool='399300.SZ',
                                       year=2019, quarter=1)
    ic_value = validation_check.ic_value_check(value_type='rank', parallel=False, rate_cal_method=2)
    # ir_value = validation_check.ir_value_check(value_type='rank', parallel=False, year=2017, quarter=1,
    #                                            test_periods=3, echo_info=1)
    print("ic_value: %f" % ic_value)

