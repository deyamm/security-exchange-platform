from flask import Blueprint, request
import json
from server import Server

quant = Blueprint('quant', __name__, url_prefix='/quant')

server = Server()


@quant.route('/init', methods=['GET', 'POST'])
def quant_init():
    recv = request.get_data()
    if recv:
        recv = json.loads(str(recv, encoding='utf-8'))
        res = server.get_quant_data()
        res['status'] = 'succses'
        # print(res)
        return json.dumps(res, ensure_ascii=False)
    else:
        return json.dumps({'status': 'fail'})


@quant.route('/index.html')
def quant_indicator_page():
    return render_template('quant_indicator.html')