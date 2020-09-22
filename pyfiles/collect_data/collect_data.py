# -*- coding: utf-8 -*-
from opendatatools import swindex
import sqlalchemy as sa
import chardet

def get_sw_index():
    """
    调用opendatatools库采集申万一级行业指数行情
    :return:
    """
    engine = sa.create_engine('mysql+mysqldb://root:qq16281091@localhost:3306/indexes?charset=utf8')
    indexes = ['801010', '801020', '801030', '801040', '801050',
               '801080', '801110', '801120', '801130', '801140',
               '801150', '801160', '801170', '801180', '801200',
               '801210', '801230', '801710', '801720', '801730',
               '801740', '801750', '801760', '801770', '801780',
               '801790', '801880', '801890']
    columns_order = ['date', 'index_code', 'index_name', 'open', 'close',
                     'high', 'low', 'change_pct', 'vol', 'amount']
    for i in range(0, len(indexes)):
        print(indexes[i] + ' start')
        data, msg = swindex.get_index_daily(indexes[i], start_date='1999-12-30',
                                            end_date='2020-9-18')
        data = data[columns_order]
        data.rename(columns={'date': 'trade_date'}, inplace=True)
        indicator, mm = swindex.get_index_dailyindicator(indexes[i], start_date='1999-12-30',
                                                         end_date='2020-9-18', freq='D')
        indicator = indicator[['avg_float_mv', 'date', 'dividend_yield_ratio', 'float_mv',
                               'pb', 'pe', 'turn_rate', 'turnover_pct', 'vwap']]
        indicator.rename(columns={'date': 'trade_date'}, inplace=True)
        data.set_index('trade_date', inplace=True)
        indicator.set_index('trade_date', inplace=True)
        res = data.merge(indicator, left_index=True, right_index=True, how='left')
        res.rename(columns={'change_pct': 'chg_pct', 'turn_rate': 'turnover_rate',
                   'vwap': 'avg_price'}, inplace=True)
        res.to_sql(name=indexes[i]+'_daily', con=engine, if_exists='append', index=True,
                   dtype={'trade_date': sa.DateTime()})
        engine.execute("alter table indexes.%s_daily add primary key(trade_date);" % indexes[i])
        print(indexes[i] + ' end')


if __name__ == '__main__':
    get_sw_index()
