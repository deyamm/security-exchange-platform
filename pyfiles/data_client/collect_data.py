# -*- coding: utf-8 -*-
from opendatatools import swindex
from pyfiles.com_lib import *
from pyfiles.data_client.database_client import MySqlServer
import sqlalchemy as sa
import pymongo
import tushare as ts
import datetime
import time
from typing import List


class CollectData(object):
    pro = None
    engine = None
    mongo_client = None
    mysql = None

    def __init__(self):
        ts.set_token('92c6ece658c377bcc32995a68319cf01696e1266ed60be0ae0dd0947')
        self.pro = ts.pro_api()
        self.engine = sa.create_engine('mysql+mysqldb://root:qq16281091@localhost:3306/indexes?charset=utf8')
        self.mongo_client = pymongo.MongoClient("mongodb://root:qq16281091@localhost/fina_db?authSource=admin")
        self.mysql = MySqlServer()

    def __del__(self):
        self.mongo_client.close()
        self.mysql.close()

    def get_sw_index(self):
        """
        调用opendatatools库采集申万一级行业指数行情
        :return:
        """
        indexes = ['801010', '801020', '801030', '801040', '801050',
                   '801080', '801110', '801120', '801130', '801140',
                   '801150', '801160', '801170', '801180', '801200',
                   '801210', '801230', '801710', '801720', '801730',
                   '801740', '801750', '801760', '801770', '801780',
                   '801790', '801880', '801890']
        columns_order = ['date', 'index_code', 'index_name', 'open', 'close',
                         'high', 'low', 'change_pct', 'vol', 'amount']
        for i in range(0, len(indexes)):
            print(indexes[i] + ' start')
            data, msg = swindex.get_index_daily(indexes[i], start_date='1999-12-30',
                                                end_date='2020-9-18')
            # 设置dataframe列的顺序
            data = data[columns_order]
            data.rename(columns={'date': 'trade_date'}, inplace=True)
            indicator, mm = swindex.get_index_dailyindicator(indexes[i], start_date='1999-12-30',
                                                             end_date='2020-9-18', freq='D')
            # 设置dataframe列的顺序
            indicator = indicator[['avg_float_mv', 'date', 'dividend_yield_ratio', 'float_mv',
                                  'pb', 'pe', 'turn_rate', 'turnover_pct', 'vwap']]
            indicator.rename(columns={'date': 'trade_date'}, inplace=True)
            data.set_index('trade_date', inplace=True)
            indicator.set_index('trade_date', inplace=True)
            res = data.merge(indicator, left_index=True, right_index=True, how='left')
            res.rename(columns={'change_pct': 'chg_pct', 'turn_rate': 'turnover_rate',
                                'vwap': 'avg_price'}, inplace=True)
            res.to_sql(name=indexes[i] + '_daily', con=self.engine, schema='indexes', if_exists='append', index=True,
                       dtype={'trade_date': sa.DateTime()})
            self.engine.execute("alter table indexes.%s_daily add primary key(trade_date);" % indexes[i])
            print(indexes[i] + ' end')

    def get_fina_data(self, attrs: List[str] = None):
        """
        从tushare接口获取财务数据并存入mongoDB数据库中
        :return:
        """
        db = self.mongo_client['fina_db']
        self.pro = ts.pro_api()
        data = pro.stock_basic(list_status='L', exchange="SSE", fields='ts_code,symbol,name,list_date')
        # 设置起始位置
        # start_index = data['ts_code'].tolist().index('600593.SH')+1
        start_index = 0
        # 当表还未创建时，判断对应表是否已存在
        if attrs is None and 'fina_' + data['ts_code'][start_index][:6] in db.collection_names():
            print(data['ts_code'][start_index] + '已存在')
            return
        #
        for i in range(start_index, len(data)):
            code = data['ts_code'][i]
            #
            print(code + " start")
            if attrs is None:  # 向表中插入原始数据
                fina_data = pro.fina_indicator(ts_code=code)
                db['fina_' + code[:6]].insert_many(fina_data.to_dict(orient='record'))
            else:  # 向表中追加数据
                fina_data = pro.fina_indicator(ts_code=code, fields='end_date,' + ','.join(attrs))
                for j in range(len(fina_data)):
                    # print(fina_data.loc[j, fina_data.columns[1:]].to_dict())
                    db['fina_' + code[:6]].update(spec={"ts_code": code, "end_date": fina_data.loc[j, 'end_date']},
                                                  document={"$set": fina_data.loc[j, fina_data.columns[1:]].to_dict()})
            #
            print(code + " store completely")
            time.sleep(0.2)
        # self.mongo_client.close()

    def get_income_data(self):
        """
        调用tushare接口获取个股利润表数据存入mongoDB数据库中
        :return:
        """
        db = self.mongo_client['income_db']
        basic_data = self.pro.stock_basic(list_status='L', exchange='', fields='ts_code,symbol,name,list_date')
        #
        # start_index = 201
        start_index = basic_data['ts_code'].tolist().index('603693.SH') + 1
        # 判断对应表是否已存在
        if 'income_' + basic_data['ts_code'][start_index][:6] in db.collection_names():
            print(basic_data['ts_code'][start_index] + '已存在')
            return
        #
        for i in range(start_index, len(basic_data)):
            code = basic_data['ts_code'][i]
            print(code + ' start')
            #
            income_data = self.pro.income(ts_code=code)
            db['income_' + code[:6]].insert_many(income_data.to_dict(orient='record'))
            #
            print(code + ' stor completely')
            time.sleep(0.5)
        # self.mongo_client.close()

    def get_balance_data(self):
        """
        调用tushare接口获取资产负债表数据并存储到mongDB数据库中
        :return:
        """
        db = self.mongo_client['balance_db']
        basic_data = self.pro.stock_basic(list_status='L', exchange='', fields='ts_code,symbol,list_date')
        #
        # start_index = 801
        start_index = basic_data['ts_code'].tolist().index('688078.SH') + 1
        # 判断对应表是否已存在
        if 'balance_' + basic_data['ts_code'][start_index][:6] in db.collection_names():
            print(basic_data['ts_code'][start_index] + '已存在')
            return
        #
        for i in range(start_index, len(basic_data)):
            code = basic_data['ts_code'][i]
            print(code + ' start')
            #
            balance_data = pro.balancesheet(ts_code=code)
            db['balance_' + code[:6]].insert_many(balance_data.to_dict(orient='record'))
            #
            print(code + ' store completely')
            time.sleep(0.5)
        # self.mongo_client.close()

    def get_cashflow_data(self):
        """
        从tushare接口获取现金流量数据并存入mongoDB数据库中
        :return:
        """
        db = self.mongo_client['cashflow_db']
        basic_data = self.pro.stock_basic(list_status='L', exchange='', fields='ts_code,symbol,list_date')
        #
        # start_index = 1501
        start_index = basic_data['ts_code'].tolist().index('603333.SH') + 1
        # 判断对应表是否已存在
        if 'cashflow_' + basic_data['ts_code'][start_index][:6] in db.collection_names():
            print(basic_data['ts_code'][start_index] + '已存在')
            return
        #
        for i in range(start_index, len(basic_data)):
            code = basic_data['ts_code'][i]
            print(code + ' start')
            #
            cashflow_data = pro.cashflow(ts_code=code)
            db['cashflow_' + code[:6]].insert_many(cashflow_data.to_dict(orient='record'))
            #
            print(code + ' store completely')
            time.sleep(0.5)
        # self.mongo_client.close()

    def get_stock_k(self, code: str, start_date=None, freq='D'):
        """
        从tushare获取指定股票的k线数据并存入到Mysql数据库中，在原先数据的基础上添加每日指标数据
        :param code: 股票代码
        :param start_date: 数据的起始日期
        :param freq: 数据频率，'D','W','M','Y'分别表示日、周、月、年
        :return:
        """
        # table_name = code[:6] + '_' + fq_trans(freq)
        table_name = 'stock_daily'
        #
        df = ts.pro_bar(ts_code=code, start_date=start_date, adj='qfq', ma=[5, 10, 20, 30, 60, 120, 250],
                        factors=['tor', 'vr'], adjfactor=True)
        if df is None:
            return
        if freq == 'D':
            indicator_df = ts.pro_api().daily_basic(ts_code=code, start_date=start_date)
            # print(indicator_df.drop(['ts_code', 'close', 'turnover_rate', 'volume_ratio'], axis=1))
            if indicator_df is not None and len(indicator_df) > 0:
                df = pd.merge(left=df,
                              right=indicator_df.drop(['ts_code', 'close', 'turnover_rate', 'volume_ratio'], axis=1),
                              on='trade_date', how='left')
        # print(df.columns)
        df.to_sql(name=table_name, con=self.engine, schema='stock', if_exists='append', index=False,
                  dtype={'trade_date': sa.DateTime()})
        #
        # self.engine.execute("alter table stock.%s add primary key(trade_date);" % table_name)

    def get_index_k(self, code: str, start_date=None, freq='D'):
        """
        从tushare接口获取指定指数的k线数据并存入MySQL数据库中
        :param code: 指数代码
        :param start_date: 开始日期
        :param freq: 频率，同上
        :return:
        """
        table_name = code[:6] + '_' + fq_trans(freq)
        print(code + " start")
        #
        df = ts.pro_bar(ts_code=code, asset='I', ma=[5, 10, 20, 30, 60, 120, 250])
        df.to_sql(name=table_name, con=self.engine, schema='indexes', if_exists='replace', index=False,
                  dtype={'trade_date': sa.DateTime()})
        self.engine.execute("alter table indexes.%s add primary key(trade_date);" % table_name)
        #
        print(code + "store completely")

    def stock_dk(self):
        """
        从tushare获取股票代表，对每支股分别调用get_stock_k函数向数据库中存数据
        :return:
        """
        data = self.pro.stock_basic(list_status='L', exchange="SSE", fields='ts_code,symbol,name,list_date')
        #
        start_index = 1700
        # start_index = data['ts_code'].tolist().index('300936.SZ') + 1
        for i in range(start_index, start_index + 200):
            code = data['ts_code'][i]
            start_date = data['list_date'][i]
            print(code + " start")
            #
            start_date = datetime.datetime.strptime(start_date, "%Y%m%d")
            start_date += datetime.timedelta(days=1)
            start_date = start_date.strftime("%Y%m%d")
            self.get_stock_k(code, start_date)
            #
            print(code + " store completely")

    def index_dk(self):
        """
        指定要获取的指数列表，对每个指数分别调用get_index_k将数据存入数据库
        :return:
        """
        indexs = ['399300.SZ', '000009.SH', '000010.SH', '000016.SH', '399001.SZ', '399005.SZ', '399006.SZ', '399005.SZ',
                  '000852.SH', '000001.SH']
        for code in indexs:
            self.get_index_k(code)
        # self.get_index_k('000852.SH')

    def get_backup_dk(self):
        """
        从tushare接口获取个股其他的每日指标，包括市值、行业等数据存入MongoDB数据库
        :return:
        """
        db = self.mongo_client['backup_daily_db']
        basic_data = self.pro.stock_basic(list_status='L', exchange='', fields='ts_code,symbol,list_date')
        #
        # start_index = 0
        start_index = basic_data['ts_code'].tolist().index('603590.SH') + 1
        # 判断对应表是否已存在
        if 'backup_daily_' + basic_data['ts_code'][start_index][:6] in db.collection_names():
            print(basic_data['ts_code'][start_index] + '已存在')
            return
        #
        for i in range(start_index, start_index + 500):
            code = basic_data['ts_code'][i]
            print(code + ' start')
            #
            df = self.pro.bak_daily(ts_code=code)
            df = df[df.columns[15:]]
            db['backup_daily_' + code[:6]].insert_many(df.to_dict(orient='record'))
            #
            print(code + ' store completely')
            time.sleep(0.5)

    def export_data(self):
        tbl_list = self.mysql.query("show tables", return_type='np').flatten()
        file_path = PRO_PATH + '/data/moneyflow.txt'
        for tbl in tbl_list:
            query = "select * from moneyflow.%s" % tbl
            print(query)
            data = self.mysql.query(query)
            data.to_csv(file_path, index=False, header=False, mode='a')

    def moneyflow(self, index, index_name, codes, start_date=None, end_date=None):
        """
        从数据源获取股票指定日期范围内的资金流向数据
        :param index:
        :param index_name:
        :param codes:
        :param start_date:
        :param end_date:
        :return:
        """
        # 设置默认起止日期
        if start_date is None:
            start_date = '20200101'
        if end_date is None:
            end_date = '20200201'
        print(index_name + "start...")
        # 获取股票在指定日期范围内的资金流向数据并存到数据库moneyflow库中
        for code in codes:
            print(code + "start....")
            df = self.pro.moneyflow(ts_code=code, start_date=start_date, end_date=end_date)
            df.to_sql(name=code[:6], con=self.engine, schema='moneyflow', if_exists='append', index=False,
                      dtype={'trade_date': sa.DateTime()})
            # df.to_csv('./static/data/moneyflow/' + index + '/' + code[:6] + '.csv', mode='a', index=False)
            # df.to_json('./static/data/moneyflow/' + index + '/' + code[:6] + '.json',
            # orient='split', force_ascii=False)
            print(code + "complete")
        # data.to_csv('./static/data/moneyflow/' + index + '/' + index[:6] + '.csv', mode='a', index=False)
        # data.to_json('./static/data/moneyflow/' + index + '/' + index[:6] + '.json',
        # orient='split', force_ascii=False)
        # df_json = data.to_json(orient='split', force_ascii=False)
        # data.set_index(["trade_date"], inplace=True)
        # data["net_amount"] = data["buy_lg_amount"] - data["sell_lg_amount"] + \
        #                      data["buy_elg_amount"] - data["sell_elg_amount"]
        print(index_name + "complete")

    def swcodes(self, level, start=None, end=None):
        """
        获取申万行业指数，并计算其资金流向数据，计算方法方法是将其成分股的各项数据相加
        :param level: 申万指数等级，共分为3级
        :param start: 指定指数列表的起始位置
        :param end: 指定指数列表的结束位置
        :return:
        """
        index_list = self.pro.index_classify(level=level, src="SW")
        #
        if start is None:
            start = 0
        if end is None:
            end = len(index_list)
        #
        for i in range(start, end):
            index = index_list['index_code'][i]
            index_name = index_list['industry_name'][i]
            codes = pro.index_member(index_code=index)['con_code'].values
            # moneyflow(pro, index, index_name, codes)
            self.cal_sw_money(index, index_name, codes)

    def cal_sw_money(self, index, index_name, codes, start_date=None, end_date=None):
        """
        计算申万指数每天的大单及特大单的净流入，并存入数据库中
        :param index: 指数代码
        :param index_name: 指数名称
        :param codes: 指数成分股
        :param start_date: 开始日期
        :param end_date: 结束日期
        :return:
        """
        if start_date is None:
            start_date = '20200101'
        if end_date is None:
            end_date = '20200201'
        print(index_name + "start...")
        path = './static/data/moneyflow/' + index
        # if not os.path.exists(path):
        #     os.makedirs(path)
        columns = ['trade_date', 'sm_net_amount', 'md_net_amount', 'lg_net_amount', 'elg_net_amount',
                   'sm_net_vol', 'md_net_vol', 'lg_net_vol', 'elg_net_vol']
        features = ['trade_date', 'buy_sm_amount - sell_sm_amount as sm_net_amount',
                    'buy_md_amount - sell_md_amount as md_net_amount',
                    'buy_lg_amount - sell_lg_amount as lg_net_amount',
                    'buy_elg_amount - sell_elg_amount as elg_net_amount', 'buy_sm_vol - sell_sm_vol as sm_net_vol',
                    'buy_md_vol - sell_md_vol as md_net_vol', 'buy_lg_vol - sell_lg_vol as lg_net_vol',
                    'buy_elg_vol - sell_elg_vol as elg_net_vol']
        data = None
        for code in codes:
            # print(code + "start..")
            query = 'select %s from moneyflow.%s;' % (','.join(features), code[:6])
            tmp = self.mysql.query(query, return_type='np')
            for line in tmp:
                line[0] = line[0].strftime("%Y%m%d")
            df = pd.DataFrame(data=tmp, columns=columns)
            df.set_index('trade_date', inplace=True)
            # 将该个股的资金数据与总数据相加
            if data is None:
                data = df.copy()
            else:
                data = data.add(df, fill_value=0)
            # print(code + 'end')
        #
        data.to_sql(name=index[:6], con=self.engine, schema='sw_moneyflow', if_exists='append', index=True,
                    dtype={'trade_date': sa.DateTime()})
        self.engine.execute("alter table sw_moneyflow.%s add primary key(trade_date);" % index[:6])
        print(index_name + "end")

    def get_trade_cal(self):
        trade_cal = self.pro.trade_cal()
        print(trade_cal)
        trade_cal.to_sql(name='trade_cal', con=self.engine, schema='basic_info', if_exists='replace', index=True,
                         dtype={'cal_date': sa.DateTime()})

    def con_sw_tree(self):
        """
        构建申万三个等级行业的树状json数据
        :return:
        """
        l1 = self.pro.index_classify(level='L1', src='SW')
        l2 = self.pro.index_classify(level='L2', src='SW')
        l3 = self.pro.index_classify(level='L3', src='SW')

        stock_info = self.pro.stock_basic(exchange='', list_status='L', fields='ts_code, name')
        stock_info.set_index(["ts_code"], inplace=True)

        stock_unit = dict.fromkeys(['name', 'code', 'value'])
        index_unit = dict.fromkeys(['name', 'code', 'children'])

        root = index_unit.copy()
        root['name'] = 'root'
        root['code'] = None
        root['children'] = []

        # 文件格式 xxxxxx xxxxxx xxxxxx ... 每个指数为6个字符，第一个为父节点，之后的为子节点
        # lines1为一级与二级的数据， lines2为二级与三级的数据
        with open(PRO_PATH + '/data/swl1.txt') as f:
            lines1 = f.readlines()

        with open(PRO_PATH + '/data/swl2.txt') as f:
            lines2 = f.readlines()

        j = 0
        # 一级行业
        for line in lines1:
            codes = line.strip().split(' ')
            if len(codes) > 0:
                node = index_unit.copy()
                node['code'] = codes[0] + '.SI'
                node['name'] = l1[l1['index_code'] == node['code']]['industry_name'].values[0]
                node['children'] = []
                # 添加二级行业
                for i in range(1, len(codes)):
                    child = index_unit.copy()
                    child['code'] = codes[i] + '.SI'
                    child['name'] = l2[l2['index_code'] == child['code']]['industry_name'].values[0]
                    child['children'] = []
                    # 添加三级行业
                    line2 = lines2[j].strip().split(' ')
                    j = j + 1
                    if (line2[0] != child['code'][:6]) or len(line2) < 1:
                        print(line2[0] + ' error ' + child['code'][:6] + ' ' + str(len(line2)))
                        return
                    for k in range(1, len(line2)):
                        gchild = index_unit.copy()
                        gchild['code'] = line2[k] + '.SI'
                        print(gchild['code'])
                        gchild['name'] = l3[l3['index_code'] == gchild['code']]['industry_name'].values[0]
                        gchild['children'] = []
                        # 添加股票列表
                        slist = pro.index_member(index_code=gchild['code'])['con_code'].values
                        for scode in slist:
                            schild = stock_unit.copy()
                            schild['code'] = scode
                            try:
                                schild['name'] = stock_info.loc[scode].values[0]
                            except KeyError:
                                print(scode + 'key error')
                                continue
                            else:
                                gchild['children'].append(schild)
                        child['children'].append(gchild)
                    node['children'].append(child)
                root['children'].append(node)
        res = json.dumps(root, indent=1, ensure_ascii=False)
        # print(res)
        with open(PRO_PATH + '/data/sw.json', 'w') as f:
            f.write(res)

    @staticmethod
    def con_sw_map():
        """
        构建三级行业向二级行业的映射以及二级行业向一级行业的映射，并保存到本地文件中
        :return:
        """
        with open(PRO_PATH + '/data/swl1.txt') as f:
            lines1 = f.readlines()
        with open(PRO_PATH + '/data/swl2.txt') as f:
            lines2 = f.readlines()
        res = dict()
        for line in lines1:
            line = line[:-1].split(' ')
            for i in range(1, len(line)):
                res[line[i]] = line[0]
        for line in lines2:
            line = line[:-1].split(' ')
            for i in range(1, len(line)):
                res[line[i]] = line[0]
        res = json.dumps(res, indent=1, ensure_ascii=False)
        print(res)
        with open(PRO_PATH + '/data/sw_map.json', 'w') as f:
            f.write(res)


if __name__ == '__main__':
    # ts.set_token('92c6ece658c377bcc32995a68319cf01696e1266ed60be0ae0dd0947')
    # get_sw_index()
    # get_fina_data()
    # stock_dk()
    CollectData().get_trade_cal()
