"""
    用于实现data_client中用到的特殊功能
"""
import pandas as pd


def combine_fund_portfolio(funds_portfolio: pd.DataFrame) -> pd.DataFrame:
    """
    将持有基金组合所有的股票持仓进行合并：
        1.  同一股票按持仓比例合并
    :param funds_portfolio: 持有基金组合的所有股票持仓
    :return: 返回合并后的基金持仓股票组合
    """
    duplicated_stock = funds_portfolio["stock_code"].duplicated()
    print(duplicated_stock)
    return funds_portfolio
