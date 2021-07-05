# 自定义异常
class TransferError(Exception):
    """
    转账异常，主要有转出金额超出可取金额；调用转账函数传入错误参数
    """
    pass


class MoneyError(Exception):
    """
    资金异常
    """
    pass


class ParamError(Exception):
    pass


class SQLError(Exception):
    pass
