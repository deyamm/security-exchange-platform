# -*- coding: utf-8 -*-
import datetime
from pyfiles.exceptions import *
from pyfiles.data_client import data_client
from typing import List
from pyfiles.tools import *
import numpy as np


class GlobalVariable:
    def __init__(self):
        self.N = None
        self.benchmark_days = None
        self.context = None


class AccountInfo:
    """
    总账户
    """
    portfolio = None  # 资金账户
    current_dt = None  # 账户当前的日期
    previous_dt = None  # 前上个交易日
    positions = []  # 账户持仓
    run_paras = dict()  # 此次运行的参数
    metrics = None

    def __init__(self, **kwargs):
        self.run_paras["start_date"] = to_date(kwargs.get("start_date", None))
        self.run_paras["end_date"] = to_date(kwargs.get("end_date", None))
        if self.current_dt is None:
            self.current_dt = self.run_paras["start_date"]

    def set_paras(self, **kwargs):
        self.current_dt = to_date(kwargs.get("current_dt", self.current_dt))
        self.run_paras["start_date"] = to_date(kwargs.get("start_date", self.run_paras["start_date"]))
        self.run_paras["end_date"] = to_date(kwargs.get("end_date", self.run_paras["end_date"]))
        if self.current_dt is None:
            self.current_dt = self.run_paras["start_date"]

    def set_cur_dt(self, cur_dt: str):
        self.current_dt = to_date(cur_dt)

    def set_portfolio(self, portfolio):
        self.portfolio = portfolio

    # 返回指定证券的持有数量
    def get_sec_amount(self, sec_code: str):
        for position in self.positions:
            if position.sec_code == sec_code:
                return position.amount
        return 0

    # 查看是否有某支证券的持仓
    def has_position(self, sec_code: str):
        for position in self.positions:
            if position.sec_code == sec_code:
                return position
        return None

    # 每个交易日需要更新持仓等相关数据
    def daily_update(self):
        # 更新持仓
        for position in self.positions:
            position.daily_update(self.current_dt)
        # 更新资金账户
        self.portfolio.daily_update(self.positions)
        # 记录指标
        self.metrics.add_profit(self.portfolio.profit, to_date_str(self.current_dt))


class Security(object):
    code = None  # 证券代码
    name = None  # 证券名称

    def __init__(self, **kwargs):
        self.code = kwargs.get("code", None)
        self.name = kwargs.get("name", None)


class Order(object):
    status = None  # 订单状态
    add_time = None  # 订单生成时间
    is_buy = None  # 买单或卖单
    amount = None  # 下单数量
    # filled = None  # 已经成效数量
    security_code = None  # 证券代码
    order_id = None  # 订单ID
    price = None  # 平均成交价格
    # side = None  # 订单类型 多/空 long/short
    # commission = None  # 交易费用（佣金、税费等）

    def __init__(self, **kwargs):
        self.status = kwargs.get("status", None)

class Position(object):
    """
    持仓
    """
    sec_code = None  # 标的代码
    price = None  # 最新行情价格
    amount = 0  # 持仓数量
    available_amount = 0  # 可用数量
    total_cash_per_position = 0  # 为每个持仓分配的资金
    available_cash = 0  # 该持仓可用资金
    acc_avg_cost = 0  # 累计持仓成本
    init_time = None  # 建仓时间
    total_value = 0  # 持仓市值
    float_profit = 0  # 单支证券浮盈/亏

    def __init__(self, sec_code: str, price: float, amount: int, cash_per: float):
        self.sec_code = sec_code
        self.total_cash_per_position = cash_per
        self.available_cash = cash_per
        self.trade(price, amount, 'B')

    def trade(self, price: float, amount: int, side: str):
        if side == 'B':
            amount = 1 * amount
        elif side == 'S':
            # 判断持仓是否足够
            if self.amount < amount:
                raise ParamError("持仓不足")
            amount = -1 * amount
        else:
            raise ParamError("params error （B/S）")
        # 调整成本
        self.acc_avg_cost = (self.acc_avg_cost * self.amount + price * amount) / \
                            (self.amount + amount)
        # 当前价格
        self.price = price
        # 持仓数量
        self.amount = self.amount + amount
        # 持仓总市值， 目前不是动态变化
        self.total_value = price * self.amount
        # 该持仓可用资金
        self.available_cash = self.available_cash + price * amount * -1

    def daily_update(self, date: datetime):
        # 将价格更新为当天收盘价
        self.price = data_client.get_price(date, self.sec_code, 'close')
        # 更新单支证券持仓市值
        self.total_value = self.price * self.amount
        # T+1，将可用数量设置为持有数量
        self.available_amount = self.amount
        # 单支证券浮盈/亏
        self.float_profit = self.total_value - self.acc_avg_cost * self.amount


class Portfolio(object):
    """
    资金账户
    """
    inout_cash = 0  # 累计出入金，转入转出账户的累计资金
    available_cash = 0  # 可用资金，可以用来购买证券的资金
    transferable_cash = 0  # 可取资金，可以提现的资金
    # locked_cash = None  # 挂单锁住的资金
    sec_value = 0  # 持仓市值
    # total_cash = 0  # 总资金
    total_asset = 0  # 总资产
    profit = 0  # 收益

    def __init__(self, first_in: float):
        self.transfer(first_in, 'in')

    def transfer(self, amount: float, side: str):
        """
        转账函数，向账户中转入或转出时使用该函数
        :param amount: float 转入或转出的金额
        :param side: str 转入或转出，in表示转入，out表示转出
        :return:
        """
        self.inout_cash = self.inout_cash + amount
        if side == 'in':
            self.available_cash = self.available_cash + amount
            self.transferable_cash = self.transferable_cash + amount
            self.total_asset = self.total_asset + amount
        elif side == 'out':
            if self.transferable_cash < amount:
                raise TransferError("可取金额不足")
            self.available_cash = self.available_cash - amount
            self.transferable_cash = self.transferable_cash - amount
            self.total_asset = self.total_asset - amount
        else:
            raise TransferError("转账函数参数错误（in/out）")

    def trade(self, money: float, side: str):
        """
        购买或卖出证券时对资金进行调整
        :param money: float 购买卖出证券的金额
        :param side: str 购买或卖出，B表示买入证券，S表示卖出证券
        :return:
        """
        if side == 'B':
            # 判断资金是否足够
            if self.available_cash < money:
                raise MoneyError("账户资金不足。当前资金： %f, 需要资金：%f。"
                                 % (self.available_cash, money))
            available_cash = self.available_cash
            self.available_cash = self.available_cash - money
            # 当不可取的可用资金不足以支付本次购买时，需要在可取资金中扣除
            if available_cash - self.transferable_cash < money:
                self.transferable_cash = available_cash - money
        elif side == 'S':
            self.available_cash = self.available_cash + money
        else:
            raise ParamError("参数错误（B/S）")

    def daily_update(self, positions: List[Position]):
        # 更新持仓总市值
        self.sec_value = 0
        for position in positions:
            self.sec_value = self.sec_value + position.amount * position.price
        # 总资产, 包括现金和持仓市值
        self.total_asset = self.available_cash + self.sec_value
        # 第二天，可用资金将转化为可取资金
        self.transferable_cash = self.available_cash
        # 更新账户利润
        self.profit = self.total_asset-self.inout_cash
        print("资金账户更新完毕")


class Metrics(object):
    """
    需要计算的各个指标
    """
    float_profit = []  # 浮盈/浮亏
    float_profit_rate = []  # 浮盈/亏率
    trade_date = []
    basic_index = None
    principal = None
    anni_profit_rate = 0  # 年化收益率
    basic_profit_rate = []  # 基准收益率
    alpha = None  # Alpha值
    beta = None  # Beta值
    max_drawdown_rate = 0  # 最大回撤率
    sharpe_ratio = 0  # 夏普比率 无风险利率选一年期定期存款利率1.5%

    def __init__(self, principal, basic_index):
        # 本金
        self.principal = principal
        # 基础收益率
        self.basic_index = basic_index

    def set_basic_profit_rate(self, index_code: str, start_date: str, end_date: str, freq: str):
        data = data_client.get_index_data(index_code=index_code, columns=['pct_chg'], start_date=to_date_str(start_date),
                                          end_date=to_date_str(end_date), freq=freq)
        self.basic_profit_rate.append(0)
        for pct in data.values:
            self.basic_profit_rate.append(float_precision(self.basic_profit_rate[-1] + pct[0], 4))

    def add_profit(self, profit: float, date: str):
        # 添加收益
        self.float_profit.append(float_precision(profit, 2))
        # 添加当天日期
        self.trade_date.append(date)
        # 添加收益率
        self.float_profit_rate.append(float_precision((profit*100/self.principal), 2))
        # 更新夏普比率
        self.cal_sharpe()

    def cal_sharpe(self):
        """
        计算夏普比率 计算方法: sharpe = [E(Rp) - Rf]/σp
            E(Rp)为平均收益率， Rf为无风险利率，此处使用一年期定存利率1.5%，σp为收益曲线波动率即标准着
        :return:
        """
        # 平均收益率
        erp = float(np.mean(self.float_profit_rate))
        # 无风险利率
        rf = 1.5
        std = float(np.std(self.float_profit_rate, ddof=1))
        self.sharpe_ratio = float_precision((erp - rf) / std, 2)

    def cal_max_drawdown(self):
        """
        最大回撤率为一个最高点到一个最低点的幅度
        :return:
        """
        max_profit = -100
        for rate in self.float_profit_rate:
            if rate > max_profit:
                max_profit = rate
            if self.max_drawdown_rate < max_profit - rate:
                self.max_drawdown_rate = max_profit - rate


class Strategy(object):
    def __init__(self):
        pass

    def initialize(self):
        pass

    def set_params(self):
        pass

    def set_variables(self):
        pass

    def set_backtest(self):
        pass

    def before_trade_start(self):
        pass

    def handle_data(self, sec_code: str):
        pass

    def after_trade_end(self):
        pass


