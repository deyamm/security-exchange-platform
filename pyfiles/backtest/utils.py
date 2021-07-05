# -*- coding: utf-8 -*-
"""
    为便于维护，
    关于日期变量命名，后缀为dt的变量为字符串，后缀为date的变量为datetime.date
"""

from pyfiles.data_client import DataClient, MySqlServer
from pyfiles.com_lib.variables import *
from pyfiles.com_lib.tools import *
import numpy as np
import time


class TradeLog(object):
    """
    该类用于记录交易过程信息，包括买入、卖出等内容，并可以导出为文件；
    交易记录有两种形式，一种为自然语言方式，另一种为dataframe实例。
    """

    def __init__(self):
        self.logs = []
        self.log_dict_list = []
        self.log_df = pd.DataFrame()
        pass

    def add_log(self, sec_code, side, dt, price, amount, money, available_cash):
        if side == 'B':
            single_log = "日期：%s，买入证券%s共%d股，买入价格%f，共%f元，当前账户剩余资金%f" \
                         % (dt, sec_code, amount, price, money, available_cash)
        elif side == 'S':
            single_log = "日期：%s，卖出证券%s共%d股，卖出价格%f，共%f元，当前账户剩余资金%f" \
                         % (dt, sec_code, amount, price, money, available_cash)
        else:
            single_log = "日期：%s" % dt
        self.logs.append(single_log)
        self.log_dict_list.append({'sec_code': sec_code, 'side': side, 'date': dt, 'price': price,
                                   'amount': amount, 'money': money, 'available_cash': available_cash})

    def save_log(self, path, sec_code=None):
        log_df = pd.DataFrame(self.log_dict_list)
        # print(log_df)
        if sec_code is None:
            log_index = log_df.index.tolist()
        else:
            log_index = log_df[log_df['sec_code'] == sec_code].index.tolist()
        with open(path, 'a') as f:
            for i in log_index:
                f.write(self.logs[i] + '\n')


class GlobalVariable:
    def __init__(self):
        self.indicator = None
        self.N = None
        self.benchmark_days = None
        self.sec_pool = None
        self.period = None


class Position(object):
    """
    持仓类，每一个实例代表一支股票的持仓
    """
    sec_code = None  # 标的代码
    price = 0  # 最新行情价格
    amount = 0  # 持仓数量
    available_amount = 0  # 可用数量
    total_cash_per_position = 0  # 为每个持仓分配的资金
    available_cash = 0  # 该持仓可用资金
    acc_avg_cost = 0  # 累计持仓成本
    init_time = None  # 建仓时间
    total_value = 0  # 持仓市值
    float_profit = 0  # 单支证券浮盈/亏
    log: TradeLog = None  # 该持仓的交易记录

    def __init__(self, sec_code: str, cash_per: float, dt: str, price: float = 0, amount: int = 0):
        self.sec_code = sec_code
        self.price = 0
        self.amount = 0
        self.available_amount = 0
        self.available_cash = 0
        self.total_cash_per_position = cash_per
        self.available_cash = cash_per
        self.acc_avg_cost = 0
        self.init_time = dt
        self.total_value = 0
        self.float_profit = 0
        self.log = TradeLog()
        self.trade(price=price, amount=amount, side='B', dt=dt)

    def trade(self, price: float, amount: int, side: str, dt: str):
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
        # 添加交易记录
        # self.log.add_log(sec_code=self.sec_code, side=side, dt=dt,
        #                  price=price, amount=amount, money=price* amount, available_cash=self.available_cash)

    def daily_update(self, dt: str, data_client: DataClient):
        # 将价格更新为当天收盘价
        self.price = data_client.get_price(dt, self.sec_code, 'close', 'last')
        # 更新单支证券持仓市值
        self.total_value = self.price * self.amount
        # T+1，将可用数量设置为持有数量
        self.available_amount = self.amount
        # 单支证券浮盈/亏
        self.float_profit = self.total_value - self.acc_avg_cost * self.amount

    def clear(self, price: float, portfolio, dt: str):
        """
        按指定价格清空该持仓
        :param dt:
        :param portfolio: 资金账户
        :param price: 清仓价
        :return:
        """
        # print('清仓，价格：%f，数量：%d' % (price, self.amount))
        portfolio.trade(sec_code=self.sec_code, price=price, amount=self.amount, side='S', dt=dt)
        self.trade(price=price, amount=self.amount, side='S', dt=dt)


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
    log: TradeLog = None  # 交易记录
    log_path = None  # 日志路径

    def __init__(self, first_in: float, **kwargs):
        # self.profit = 0
        self.log = TradeLog()
        self.transfer(first_in, 'in')
        self.log_path = kwargs.get("log_path")
        # print(id(self.profit))

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

    def trade(self, sec_code: str, price: float, amount: int, side: str, dt: str):
        """
        购买或卖出证券时对资金进行调整
        :param dt:
        :param amount:
        :param price:
        :param sec_code:
        :param side: str 购买或卖出，B表示买入证券，S表示卖出证券
        :return:
        """
        money = price * amount
        if side == 'B':
            # 判断资金是否足够
            if self.available_cash < money:
                self.log.save_log(path=self.log_path + 'log.txt', sec_code=sec_code)
                raise MoneyError("账户资金不足。当前资金： %f, 需要资金：%f。"
                                 % (self.available_cash, money))
            available_cash = self.available_cash
            self.available_cash = self.available_cash - money
            # 当不可取的可用资金不足以支付本次购买时，需要在可取资金中扣除
            if available_cash - self.transferable_cash < money:
                self.transferable_cash = available_cash - money
            # print("买入：" + str(money))
            # print("当前可用总现金： " + str(self.available_cash))
            self.log.add_log(sec_code=sec_code, price=price, amount=amount, dt=dt, side=side,
                             money=money, available_cash=self.available_cash)
        elif side == 'S':
            self.available_cash = self.available_cash + money
            # print("卖出：" + str(money))
            # print("当前可用总现金： " + str(self.available_cash))
            self.log.add_log(sec_code=sec_code, price=price, amount=amount, dt=dt, side=side,
                             money=money, available_cash=self.available_cash)
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
        self.profit = self.total_asset - self.inout_cash
        # print(id(self.profit))

    def __del__(self):
        # print(self.log.log_df)
        self.log.save_log(path=self.log_path + 'total_log.txt')


class Metrics(object):
    """
    需要计算的各个指标
    """
    float_profit = []  # 浮盈/浮亏
    float_profit_rate = []  # 浮盈/亏率
    trade_date = []
    basic_index = None  # 目前还未用到
    principal = None  # 本金
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
        self.float_profit = []
        self.float_profit_rate = []
        self.trade_date = []
        self.basic_profit_rate = []

    def set_basic_profit_rate(self, index_code: str, start_dt: str, end_dt: str, freq: str, data_client: DataClient):
        """
        设置基准收益率
        :param index_code:
        :param start_dt:
        :param end_dt:
        :param freq:
        :param data_client:
        :return:
        """
        data = data_client.get_index_data(index_code=index_code, columns=['pct_chg'], start_dt=to_date_str(start_dt),
                                          end_dt=to_date_str(end_dt), freq=freq)
        self.basic_profit_rate.append(0)
        for pct in data.values:
            self.basic_profit_rate.append(float_precision(self.basic_profit_rate[-1] + pct[0], 4))

    def add_profit(self, profit: float, dt: str):
        # 添加收益
        self.float_profit.append(float_precision(profit, 2))
        # 添加当天日期
        self.trade_date.append(dt)
        # 添加收益率
        self.float_profit_rate.append(float_precision((profit * 100 / self.principal), 2))

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
        try:
            self.sharpe_ratio = float_precision((erp - rf) / std, 2)
        except ZeroDivisionError:
            self.sharpe_ratio = 0

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
                self.max_drawdown_rate = float_precision(max_profit - rate, 2)

    def period_profit_rate(self):
        return float_precision(self.float_profit_rate[-1], 2)


class AccountInfo(object):
    """
    总账户
    """
    portfolio: Portfolio = None  # 资金账户
    current_date: datetime.date = None  # 账户当前的日期
    previous_date: datetime.date = None  # 前上个交易日
    positions = []  # 账户持仓
    run_paras = dict()  # 此次运行的参数
    metrics: Metrics = None
    data_client = None

    def __init__(self, data_client: DataClient = None, **kwargs):
        self.positions = []
        self.run_paras["start_date"] = to_date(kwargs.get("start_date", None))
        self.run_paras["end_date"] = to_date(kwargs.get("end_date", None))
        self.data_client = data_client
        if self.current_date is None:
            self.current_date = self.run_paras["start_date"]

    def set_paras(self, **kwargs):
        self.current_date = to_date(kwargs.get("current_date", self.current_date))
        self.run_paras["start_date"] = to_date(kwargs.get("start_date", self.run_paras["start_date"]))
        self.run_paras["end_date"] = to_date(kwargs.get("end_date", self.run_paras["end_date"]))
        if self.current_date is None:
            self.current_date = self.run_paras["start_date"]

    def set_cur_date(self, cur_dt: str):
        self.current_date = to_date(cur_dt)

    def set_pre_date(self, pre_dt: str):
        self.previous_date = to_date(pre_dt)

    def set_portfolio(self, portfolio):
        self.portfolio = portfolio

    def set_data_client(self, data_client):
        self.data_client = data_client

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
    def daily_update(self, **kwargs):
        echo_info = kwargs.get("echo_info", 1)
        # 更新持仓
        for position in self.positions:
            position.daily_update(to_date_str(self.current_date), data_client=self.data_client)
        # 更新资金账户
        self.portfolio.daily_update(self.positions)
        # 记录指标
        self.metrics.add_profit(self.portfolio.profit, to_date_str(self.current_date))
        if echo_info >= ECHO_INFO_ACCOUNT:
            print("账户更新结束，%s，当前总资产：%f" % (to_date_str(self.current_date), self.portfolio.total_asset))

    def clear_position(self, **kwargs):
        """
        清仓操作，将所有持仓按指定日期开盘价卖出
        :return:
        """
        echo_info = kwargs.get("echo_info", 1)
        for position in self.positions:
            # print("清仓：" + position.sec_code)
            if position.amount <= 0:
                continue
            price = self.data_client.get_price(dt=to_date_str(self.current_date), sec_code=position.sec_code,
                                               price_type='open', not_exist='last')
            amount = position.amount
            position.clear(price=price, portfolio=self.portfolio, dt=to_date_str(self.current_date))
            if echo_info >= ECHO_INFO_TRADE:
                print("卖出，%s，%s，数量：%d，价格：%f， 剩余现金：%f"
                      % (to_date_str(self.current_date), position.sec_code, amount, price, self.portfolio.available_cash))
        # self.positions = []


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


class Strategy(object):
    account: AccountInfo = None
    g: GlobalVariable = None
    kwargs = None
    data_client: DataClient = None
    backtest_params: dict = None

    def __init__(self, kwargs):
        # self.data_client = DataClient()
        # 初始化账户
        # self.account = AccountInfo(data_client=self.data_client)
        # 初始化全局变量
        # self.g = GlobalVariable()
        # 设置参数
        # self.kwargs = kwargs
        # 初始化策略
        # self.initialize()
        pass

    def initialize(self):
        # 设置回测范围
        self.account.set_paras(start_date=to_date(self.kwargs.get("start_dt", '2015-01-01')),
                               end_date=to_date(self.kwargs.get("end_dt", '2019-01-01')))
        # 资金账户
        self.account.portfolio = Portfolio(first_in=self.kwargs.get("first_in", 100000),
                                           log_path='/home/deyam/Stock/project/logs/')
        # 指标
        self.account.metrics = Metrics(principal=self.account.portfolio.inout_cash, basic_index=0)
        self.set_params()
        self.set_variables()

    def set_params(self):
        pass

    def set_variables(self):
        pass

    def set_backtest(self):
        pass

    def before_trade_start(self):
        pass

    def handle_data(self):
        pass

    def after_trade_end(self):
        pass

    def back_test(self):
        start_date = self.account.run_paras['start_date']
        end_date = self.account.run_paras['end_date']
        #
        current_date = start_date
        self.account.set_cur_date(cur_dt=to_date_str(current_date))
        self.account.set_pre_date(pre_dt=to_date_str(start_date))
        #
        if self.backtest_params['echo_info'] >= ECHO_INFO_BE:
            print("回测开始，开始日期：%s，结束日期：%s，账户总资金：%f，股池: %s"
                  % (to_date_str(start_date), to_date_str(end_date), self.account.portfolio.inout_cash,
                     ','.join(self.g.sec_pool)))
        time_start = time.time()
        current_date, self.account.previous_date = self.data_client.init_start_trade_date(
            start_dt=to_date_str(start_date), end_dt=to_date_str(end_date))
        self.account.set_cur_date(cur_dt=to_date_str(current_date))
        # 计算调仓时期
        counter = 0
        # print(current_date, end_date)
        while current_date.__ne__(end_date):
            if self.data_client.is_marketday(date=self.account.current_date):
                self.before_trade_start()
                if counter % self.g.period == 0:
                    self.handle_data()
                self.after_trade_end()
                self.account.daily_update(echo_info=self.backtest_params['echo_info'])
                counter = counter + 1
            #
            if self.data_client.is_marketday(date=current_date):
                self.account.previous_date = current_date
            current_date = current_date + datetime.timedelta(days=1)
            self.account.set_cur_date(cur_dt=to_date_str(current_date))
        time_end = time.time()
        if self.backtest_params['echo_info'] >= ECHO_INFO_BE:
            print("回测结束，本次用时：%fs" % (time_end - time_start))
        self.account.metrics.cal_max_drawdown()
        self.account.metrics.cal_sharpe()
        return self.account.metrics


