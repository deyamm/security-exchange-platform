function getKlineOption(data) {
    let dates = data['date'];
    let kdata = data['kdata'];
    let volumes = data['volumes'];
    let option = {
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
    return option;
}

export {getKlineOption};
