from flask import Blueprint, request, render_template
import json
from pyfiles.com_lib.variables import *
from server import Server

path = 'visualize'

visualize = Blueprint(path, __name__, url_prefix='/'+path)

server = Server()


@visualize.route('/init', methods=['GET', 'POST'])
def quant_init():
    recv = request.get_data()
    if recv:
        recv = json.loads(str(recv, encoding='utf-8'))
        res = dict()
        res['quant_data'] = server.get_quant_data()
        # res['heatmap_data'] = server.get_heatmap_data()
        with open(PRO_PATH + '/data/heatmap.json') as f:
            res['heatmap_data'] = json.load(f)
        res['status'] = 'succses'
        # print(res)
        return json.dumps(res, ensure_ascii=False)
    else:
        return json.dumps({'status': 'fail'})


@visualize.route('/')
def quant_indicator_page():
    return render_template('visualize.html')


@visualize.route('/bar.html')
def show_bar():
    return render_template('three.html')
