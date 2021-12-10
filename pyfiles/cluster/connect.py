from thrift.transport import TSocket, TTransport
from thrift.protocol import TBinaryProtocol
from hbase.ttypes import Mutation
from hbase import Hbase
from pyfiles.com_lib.tools import *
import pandas as pd
import tushare as ts
from multiprocessing import Pool
from pyhive import hive
import happybase
from pyspark import SparkConf
from pyspark import SparkContext
import findspark
import json
from kafka import KafkaProducer, KafkaConsumer
from kafka.errors import kafka_errors
import time
from pyfiles.com_lib.variables import *
import os

'''
    该文件用于测试python连接hbase，以及向hbase中存入数据，首先是将所有股票的个股日K数据
    hadoop生态版本
    hadoop  3.2.1
    java    1.8.0
    scala   2.11.6
    hbase   2.4.2
    hive    3.1.2
    spark   3.0.2
    kafka   2.4.1
    flink   1.14.0
    zk      3.5.9
'''


class HbaseClient(object):
    """
    hbase
    """

    def __init__(self):
        self.connection = happybase.Connection(host='localhost', port=9090,
                                               table_prefix='stock', table_prefix_separator=':')
        self.table = self.connection.table('stock_daily')

    def exe_cmd(self):
        rows = self.table.scan(row_prefix=b'000001')
        print(pd.DataFrame(list(rows)))
        # for key, data in rows:
        #     print(str(key, 'utf-8'))


class SparkClient(object):
    """
    spark
    """
    app_name = "test"
    master = "spark://localhost:7077"
    sc = None

    def __init__(self):
        os.environ['SPARK_HOME'] = r"/usr/local/spark-3.0.2"
        os.environ['JAVA_HOME'] = r"/usr/lib/jvm/java-1.8.0-openjdk-amd64"
        findspark.init()
        conf = SparkConf().setAppName(self.app_name).setMaster(self.master)
        self.sc = SparkContext(conf=conf)

    def test(self):
        # lines = self.sc.textFile("hdfs://localhost:9000/input/file1.txt")
        data = [1, 2, 3, 4]
        nums = self.sc.parallelize(data)
        # nums.collect()
        print(nums.map(lambda x: (x, 1)).collect())


class FlinkClient(object):

    def __init__(self):
        pass


class Producer(object):
    """
    kafka生产者
    由Python爬取分时数据并发送到kafka
    """
    producer = None

    def __init__(self):
        self.producer = KafkaProducer(
            bootstrap_servers=['172.18.0.2:9092'],  # 此处ip地址为容器的地址
            key_serializer=lambda k: json.dumps(k).encode('utf-8'),
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
        )

    def produce_msg(self, topic: str, data: List[str]):
        num = 0
        while True:
            # print('before')
            future = self.producer.send(
                topic,
                key='count_num',
                value=str(num)
            )
            print("send %s" % str(num))
            time.sleep(1)
            num += 1
            try:
                future.get(timeout=10)
            except kafka_errors:
                print('error1')


def insert_row(columns, line, client):
    mutations = []
    for j in range(len(columns)):
        if j < 1:
            mutations.append(Mutation(column='info:' + columns[j], value=str(line[columns[j]])))
        elif j < 2:
            mutations.append(Mutation(column='info:' + columns[j], value=chg_dt_format(dt=line[columns[j]])))
        elif j < 11:
            mutations.append(Mutation(column='price:' + columns[j], value=str(line[columns[j]])))
        else:
            mutations.append(Mutation(column='daily_indicator:' + columns[j], value=str(line[columns[j]])))
    client.mutateRow('stock:stock_daily', line['ts_code'][:6] + line['trade_date'], mutations)


def insert_hbase_rows():
    # col1 = ColumnDescriptor(name='info')
    # col2 = ColumnDescriptor(name='price')
    # col3 = ColumnDescriptor(name='daily_indicator')
    # client.createTable('stock:test', [col1, col2, col3])
    # print(client.getTableNames())
    #
    socket = TSocket.TSocket('127.0.0.1', 9090)
    socket.setTimeout(5000)
    #
    transport = TTransport.TBufferedTransport(socket)
    protocol = TBinaryProtocol.TBinaryProtocol(transport)
    #
    client = Hbase.Client(protocol)
    socket.open()

    ts.set_token('92c6ece658c377bcc32995a68319cf01696e1266ed60be0ae0dd0947')
    pro = ts.pro_api()
    data = pro.stock_basic(list_status='L', exchange="SZSE", fields='ts_code,symbol,name,list_date')
    #
    start_index = 0
    # start_index = data['ts_code'].tolist().index('300921.SZ') + 1
    pro_pool = Pool(30)
    for i in range(start_index, start_index+1):
        code = data['ts_code'][i]
        # start_date = data['list_date'][i]
        # 日线信息以及价格
        kdata = pro.daily(ts_code=code)
        if kdata is None:
            continue
        start_date = kdata.loc[len(kdata)-1, 'trade_date']
        # 每日指标
        daily_indicator = pro.daily_basic(ts_code=code, start_date=start_date,)
        if daily_indicator is not None and len(daily_indicator) > 0:
            kdata = pd.merge(left=kdata,
                             right=daily_indicator.drop(['ts_code', 'close'], axis=1),
                             on='trade_date', how='left')
        # 复权因子
        adj_factor = pro.adj_factor(ts_code=code, start_date=start_date)
        if adj_factor is not None and len(adj_factor) > 0:
            kdata = pd.merge(left=kdata, right=adj_factor.drop(['ts_code'], axis=1), on='trade_date', how='left')
        kdata.fillna('None', inplace=True)
        columns = kdata.columns
        print('%s数据开始入库....' % code)
        for line in range(len(kdata)):
            pro_pool.apply_async(insert_row, (columns, kdata.loc[line], client,),
                                 error_callback=call_back)
        print('%s数据入库' % code)
        # kdata.to_csv('../../data/tmp.csv', index=False)
        # print(kdata.columns)
    socket.close()


def insert_hive_rows():
    conn = hive.Connection(host='localhost', port=10000, username='root', password='qq16281091',
                           database='stock', auth='LDAP')
    cursor = conn.cursor()
    cursor.execute("select * from stock.moneyflow")
    res = cursor.fetchall()
    print(res)
    cursor.close()
    conn.close()


def hbase_operate():
    socket = TSocket.TSocket('127.0.0.1', 9090)
    socket.setTimeout(5000)
    #
    transport = TTransport.TBufferedTransport(socket)
    protocol = TBinaryProtocol.TBinaryProtocol(transport)
    #
    client = Hbase.Client(protocol)
    socket.open()
    print(client)
    socket.close()


if __name__ == '__main__':
    Producer().produce_msg('test', ['data1', 'data2', 'data3'])
    pass


