from flask import Blueprint, request, render_template
import json
from pyfiles.com_lib.variables import *
from server import Server

path = 'stock_filter'

stock_filter = Blueprint(path, __name__, url_prefix='/'+path)

server = Server()


@stock_filter.route('/')
def index():
    return render_template("stock_list.html")


@stock_filter.route('/init', methods=['GET', 'POST'])
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


@stock_filter.route('/search', methods=['GET', 'POST'])
def stock_pick_search():
    recv = request.get_data()
    if recv:
        recv = json.loads(str(recv, encoding='utf-8'))
        res = server.sec_filter(recv['options'])
        return res.to_json(force_ascii=False, orient='records')
    else:
        return json.dumps({'status': 'fail'})
