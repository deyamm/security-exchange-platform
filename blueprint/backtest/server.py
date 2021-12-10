from pyfiles.strategies.single_indicator import SingleIndicator
from pyfiles.com_lib.exceptions import *


def backtest(kwargs: dict):
    print(kwargs)
    sec_pool = kwargs.get("sec_pool", dict())
    strategy = kwargs.get("stragety", None)
    start_dt = kwargs.get("start_date", None)
    end_dt = kwargs.get("end_date", None)
    first_in = kwargs.get("first_in", 100000)
    if strategy is None:
        raise ParamError("求指定回测策略")
    if strategy == 'multi_indicator':
        indicators = kwargs.get("indicators", [])
        if len(indicators) < 1:
            raise ParamError("多因子未指定指标")
    elif strategy == 'single_indicator':
        indicator = kwargs.get("indicator", None)
        if indicator is None:
            raise ParamError("单因子未指定指标")
        metrics = SingleIndicator(sec_pool=list(sec_pool.keys()), indicator=indicator,
                                  start_dt=start_dt, end_dt=end_dt, echo_info=2,
                                  max_position_num=1, first_in=first_in).back_test()
        return metrics
    else:
        raise ParamError("错误或未开发策略： %s" % strategy)
