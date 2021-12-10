from ..share import *


def search_fund(code, decided):
    # print(code)
    fund_basic = basic_info.fund_basic
    if decided is False:
        searched_list = fund_basic[fund_basic.ts_code.str.startswith(code)]
        # print(len(searched_list['ts_code']))
        return searched_list.set_index('ts_code')['name'][:20].to_dict()
    else:
        searched_fund = fund_basic[fund_basic['ts_code'] == code].fillna('null').to_dict(orient='records')[0]
        return searched_fund


def analyse_fund(fund_list):
    fund_portfolio = data_client.get_funds_portfolio(fund_list=fund_list)
    return fund_portfolio
