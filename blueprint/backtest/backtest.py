from flask import Blueprint, request, render_template
import json
from .server import backtest

path = 'backtest'

backtest_bp = Blueprint(path, __name__, url_prefix='/'+path)


@backtest_bp.route('/')
def index():
    return render_template("backtest.html")


@backtest_bp.route("/run", methods=['GET', 'POST'])
def run():
    recv = request.get_data()
    if recv:
        recv = json.loads(str(recv, encoding='utf-8'))
        res = backtest(recv).return_metrics()
        return json.dumps({'metrics': res, 'status': 'success'})
    else:
        return json.dumps({'stauts': 'fail'})
