# -*- coding: utf-8 -*-
import numpy as np
from pyfiles.utils import *

def order(account: AccountInfo, g: GlobalVariable, sec_code: str, price: float, amount: int, side: str):
    """
    下单函数
    :param account:
    :param g:
    :param sec_code:
    :param price:
    :param amount:
    :param side:
    :return:
    """
    # 持仓 list
    positions = account.positions
    # 资金账户 Portfolio
    portfolio = account.portfolio
    totol_money = price * amount
    if side == 'B':  # 买入
        # 已有该股的持仓
        for position in positions:
            if position.sec_code == sec_code:
                # 调整持仓
                position.trade(price, amount, 'B')
                # 调整资金账户, 'B'表示买入证券
                portfolio.trade(totol_money, 'B')
                # print('买入证券%s成功，数量%d，价格%f，总价%f' % (sec_code, amount, price, amount*price))
                return
        # 未有该股的持仓，添加该证券的持仓
        new_position = Position(sec_code=sec_code, price=price, amount=amount,
                                cash_per=account.portfolio.inout_cash/g.N)
        positions.append(new_position)
        # 调整账户资金
        portfolio.trade(totol_money, 'B')
        # print('新增持仓，买入证券%s成功，数量%d，价格%f，总价%f' % (sec_code, amount, price, amount*price))
    elif side == 'S':  # 卖出
        for position in positions:
            if position.sec_code == sec_code:
                # 调整持仓
                position.trade(price, amount, 'S')
                # if position.amount == 0:
                #     positions.remove(position)
                # 调整资金
                portfolio.trade(totol_money, 'S')
                # print('卖出证券%s成功，数量%d，价格%f，总价%f' % (sec_code, amount, price, amount*price))
                return
        # 未有该证券的仓位
        # raise ParamError("持仓不足")
        # print("未操作")
    else:
        raise ParamError("下单参数错误（B/S）")
