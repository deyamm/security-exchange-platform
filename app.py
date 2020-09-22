# -*- coding: utf-8 -*-
from flask import Flask, request
from flask import render_template
import json
import server

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


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
