from ..share import *
from opendatatools import swindex


def get_quant_data():
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
    index_data = data_client.get_index_data(index_code='399300.SZ', columns=['close'],
                                            start_dt=start_dt, end_dt=end_dt, freq='D')
    # print(index_data)
    data['trade_date'] = quant_data['trade_date'].tolist()
    data['indicator_value'] = quant_data['indicator_value'].tolist()
    data['index_data'] = index_data['close'].tolist()
    # print(data)
    return data


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
        scatter_data = [
            daily_data.loc[len(daily_data) - 1, ['turn_rate', 'change_pct', 'vol', 'index_name']].values.tolist()]
        data['scatter'].extend(scatter_data)
    if is_save:
        with open(PRO_PATH + '/data/heatmap.json', 'w') as f:
            json.dump(data, f, indent=1, ensure_ascii=False)
    return data
