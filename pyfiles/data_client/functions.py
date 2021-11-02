"""
    用于实现data_client中用到的特殊功能
"""
import pandas as pd


def combine_fund_portfolio(funds_portfolio: pd.DataFrame, totalmoney: float, industry_dt: pd.DataFrame) -> dict:
    """
    将持有基金组合所有的股票持仓进行合并：
        1.  同一股票按持仓比例合并
    :param funds_portfolio: 持有基金组合的所有股票持仓
    :param totalmoney: 用于计算组合持仓比例
    :param industry_dt:
    :return: 返回合并后的基金持仓股票组合
    """
    fund_res = dict()
    duplicated_funds = funds_portfolio[funds_portfolio["stock_code"].duplicated()].reset_index(drop=True)
    funds = funds_portfolio.drop_duplicates(subset=['stock_code']).set_index(keys='stock_code')
    print('重复持仓%d条' % len(duplicated_funds))
    # 将重复的持仓加到去重后的持仓中
    for i in range(len(duplicated_funds)):
        dfund = duplicated_funds.loc[i]
        funds.loc[dfund['stock_code'], 'holdmoney'] = funds.loc[dfund['stock_code'], 'holdmoney'] + dfund['holdmoney']
    funds['holdmoney'] = round(funds['holdmoney'], 2)
    funds['hold_pct'] = round(funds['holdmoney'] / totalmoney * 100, 2)
    funds.sort_values(by=['holdmoney'], ascending=False, inplace=True)
    # 统计行业分布
    industry_dt = industry_dt.set_index(keys=['stock_code'])
    funds = pd.merge(left=funds, right=industry_dt, on='stock_code', how='left')
    funds.fillna(value={'industry': '港股'}, inplace=True)
    # 行业分布
    industry_pct = funds.groupby(by='industry').sum()
    industry_pct = round(industry_pct['hold_pct'], 2)
    # 统计数据
    fund_res['portfolio'] = funds.reset_index().to_dict(orient='records')
    fund_res['industry_pct'] = industry_pct.reset_index().to_dict(orient='records')
    fund_res['metrics'] = dict()
    fund_res['metrics']['enddate'] = '2021-9-30'
    fund_res['metrics']['totalmoney'] = round(funds['holdmoney'].sum(), 2)
    fund_res['metrics']['totalpct'] = round(funds['hold_pct'].sum(), 2)
    return fund_res
