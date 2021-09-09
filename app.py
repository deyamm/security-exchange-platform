# -*- coding: utf-8 -*-
from flask import Flask, request
from flask import render_template
from flask_cors import CORS
import json
from server import Server
from blueprint import visualize, fetch_data

app = Flask(__name__)
CORS(app)
server = Server()

app.register_blueprint(visualize.quant)
app.register_blueprint(fetch_data.data)


@app.route('/')
def index():
    return render_template('index.html')
    # return 'index.html'


@app.route('/page_list.html')
def stragety_list_page():
    return render_template('page_list.html')


@app.route('/stock_list.html')
def stock_list_page():
    return render_template('stock_list.html')


@app.route('/fund_pick.html')
def fund_pick_page():
    return render_template('fund_pick.html')


@app.route('/stock_info.html')
def stock_info_page():
    return render_template('stock_info.html')


@app.route('/multi_indicator.html')
def multi_indicator_page():
    return render_template("multi_indicator.html")


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


@app.route("/backtest", methods=['GET', 'POST'])
def backtest():
    recv = request.get_data()
    if recv:
        recv = json.loads(str(recv, encoding='utf-8'))
        res = server.backtest(recv).return_metrics()
        return json.dumps({'metrics': res, 'status': 'success'})
    else:
        return json.dumps({'stauts': 'fail'})


@app.route('/multi_indicator/regression', methods=['GET', 'POST'])
def multi_indicator():
    recv = request.get_data()
    if recv:
        recv = json.loads(str(recv, encoding='utf-8'))
        return json.dumps({'status': 'succes'})
    else:
        return json.dumps({'status': 'fail'})


if __name__ == '__main__':
    app.run()
