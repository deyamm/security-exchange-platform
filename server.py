# -*- coding: utf-8 -*-
import MySQLdb as sql
import numpy as np
import pandas as pd
import pyfiles.tools as tool
from pyfiles.back_test import BackTest

def k_data(sec_code: str, **kwargs):
    # 存储绘制k线图的数据
    kdata = dict()
    # 配置参数
    start_date = kwargs.get("start_date", '2018-01-01')
    end_date = kwargs.get("end_date", '2019-02-01')
    ma_lines = kwargs.get("ma", ['ma5', 'ma10', 'ma20', 'ma30'])
    fq = kwargs.get("fq", "D")
    # 数据库连接
    con = sql.connect(host='localhost', port=3306, user='root', passwd='qq16281091', db='stock', charset='utf8')
    cur = con.cursor()
    # 获取并处理数据
    table_name = sec_code[:6] + '_' + tool.fq_trans(fq)
    columns = ['trade_date', 'open', 'close', 'high', 'low', 'amount']
    columns.extend(ma_lines)
    query = "select %s from stock.%s where trade_date between '%s' and '%s';" \
            % (','.join(columns), table_name, start_date, end_date)
    cur.execute(query)
    res = np.array(cur.fetchall())
    for line in res:
        line[0] = tool.to_date_str(line[0].date())
    data = pd.DataFrame(res, columns=columns)
    # 设置数据格式
    kdata['kdata'] = data[['open', 'close', 'high', 'low']].values.tolist()
    kdata['date'] = data['trade_date'].values.tolist()
    kdata['volume'] = data['amount'].values.tolist()
    for ma in ma_lines:
        kdata[ma] = data[ma].values.tolist()
    #
    return kdata


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


if __name__ == '__main__':
    k_data('000001.SZ')