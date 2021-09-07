# -*- coding: utf-8 -*-
from pyfiles.backtest.utils import *
from pyfiles.com_lib.variables import *


def order(account: AccountInfo, g: GlobalVariable, sec_code: str, price: float, amount: int, side: str, **kwargs):
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
    echo_info = kwargs.get("echo_info", 1)
    if side == 'B':  # 买入
        # 已有该股的持仓
        position = account.has_position(sec_code=sec_code)
        if position is None:
            # 未有该股的持仓，添加该证券的持仓
            new_position = Position(sec_code=sec_code, price=price, amount=amount,
                                    cash_per=account.portfolio.available_cash / g.N, dt=to_date_str(account.current_date))
            positions.append(new_position)
            # 调整账户资金
            portfolio.trade(sec_code=sec_code, price=price, amount=amount, side='B',
                            dt=to_date_str(account.current_date))
            if echo_info >= ECHO_INFO_TRADE:
                print('新增，%s，%s，数量：%d，价格：%f，总价：%f，剩余现金：%f'
                      % (to_date_str(account.current_date), sec_code, amount, price, amount*price, account.portfolio.available_cash))
        else:
            # 调整持仓
            position.trade(price=price, amount=amount, side='B', dt=to_date_str(account.current_date))
            # 调整资金账户, 'B'表示买入证券
            portfolio.trade(sec_code=sec_code, price=price, amount=amount,
                            side='B', dt=to_date_str(account.current_date))
            if echo_info >= ECHO_INFO_TRADE:
                print('买入，%s，%s，数量：%d，价格：%f，总价：%f，剩余现金：%f'
                      % (to_date_str(account.current_date), sec_code, amount, price, amount*price, account.portfolio.available_cash))
    elif side == 'S':  # 卖出
        for position in positions:
            if position.sec_code == sec_code:
                # 调整持仓
                position.trade(price=price, amount=amount, side='S', dt=dt)
                # if position.amount == 0:
                #     positions.remove(position)
                # 调整资金
                portfolio.trade(sec_code=sec_code, price=price, amount=amount,
                                side='S', dt=to_date_str(account.current_date))
                if echo_info >= ECHO_INFO_TRADE:
                    print('卖出，%s，%s，数量：%d，价格：%f，总价%f，剩余现金：%f'
                          % (to_date_str(account.current_date), sec_code, amount, price, amount*price, account.portfolio.available_cash))
                return
        # 未有该证券的仓位
        # raise ParamError("持仓不足")
        # print("未操作")
    else:
        raise ParamError("下单参数错误（B/S）")
