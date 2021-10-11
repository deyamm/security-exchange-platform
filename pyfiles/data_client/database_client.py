import MySQLdb as sql
from sqlalchemy import create_engine
import numpy as np
import pymongo
import pandas as pd
import tushare as ts
import redis
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
        self.client.set(key, value.to_msgpack(), ex=600)

    def is_exsits(self, key):
        return self.client.exists(key)

    def get_data(self, key: str) -> pd.DataFrame:
        value = pd.read_msgpack(self.client.get(key))
        return value


if __name__ == '__main__':
    mongo = MongoClient()
    fina = mongo.client['fina_db']
    local = mongo.client['local']
    res = local.collection_names()
    print(res)
