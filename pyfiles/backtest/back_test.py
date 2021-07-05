# -*- coding: utf-8 -*-
"""
    回测过程
"""
from pyfiles.strategies.single_indicator import *
from pyfiles.strategies.multi_indicator import *
import time


class BackTest(object):
    kwargs = None

    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def back_test(self):
        # 初始化策略信息
        strategy = SingleIndicator()
        account = strategy.account
        g = strategy.g
        data_client = strategy.data_client
        #
        start_date = account.run_paras["start_date"]
        end_date = account.run_paras["end_date"]
        #
        current_date = start_date
        account.set_cur_date(cur_dt=to_date_str(current_date))
        account.set_pre_date(pre_dt=to_date_str(current_date))
        #
        print("回测开始，开始时间：%s，结束时间：%s，账户总资金：%f，股池个数：%d"
              % (to_date_str(start_date), to_date_str(end_date), account.portfolio.available_cash, g.N))
        time_start = time.time()
        # 首先在设定起始日期的基础上使得当前日期以及上一日期无为交易日
        current_date, account.previous_date = data_client.init_start_trade_date(to_date_str(start_date),
                                                                                to_date_str(end_date))
        account.current_date = current_date
        #
        counter = 0
        while current_date.__ne__(end_date):
            # print("current date: %s, end date: %s" % (to_date_str(current_date), to_date_str(end_date)))
            if data_client.is_marketday(account.current_date):
                strategy.before_trade_start()
                if counter % g.period == 0:
                    strategy.handle_data()
                strategy.after_trade_end()
                account.daily_update()
                counter = counter + 1
            #
            if data_client.is_marketday(current_date):
                account.previous_dt = current_date
            current_date = current_date + datetime.timedelta(days=1)
            account.set_cur_date(cur_dt=to_date_str(current_date))
        # print(Account.metrics.float_profit)
        print("end")
        time_end = time.time()
        print("本次回测用时:%fs" % (time_end - time_start))
        account.metrics.cal_max_drawdown()
        return account.metrics


def test():
    data_client = DataClient()
    sec_codes = ['000001.SZ', '000002.SZ', '000004.SZ', '000005.SZ', '000006.SZ',
                 '000007.SZ', '000008.SZ', '000009.SZ', '000010.SZ', '000011.SZ']
    indicator_df = pd.DataFrame(sec_codes, columns=['sec_code'])
    indicator_df.set_index('sec_code', inplace=True)
    indicator = ['eps', 'roa', 'profit_dedt', 'roe', 'roe_dt', 'op_of_gr',
                 'netprofit_margin', 'grossprofit_margin', 'adminexp_of_gr',
                 'salescash_to_or', 'tr_yoy']
    df = data_client.get_fina_data(sec_code='000002.SZ', columns=indicator)
    #
    redundance = corr_check(df.corr(), 0.8)
    for i in redundance:
        indicator.remove(i)
    # print(secs_fina[secs_fina['eps'] >= 0].sort_values(by='eps'))

    sec_pool = data_client.index_weight(index_code='399300.SZ', trade_date=datetime.date(2019, 3, 1))['con_code'].tolist()
    print(len(sec_pool))
    fina_data = data_client.get_fina_list(sec_codes=sec_pool, columns=['eps'])
    fina_date_pos = fina_data[fina_data['eps'] >= 0].sort_values(by='eps')
    fina_data_neg = fina_data[fina_data['eps'] < 0].sort_values(by='eps', ascending=False)
    fina_data = pd.concat([fina_date_pos, fina_data_neg])
    fina_data.set_index('ts_code', inplace=True)
    fina_data['indicator_rank'] = range(len(fina_data))
    for sec_code in sec_pool:
        profit_rate = SingleIndicator(start_dt='2019-03-01', end_dt='2019-04-01', sec_pool=[sec_code])\
            .back_test().period_profit_rate()
        # print(profit_rate)
        fina_data.loc[sec_code, 'profit_rate'] = profit_rate
    fina_data.sort_values(by='profit_rate', ascending=False, inplace=True)
    fina_data['profit_rate_rank'] = range(len(fina_data))
    print(fina_data)
    print(fina_data['indicator_rank'].corr(fina_data['profit_rate_rank']))
    # print(res.sort_values(by='S', axis=0).index[:5].tolist())


if __name__ == '__main__':
    data_client = DataClient()
    # BackTest().back_test()
    # test()
    # print(os.path.dirname(os.path.abspath(__file__)))
    # rate = SingleIndicator(data_client=DataClient(), account=AccountInfo(), g=GlobalVariable(),
    #                        start_dt='2019-03-01', end_dt='2019-04-01', sec_pool=['000661.SZ'], indicator='roe') \
    #     .back_test().period_profit_rate()
    # print(chg_dt('2019-03-01', 20, 'back', is_trade_day=True))
    # res1 = SingleIndicator(start_dt='2019-04-13', end_dt='2019-08-29', sec_pool=['000001.SZ'], echo_info=1,
    #                        indicator='roe', first_in=1999892.1).back_test().period_profit_rate()/100
    # res2 = DataClient().get_profit_rate(sec_code='000001.SZ', start_dt='2019-04-13', end_dt='2019-08-29', by='price')
    # print(res1)
    # print(res2)
    dt = data_client.get_fina_date_range(sec_codes=['002252.SZ'], quarter=1, year=2018)
    rate = data_client.get_profit_rate(sec_code='002252.SZ', start_dt=to_date_str(dt.loc['002252.SZ', 'start_date']),
                                       end_dt=to_date_str(dt.loc['002252.SZ', 'end_date']))
    print(dt)
    print(rate)
