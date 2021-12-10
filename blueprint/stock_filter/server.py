from ..share import *
import time
from typing import List


def get_fina_data(sec_codes, **kwargs):
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
        fina_data = data_client.get_fina_list(sec_codes=sec_codes, columns=[], year=trade_date.year,
                                              quarter=get_quarter(trade_date), filters=filters['fina_attr'])
    else:
        fina_data = data_client.get_fina_list(sec_codes=sec_codes, columns=[], year=trade_date.year,
                                              quarter=get_quarter(trade_date))
    # 获取证券名称
    stock_basic = data_client.stock_basic(list_status=None)
    stock_basic.set_index(keys='ts_code', inplace=True)
    # print(fina_data[['ts_code', 'roe']])
    fina_data['name'] = stock_basic.loc[fina_data['ts_code'], 'name'].values
    # print(stock_basic)
    # 获取符合条件的行情数据
    if filters.get("kline_attr") is not None:
        indicator = data_client.get_k_data(dt=to_date_str(trade_date), sec_codes=sec_codes,
                                           columns=['ts_code', 'close', 'turnover_rate', 'pe', 'pb',
                                                    'total_mv', 'circ_mv'], filters=filters['kline_attr'],
                                           is_recur=False)
    else:
        indicator = data_client.get_k_data(dt=to_date_str(trade_date), sec_codes=sec_codes,
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


def sec_filter(options: List[str]):
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
                    add_option(key, words, filters)
                    break
    # print(filters)
    sec_pool = data_client.index_weight(index_code=sec_pool_code, trade_date=to_date(trade_dt))[
        'con_code'].tolist()
    fina_data = get_fina_data(sec_pool, filters=filters)
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