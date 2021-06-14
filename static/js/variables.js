/**
 * 全局变量文件
 */

/**
 * 股票排列方式，分为详细列表LIST_LARGE，简单列表LIST_SMALL
 * @type {string}
 */
let LIST_LARGE = "1";
let LIST_SMALL = "2";

let stockPoolTree = {
    'broad_index': {
        'name': '交易所指数',
        '000001.SH': '上证指数',
        '399001.SZ': '深证指数',
        '399005.SZ': '中小板指',
        '399006.SZ': '创业板指',
        '000016.SH': '上证50',
        '399300.SZ': '沪深300',
        '000905.SH': '中证500',
        '000852.SH': '中证1000'
    },
    'sw_index': {
        'name': '申万指数',
        '801010': '农林牧渔',
        '801020': '采掘',
        '801030': '化工',
        '801040': '钢铁'
    },
};

let indicatorTree = {
    'fina_indicator': {
        'name': '财务指标',
        'eps': {
            'name': '基本每股收益'
        },
        'roe': {
            'name': '净资产收益率'
        },
        'revenue_ps': {
            'name': '每股营业收入'
        },
        'ebit_of_gr': {
            'name': '息税前利润/营业总收入'
        },
        'fcff_ps': {
            'name': '每股企业自由现金流量'
        }
    },
    'tech_indicator': {
        'name': '技术指标',
        'ma': {
            'name': '均线',
            'ma5': '5日均线',
            'ma10': '10日均线',
            'ma20': '20日均线',
            'ma30': '30日均线',
            'ma60': '60日均线',
            'ma120': '120日均线',
            'ma250': '250日均线'
        },
        'captial': {
            'name': '资金流入'
        },
        'MACD': {
            'name': 'MACD'
        },
        'KDJ': {
            'name': 'KDJ'
        },
        'RSI': {
            'name': 'RSI'
        }
    },
    'daily_indicator': {
        'name': '每日指标',
        'total_mv': {
            'name': '总市值'
        },
        'circ_mv': {
            'name': '流通市值'
        },
        'volume_ratio': {
            'name': '量比'
        }

    }
};

export {
    LIST_LARGE, LIST_SMALL,
    stockPoolTree, indicatorTree
};