/**
 * 绘制k线图，从服务器接收[日期，开盘价，收盘价，最高价，最低价]作为基础k线图，其中日期可以独立出来
 * 作为可选项，向服务器发送的请求中包含需要绘制的均线种类，由服务器计算并返回到前端。
 */

function getKLineOption() {
    var config = {};
    config['sec_code'] = '000001.SZ';
    var option = null;
    var volume = [];
    $.ajax({
        url: "/data/kline",
        type: "POST",
        data: JSON.stringify(config),
        dataType: "json",
        async: false,
        success: function (data) {
            console.log(data);
            for(var i = 0; i < data['volume'].length; i++){
                volume.push([i, data['volume'][i], data['kdata'][i][1] > data['kdata'][i][0] ? 1 : -1]);
            }
            option = {
                backgroundColor: '#21202D',
                // 图例
                legend: {
                    data: ['日K', 'MA5', 'MA10', 'MA20', 'MA30'],
                    inactiveColor: '#777',
                    textStyle: {
                        color: '#fff'
                    }
                },
                // 提示框
                tooltip: {
                    trigger: 'axis',
                    axisPointer: {
                        animation: false,
                        type: 'cross',
                        lineStyle: {
                            color: '#376df4',
                            width: 2,
                            opacity: 1
                        }
                    }
                },
                // 将两个图的提示框合并
                axisPointer: {
                    link: {
                        xAxisIndex: 'all'
                    }
                },
                // x轴
                xAxis: [
                    {
                        type: 'category',
                        data: data['date'],
                        axisLine: {
                            lineStyle: {
                                color: '#8392A5'
                            }
                        }
                    },
                    {
                        type: 'category',
                        data: data['date'],
                        gridIndex: 1,
                        axisLine: {
                            lineStyle: {
                                color: '#8392A5'
                            }
                        },
                        axisTick: {
                            show: false
                        },
                        axisLabel: {
                            show: false
                        }
                    }
                ],
                // y轴
                yAxis: [
                    {
                        scale: true,
                        axisLine: {
                            lineStyle: {
                                color: '#8392A5'
                            }
                        },
                        splitLine: {
                            show: false
                        }
                    },
                    {
                        scale: true,
                        gridIndex: 1,
                        axisLine: {
                            lineStyle: {
                                color: '#8392A5'
                            }
                        },
                        axisLabel: {
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
                visualMap: {
                    show: false,
                    seriesIndex: 5,
                    dimension: 2,
                    pieces: [{
                        value: 1,
                        color: '#ec0000'
                    },{
                        value: -1,
                        color: '#00da3c'
                    }]
                },
                // 图形距边界距离，划分出不同的区域来同时显示不同的图
                grid: [
                    {
                        bottom: '20%'
                    },
                    {
                        height: '10%',
                        bottom: '7%'
                    }

                ],
                // 缩放条
                dataZoom: [{
                    textStyle: {
                        color: '#8392A5'
                    },
                    handleIcon: 'M10.7,11.9v-1.3H9.3v1.3c-4.9,0.3-8.8,4.4-8.8,9.4c0,5,3.9,9.1,8.8,' +
                        '9.4v1.3h1.3v-1.3c4.9-0.3,8.8-4.4,8.8-9.4C19.5,16.3,15.6,12.2,10.7,11.9z ' +
                        'M13.3,24.4H6.7V23h6.6V24.4z M13.3,19.6H6.7v-1.4h6.6V19.6z\'',
                    handleSize: '80%',
                    dataBackground: {
                        areaStyle: {
                            color: '#8392A5'
                        },
                        lineStyle: {
                            opacity: 0.8,
                            color: '#8392A5'
                        }
                    },
                    handleStyle: {
                        color: '#fff',
                        shadowBlur: 3,
                        shadowColor: '#rgba(0, 0, 0, 0.6)',
                        shadowOffsetX: 2,
                        shadowOffsetY: 2
                    },
                    xAxisIndex: [0, 1]
                }, {
                    type: 'inside',
                    xAxisIndex: [0, 1]
                }],
                animation: false,
                series: [
                    {
                        type: 'candlestick',
                        name: '日K',
                        data: data['kdata'],
                        itemStyle: {
                            color: '#FD1050',
                            color0: '#0CF49B',
                            borderColor: '#FD1050',
                            borderColor0: '#0CF49B'
                        }
                    },
                    {
                        name: 'MA5',
                        type: 'line',
                        data: data['ma5'],
                        smooth: true,
                        showSymbol: false,
                        lineStyle: {
                            width: 1
                        }
                    },
                    {
                        name: 'MA10',
                        type: 'line',
                        data: data['ma10'],
                        smooth: true,
                        showSymbol: false,
                        lineStyle: {
                            width: 1
                        }
                    },
                    {
                        name: 'MA20',
                        type: 'line',
                        data: data['ma20'],
                        smooth: true,
                        showSymbol: false,
                        lineStyle: {
                            width: 1
                        }
                    },
                    {
                        name: 'MA30',
                        type: 'line',
                        data: data['ma30'],
                        smooth: true,
                        showSymbol: false,
                        lineStyle: {
                            width: 1
                        }
                    },
                    {
                        name: 'Volume',
                        type: 'bar',
                        xAxisIndex: 1,
                        yAxisIndex: 1,
                        data: volume
                    }
                ]
            };
        }
    });
    return option;
}

