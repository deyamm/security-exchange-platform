# -*- coding: utf-8 -*-
from flask import Flask, request, render_template
import json
from blueprint import *

app = Flask(__name__)
app.jinja_env.variable_start_string = '[['
app.jinja_env.variable_end_string = ']]'

app.register_blueprint(visualize.visualize_bp)
app.register_blueprint(fetch_data.fetch_data_bp)
app.register_blueprint(backtest.backtest_bp)
app.register_blueprint(stock_filter.stock_filter_bp)
app.register_blueprint(fund.fund_bp)


@app.route('/')
def index():
    return render_template('page_list.html')
    # return 'index.html'


# @app.route('/page_list.html')
# def stragety_list_page():
#     return render_template('page_list.html')


@app.route('/fund_analysis.html')
def fund_pick_page():
    return render_template('fund_analysis.html')


@app.route('/stock_info.html')
def stock_info_page():
    return render_template('stock_info.html')


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
