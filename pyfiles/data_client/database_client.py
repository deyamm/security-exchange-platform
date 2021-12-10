import MySQLdb as sql
from sqlalchemy import create_engine
import pymongo
import tushare as ts
import redis
import requests
import js2py
import pickle
from bs4 import BeautifulSoup
from pyfiles.com_lib import *


class MongoClient(object):
    client = None

    def __init__(self, **kwargs):
        user = kwargs.get("user", 'root')
        passwd = kwargs.get("passwd", 'qq16281091')
        host = kwargs.get("host", 'localhost')
        db = kwargs.get("db", 'fina_db')
        self.client = pymongo.MongoClient("mongodb://%s:%s@%s/%s?authSource=admin"
                                          % (user, passwd, host, db))

    def get_client(self):
        return self.client


class DataClientORM(object):
    engine = None
    connect = None

    def __init__(self, **kwargs):
        host = kwargs.get("host", 'localhost')
        port = kwargs.get("port", 3306)
        user = kwargs.get("user", 'root')
        passwd = kwargs.get("passwd", 'qq16281091')
        db = kwargs.get("db", 'stock')
        charset = kwargs.get("charset", 'utf8')
        self.engine = create_engine("mysql://%s:%s@%s:%s/%s?%s" % (user, passwd, host, port, db, charset))
        self.connect = self.engine.connect()

    def get_engine(self):
        return self.engine

    def get_connect(self):
        return self.connect

    def __del__(self):
        self.connect.close()


class MySqlServer(object):
    connect = None
    cursor = None

    def __init__(self, **kwargs):
        host = kwargs.get("host", 'localhost')
        port = kwargs.get("port", 3306)
        user = kwargs.get("user", 'root')
        passwd = kwargs.get("passwd", 'qq16281091')
        db = kwargs.get("db", 'stock')
        charset = kwargs.get("charset", 'utf8')
        self.connect = sql.connect(host=host, port=port, user=user, passwd=passwd, db=db,
                                   charset=charset)
        self.cursor = self.connect.cursor()

    def __del__(self):
        self.cursor.close()

    def query(self, query: str, return_type='df'):
        self.cursor.execute(query)
        data = list(self.cursor.fetchall())
        # print(data)
        columns = [col[0] for col in self.cursor.description]
        df_res = pd.DataFrame(data, columns=columns)
        if 'trade_date' in columns:
            df_res['trade_date'] = df_res['trade_date'].map(lambda x: to_date(x))
        if 'cal_date' in columns:
            df_res['cal_date'] = df_res['cal_date'].map(lambda x: to_date(x))
        if len(data) < 1:
            return pd.DataFrame()
        if return_type == 'df':
            # print(df_res.dtypes)
            return df_res
        elif return_type == 'np':
            return df_res.values
        else:
            raise ParamError("return type error: " + return_type)

    def get_cursor(self):
        return self.cursor

    def close(self):
        self.cursor.close()
        self.connect.close()


class TushareClient(object):
    pro = None

    def __init__(self):
        ts.set_token(TS_TOKEN)
        self.pro = ts.pro_api()

    def get_pro(self):
        return self.pro


class RedisClient(object):
    client = None

    def __init__(self):
        self.client = redis.Redis(host='localhost', port=6379, db=1)

    def get_client(self):
        return self.client

    def store_data(self, key: str, value: pd.DataFrame):
        self.client.set(key, pickle.dumps(value), ex=600)
        print('%s has stored in redis, existence time: 600s' % key)

    def is_exsits(self, key):
        return self.client.exists(key)

    def get_data(self, key: str) -> pd.DataFrame:
        # value = pd.read_pickle(self.client.get(key))
        value = pickle.loads(self.client.get(key))
        return value


class EastMoneyClient(object):
    """
    东方财富数据接口
    """
    attr_dict = None

    def __init__(self):
        self.attr_dict = AttributeDict()

    def get_portfolio_page(self, code: str, topline: int, year: int, month: int):
        url_params = {'type': 'jjcc', 'code': code[:6], 'topline': topline,
                      'year': year, 'month': month}
        url = 'https://fundf10.eastmoney.com/FundArchivesDatas.aspx'
        response = requests.get(url, url_params)
        if response.status_code != 200:
            raise RequestError('url: %s, code: %d' % (url, response.status_code))
        apidata = js2py.eval_js(response.text).to_dict() if response.text.startswith(EASTMONEY_PREFIX) else {'content': ''}
        return apidata

    def get_fund_portfolio(self, code: str, topline: int, year: int, month: int) -> pd.DataFrame:
        """
        东方财富基金持仓
        eg. https://fundf10.eastmoney.com/FundArchivesDatas.aspx?type=jjcc&code=006113&topline=10&year=&month=
        url: https://fundf10.eastmoney.com/FundArchivesDatas.aspx
        type: jjcc指基金持仓
        :param code: 基金代码（只包含6位数字）
        :param topline: 前n持仓（年报与半年报可以取到所有的持仓，一季报和三季报只包括前10大持仓，*则为特殊持仓）
        :param year: 指定年份的持仓，会获取当年各个季度的持仓
        :param month: 目前的理解是指定月份的详细持仓
        :return:
        """
        apidata = self.get_portfolio_page(code, topline, year, month)
        # 首先判断指定年份是否有持仓数据，通过apidata中的arryear来判断
        # 如果不存在，则根据大小关系设置year和month并再次获取apidata
        arryear = apidata.get('arryear', [])
        arryear.sort(reverse=True)  # 降序排序
        if year not in arryear:
            if year > arryear[0]:
                year = arryear[0]
                month = 12
            else:
                year = arryear[-1]
                month = 3
            apidata = self.get_portfolio_page(code, topline, year, month)
        # 解析表格中的持仓数据
        bs = BeautifulSoup(apidata.get('content', ''), "html.parser")
        end_dts = get_fund_end_dts(year=year, length=len(bs.select('.box')))
        dt = None
        for tr in bs.select('tr'):
            ths = tr.select('th')
            if len(ths) > 0:
                if dt is not None:
                    # print(id(dt))
                    end_dt = end_dts.pop()
                    self.format_fund_portfolio(dt, end_dt, code)
                    if to_date(end_dt).month <= month:
                        return dt
                dt = pd.DataFrame(columns=list(map(lambda x: x.text, ths)))
            else:
                tds = tr.select('td')
                dt.loc[len(dt)] = list(map(lambda x: x.text, tds))
        self.format_fund_portfolio(dt, end_dates.pop(), code)
        return dt

    def format_fund_portfolio(self, dt: pd.DataFrame, end_date: str, fund_code: str):
        """
        将从网页中获取的原始持仓数据的格式结构化
        该方法是在所传参数的原对象上修改
        :param dt:
        :param end_date: 该持仓的公告日期
        :param fund_code:
        :return:
        """
        # 通过英文列名筛选出有用的列
        n_columns, o_columns = self.attr_dict.columns_attr(dt.columns.tolist())
        dt.drop(o_columns, axis=1, inplace=True)
        dt.columns = n_columns
        # print(id(dt))
        # dt = dt[n_columns] # 改过程会改变dt变量的地址
        # print(id(dt))
        # 基金代码
        dt.insert(0, 'fund_code', fund_code)
        # 持仓报告日期
        dt.insert(1, 'end_date', end_date)
        # 为股票代码添加后缀
        dt['stock_code'] = dt['stock_code'].map(lambda x: stock_code_complete(x))
        # 将百分比删去'%'并转换为float
        dt['hold_pct'] = dt['hold_pct'].map(lambda x: x[:-1]).astype('float')
        # 删去','并转换为float
        dt['amount'] = dt['amount'].map(lambda x: x.replace(',', ''))
        dt['mkv'] = dt['mkv'].map(lambda x: x.replace(',', ''))
        dt[['amount', 'mkv']] = dt[['amount', 'mkv']].astype('float')
        # print(id(dt))


if __name__ == '__main__':
    client = EastMoneyClient()
    client.get_fund_portfolio(code='006113.OF', topline=10, year=2021, month=6)
