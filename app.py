# -*- coding: utf-8 -*-
from flask import Flask, request
from flask import render_template
import json
from server import Server

app = Flask(__name__)

server = Server()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/stragety_list.html')
def stragety_list_page():
    return render_template('stragety_list.html')


@app.route('/stock_list.html')
def stock_list_page():
    return render_template('stock_list.html')


@app.route('/fund_pick.html')
def fund_pick_page():
    return render_template('fund_pick.html')


@app.route('/stock_info.html')
def stock_info_page():
    return render_template('stock_info.html')


@app.route('/quant_indicator.html')
def quant_indicator_page():
    return render_template('quant_indicator.html')


@app.route('/quant/init', methods=['GET', 'POST'])
def quant_init():
    recv = request.get_data()
    if recv:
        recv = json.loads(str(recv, encoding='utf-8'))
        res = server.get_quant_data()
        res['status'] = 'succses'
        # print(res)
        return json.dumps(res, ensure_ascii=False)
    else:
        return json.dumps({'status': 'fail'})


@app.route('/stock_pick/init', methods=['GET', 'POST'])
def stock_pick_init():
    recv = request.get_data()
    if recv:
        recv = json.loads(str(recv, encoding='utf-8'))
        res = server.get_fina_data(recv['sec_codes'])
        # print(res)
        # print(res.to_json(force_ascii=False, orient='records'))
        return res.to_json(force_ascii=False, orient='records')
    else:
        return json.dumps({'status': 'fail'})


@app.route('/stock_pick/search', methods=['GET', 'POST'])
def stock_pick_search():
    recv = request.get_data()
    if recv:
        recv = json.loads(str(recv, encoding='utf-8'))
        res = server.sec_filter(recv['options'])
        return res.to_json(force_ascii=False, orient='records')
    else:
        return json.dumps({'status': 'fail'})


@app.route('/data/kline', methods=['GET', 'POST'])
def get_k_data():
    recv = request.get_data()
    if recv:
        recv = json.loads(str(recv, encoding='utf-8'))
        res = server.k_data(recv['sec_code'])
        return json.dumps(res, indent=1, ensure_ascii=False)
    else:
        return json.dumps({'status': 'fail'})


@app.route('/data/profit_line', methods=['GET', 'POST'])
def get_profit_line():
    recv = request.get_data()
    if recv:
        recv = json.loads(str(recv, encoding='utf-8'))
        # print(recv)
        res = server.get_profit_line()
        return json.dumps(res, indent=1, ensure_ascii=False)
    else:
        return json.dumps({'status': 'fail'})


if __name__ == '__main__':
    app.run()
