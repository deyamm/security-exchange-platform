from flask import Blueprint, request
from .server import *
import json

fetch_data_bp = Blueprint('data', __name__, url_prefix='/data')


@fetch_data_bp.route('/profit_line', methods=['GET', 'POST'])
def get_profit_line():
    recv = request.get_data()
    if recv:
        recv = json.loads(str(recv, encoding='utf-8'))
        # print(recv)
        res = get_profit_line()
        return json.dumps(res, indent=1, ensure_ascii=False)
    else:
        return json.dumps({'status': 'fail'})


@fetch_data_bp.route('/sec_pool', methods=['GET', 'POST'])
def get_secs():
    recv = request.get_data()
    if recv:
        recv = json.loads(str(recv, encoding='utf-8'))
        print(recv)
        res = get_sec_pool(recv['pool_list'])
        return res.to_json(force_ascii=False, orient='records')
    else:
        return json.dumps({'status': 'fail'})


@fetch_data_bp.route('/kline', methods=['GET', 'POST'])
def get_k_data():
    recv = request.get_data()
    if recv:
        recv = json.loads(str(recv, encoding='utf-8'))
        res = k_data(recv['sec_code'])
        return json.dumps(res, indent=1, ensure_ascii=False)
    else:
        return json.dumps({'status': 'fail'})
