from flask import Blueprint, request, render_template
import json
from pyfiles.com_lib.variables import *
import pandas as pd
from .server import *

path = 'visualize'

visualize_bp = Blueprint(path, __name__, url_prefix='/'+path)


@visualize_bp.route('/')
def quant_indicator_page():
    return render_template('visualize.html')


@visualize_bp.route('/init', methods=['GET', 'POST'])
def quant_init():
    recv = request.get_data()
    if recv:
        recv = json.loads(str(recv, encoding='utf-8'))
        res = dict()
        res['quantdata'] = get_quant_data()
        # res['heatmapdata'] = server.get_heatmap_data(is_save=True)
        with open(PRO_PATH + '/data/heatmap.json') as f:
            res['heatmapdata'] = json.load(f)
        res['scatterdata'] = res['heatmapdata']['scatter']
        del res['heatmapdata']['scatter']
        res['status'] = 'succses'
        # print(res)
        return json.dumps(res, ensure_ascii=False)
    else:
        return json.dumps({'status': 'fail'})


# @visualize.route('/bar.html')
# def show_bar():
#     return render_template('three.html')


@visualize_bp.route('/save_quantdata', methods=['GET', 'POST'])
def save_quantdata():
    recv = request.get_data()
    if recv:
        recv = json.loads(str(recv, encoding='utf-8'))['quant_data']
        del recv['index_data']
        # print(len(recv['quant_data']['trade_date']))
        # print(len(recv['quant_data']['indicator_value']))
        res = pd.DataFrame.from_dict(recv, orient='columns')
        res.to_csv(PRO_PATH+'/data/quant.csv', index=False)
        # print(res)
        return json.dumps({'status': 'succed'})
    else:
        return json.dumps({'status': 'fail'})
