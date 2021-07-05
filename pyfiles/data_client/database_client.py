import MySQLdb as sql
from sqlalchemy import create_engine
import numpy as np
import pandas as pd
from pyfiles.com_lib.exceptions import *


class DataClientORM(object):
    engine = None

    def __init__(self, **kwargs):
        host = kwargs.get("host", 'localhost')
        port = kwargs.get("port", 3306)
        user = kwargs.get("user", 'root')
        passwd = kwargs.get("passwd", 'qq16281091')
        db = kwargs.get("db", 'stock')
        charset = kwargs.get("charset", 'utf8')
        self.engine = create_engine("mysql://%s:%s@%s:%s/%s?%s" % (user, passwd, host, port, db, charset))


class MySqlServer(object):

    def __init__(self, **kwargs):
        host = kwargs.get("host", 'localhost')
        port = kwargs.get("port", 3306)
        user = kwargs.get("user", 'root')
        passwd = kwargs.get("passwd", 'qq16281091')
        db = kwargs.get("db", 'stock')
        charset = kwargs.get("charset", 'utf8')
        self.connect = sql.connect(host=host, port=port, user=user, passwd=passwd, db=db, charset=charset)
        self.cursor = self.connect.cursor()

    def query(self, query: str, return_type='df'):
        self.cursor.execute(query)
        data = np.array(self.cursor.fetchall())
        columns = [col[0] for col in self.cursor.description]
        if return_type == 'df':
            return pd.DataFrame(data, columns=columns)
        elif return_type == 'np':
            return data
        else:
            raise ParamError("return type error: " + return_type)

    def get_cursor(self):
        return self.cursor

    def close(self):
        self.cursor.close()
        self.connect.close()

