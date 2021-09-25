/**
 * echarts k线图
 * @param data，
 * @returns
 */
function getKlineOption(data) {
    let dates = data['date'];
    let kdata = data['kdata'];
    let volumes = data['volumes'];
    let downColor = '#00da3c';
    let upColor = '#ec0000';
    return {
        animation: false,
        legend: { // 图例
            data: ['日k', 'MA5', 'MA10', 'MA20', 'MA30'],
            inactiveColor: '#777',
        },
        tooltip: { // 指示线
            trigger: 'axis',
            axisPointer: {
                animation: false,
                type: 'cross',
                lineStyle: {
                    color: '#376df4',
                    width: 2,
                    opacity: 1
                }
            },
            formatter: function (params) {
                let kparam = params[0];
                //console.log(params);
                return [
                    '日期： ' + kparam.name + '<hr size=1 style="margin: 3px 0">',
                    '开盘价：' + kparam.data[1] + '<br/>',
                    '收盘价：' + kparam.data[2] + '<br/>',
                    '最低价： ' + kparam.data[3] + '<br/>',
                    '最高价： ' + kparam.data[4] + '<hr size=1 style="margin: 3px 0">',
                    'MA5： ' + params[1].data + '<br/>',
                    'MA10： ' + params[2].data + '<br/>',
                    'MA20： ' + params[3].data + '<br/>',
                    'MA30： ' + params[4].data + '<hr size=1 style="margin: 3px 0">',
                    '交易量： ' + params[5].data[1] + '<br/>'
                ].join('');
            }
        },
        axisPointer: { //数据显示面板
            link: {
                xAxisIndex: 'all'
            },
            label: {
                backgroundColor: '#777'
            }
        },
        toolbox: { //工具箱
            feature: {
                dataZoom: {
                    yAxisIndex: false
                },
                brush: {
                    type: ['lineX', 'clear']
                }
            }
        },
        brush: {
            xAxisIndex: 'all',
            brushLink: 'all',
            outOfBrush: {
                colorAlpha: 0.1
            }
        },
        visualMap: {
            show: false,
            seriesIndex: 5,
            dimension: 2,
            pieces: [{
                value: 1,
                color: upColor
            }, {
                value: -1,
                color: downColor
            }]
        },
        grid: [
            {
                left: '10%',
                right: '8%',
                height: '50%'
            },
            {
                left: '10%',
                right: '8%',
                top: '63%',
                height: '16%'
            }
        ],
        xAxis: [
            {
                type: 'category',
                data: dates,
                scale: true,
                boundaryGap: false,
                axisLine: {
                    onZero: false,
                    lineStyle: {
                        color: '#8392A5'
                    }
                },
                splitLine: {
                    show: false
                },
                splitNumber: 20,
                min: 'dataMin',
                max: 'dataMax',
                axisPointer: {
                    z: 100
                }
            },
            {
                type: 'category',
                gridIndex: 1,
                data: dates,
                scale: true,
                boundaryGap: false,
                axisLine: {
                    onZero: false
                },
                axisTick: {
                    show: false
                },
                splitLine: {
                    show: false
                },
                axisLabel: {
                    show: false
                },
                splitNumber: 20,
                min: 'dataMin',
                max: 'dataMax'
            }
        ],
        yAxis: [
            {
                scale: true,
                splitArea: {
                    show: true
                }
            },
            {
                scale: true,
                gridIndex: 1,
                splitNumber: 2,
                axisLabel: {
                    show: false
                },
                axisLine: {
                    show: false
                },
                axisTick: {
                    show: false
                },
                splitLine: {
                    show: false
                }
            }
        ],
        dataZoom: [
            {
                type: 'inside',
                xAxisIndex: [0, 1],
                start: 0,
                end: 100
            },
            {
                show: true,
                xAxisIndex: [0, 1],
                type: 'slider',
                top: '85%',
                start: 0,
                end: 100
            }
        ],
        series: [
            {
                type: 'candlestick',
                name: '日k',
                data: kdata,
                itemStyle: {
                    color: upColor,
                    color0: downColor,
                    borderColor: null,
                    borderColor0: null
                },
            },
            {
                name: 'MA5',
                type: 'line',
                data: data['ma5'],
                smooth: true,
                showSymbol: false,
                lineStyle: {
                    width: 1,
                    opacity: 0.5
                }
            },
            {
                name: 'MA10',
                type: 'line',
                data: data['ma10'],
                smooth: true,
                showSymbol: false,
                lineStyle: {
                    width: 1,
                    opacity: 0.5
                }
            },
            {
                name: 'MA20',
                type: 'line',
                data: data['ma20'],
                smooth: true,
                showSymbol: false,
                lineStyle: {
                    width: 1,
                    opacity: 0.5
                }
            },
            {
                name: 'MA30',
                type: 'line',
                data: data['ma30'],
                smooth: true,
                showSymbol: false,
                lineStyle: {
                    width: 1,
                    opacity: 0.5
                }
            },
            {
                name: "Volume",
                type: 'bar',
                xAxisIndex: 1,
                yAxisIndex: 1,
                data: volumes
            }
        ]
    };
}

/**
 * 申万一级行业涨跌幅热力图
 * 数据格式：x轴：日期数组；y轴：行业数组，
 * 涨跌幅数据：3*n数组
 * @param data
 */
function getHeatmapOption(data) {
    let horizon = data['trade_date'];
    let vertical = data['industry'];
    let heatmapData = data['heatmap'];
    return {
        tooltip: {
            position: 'top',
            formatter: function (params) {
                //console.log(params['data']);
                let cell = params['data'];
                return [
                    '行业： ' + vertical[cell[1]] + '<br>',
                    '日期： ' + horizon[cell[0]] + '<br>',
                    '涨跌幅： ' + cell[2] + '<br>'
                ].join('');
            }
        },
        grid: {
            height: '80%',
            top: '5%'
        },
        xAxis: {
            type: 'category',
            data: horizon,
            splitArea: {
                show: true
            }
        },
        yAxis: {
            type: 'category',
            data: vertical,
            splitArea: {
                show: true
            }
        },
        visualMap: {
            min: -10,
            max: 10,
            calculable: true,
            orient: 'horizontal',
            left: 'center',
            bottom: '5%',
            inRange: {
                color: ['rgba(0, 0, 255, 1)', 'rgba(255, 255, 255, 1)', 'rgba(255, 0, 0, 1)']
            }
        },
        series: [{
            name: '申万一级行业涨幅热力图',
            type: 'heatmap',
            data: heatmapData,
            label: {
                //show: true
            },
            emphasis: {
                itemStyle: {
                    shadowBlur: 100,
                    shadowColor: 'rgba(0, 0, 0, 0.5)'
                }
            }
        }]
    };
}

/**
 * 多空因子图、柱状及折线图
 * @param data: object，data['trade_date']: 日期，只包括交易日
 *                      data['indicator_value']: 多空因子值
 *                      data['index_value']: 基准指数收盘人价
 * @returns
 */
function getQuantOption(data) {
    return {
        tooltip: {
            trigger: 'axis',
            axisPointer: {
                type: 'cross',
                crossStyle: {
                    color: '#999'
                }
            }
        },
        toolbox: {
            feature: {
                dataView: {
                    show: true,
                    readOnly: false
                },
                magicType: {
                    show: true,
                    type: ['line', 'bar']
                },
                restore: {
                    show: true
                },
                saveAsImage: {
                    show: true
                }
            }
        },
        legend: {
            data: ['多空因子', '沪深300']
        },
        xAxis: [
            {
                type: 'category',
                data: data['trade_date'],
                axisPointer: {
                    type: 'shadow'
                }
            }
        ],
        yAxis: [
            {
                type: 'value',
                name: '多空因子',
                scale: true,
                min: -30,
                max: 30,
                interval: 10,

            },
            {
                type: 'value',
                name: '沪深300',
                scale: true,
                splitLine: {
                    show: false
                }
            }
        ],
        series: [
            {
                name: '多空因子',
                type: 'bar',
                data: data['indicator_value'],
                markLine: {
                    symbol: 'none',
                    data: [
                        {
                            silent: true,
                            lineStyle: {
                                type: 'solid',
                                color: '#3398DB'
                            },
                            yAxis: -20
                        },
                        {
                            silent: true,
                            lineStyle: {
                                type: 'solid',
                                color: '#FA3934'
                            },
                            yAxis: -26
                        }
                    ]
                }
            },
            {
                name: '沪深300',
                type: 'line',
                yAxisIndex: 1,
                data: data['index_data']
            }
        ]
    };
}

export {getKlineOption, getHeatmapOption, getQuantOption};
