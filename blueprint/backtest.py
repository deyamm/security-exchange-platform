from flask import Blueprint, request, render_template
import json
from pyfiles.com_lib.variables import *
from server import Server

path = 'backtest'

backtest = Blueprint(path, __name__, url_prefix='/'+path)

server = Server()


@backtest.route('/')
def index():
    return render_template("backtest.html")


@backtest.route("/run", methods=['GET', 'POST'])
def run():
    recv = request.get_data()
    if recv:
        recv = json.loads(str(recv, encoding='utf-8'))
        res = server.backtest(recv).return_metrics()
        return json.dumps({'metrics': res, 'status': 'success'})
    else:
        return json.dumps({'stauts': 'fail'})
