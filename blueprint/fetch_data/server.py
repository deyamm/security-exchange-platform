from pyfiles.backtest.back_test import BackTest
from ..share import *


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


def get_sec_pool(pool_list):
    print(pool_list)
    sec_list = data_client.get_sec_pool(sec_pool='000016.SH')
    # print(sec_list['list_date'])
    return sec_list


def k_data(sec_code: str, **kwargs):
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
    data = mysql.query(query)
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
