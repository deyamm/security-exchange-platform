from flask import Blueprint, request, render_template
import json
from pyfiles.com_lib.variables import *
from .server import *

path = 'fund'

fund_bp = Blueprint(path, __name__, url_prefix='/'+path)


@fund_bp.route('/analysis.html')
def index():
    return render_template("fund_analysis.html")


@fund_bp.route('/search_fund', methods=['GET', 'POST'])
def search_fund():
    recv = request.get_data()
    if recv:
        recv = json.loads(str(recv, encoding='utf-8'))
        res = search_fund(recv['code'], recv['decided'])
        # print(res)
        return json.dumps(res)
    else:
        return json.dumps({'status': 'fail'})


@fund_bp.route('/save_holded_fund', methods=['GET', 'POST'])
def save_holded_fund():
    recv = request.get_data()
    if recv:
        recv = json.loads(str(recv, encoding='utf-8'))
        with open(PRO_PATH + '/data/holded_fund.json', 'w') as f:
            json.dump(recv, f, ensure_ascii=False, indent=1)
        # print(recv)
        return json.dumps({'status': 1})
    else:
        return json.dumps({'status': 0})


@fund_bp.route('/load_holded_fund', methods=['GET', 'POST'])
def load_holded_fund():
    recv = request.get_data()
    if recv:
        recv = json.loads(str(recv, encoding='utf-8'))
        with open(PRO_PATH + '/data/holded_fund.json', 'r') as f:
            holded_fund = json.load(f)
        return json.dumps(holded_fund, ensure_ascii=False, indent=1)
    else:
        return json.dumps({'status': 0})


@fund_bp.route('/analyse', methods=['GET', 'POST'])
def analyse():
    recv = request.get_data()
    if recv:
        recv = json.loads(str(recv, encoding='utf-8'))
        res = analyse_fund(recv['funds'])
        # print(json.dumps(res, ensure_ascii=False, indent=1))
        return json.dumps(res, ensure_ascii=False, indent=1)
    else:
        return json.dumps({'status': 0})
