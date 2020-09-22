function drawLine(eleId) {
    var profitLine = echarts.init(document.getElementById(eleId));
    var config = {

    };
    var option = null;
    var text = [];
    $.ajax({
        url: '/data/profit_line',
        type: "POST",
        data: JSON.stringify(config),
        dataType: "json",
        async: false,
        success: function (data) {
            console.log(data);
            option = {
                //图例
                legend: {
                    data: ['收益率', '基准收益率'],
                    inactiveColor: '#777',
                    textStyle: {
                        color: '#000'
                    }
                },
                // 提示框
                tooltip: {
                    trigger: 'axis',
                    position: function (pt) {
                        return [pt[0], '10%'];
                    }
                },
                // 标题
                title: {
                    left: 'left',
                    text: '回测曲线'
                },
                // 工具箱
                toolbox: {
                    feature: {
                        dataZoom: {
                            yAxisIndex: 'none'
                        },
                        restore: {},
                        saveAsImage: {}
                    }
                },
                // x轴
                xAxis: {
                    type: 'category',
                    boundaryGap: false, // 坐标轴留白
                    data: data['trade_date']
                },
                // y轴
                yAxis: {
                    type: 'value',
                    boundaryGap: [0, '100%']
                },
                // 缩放工具
                dataZoom: [{
                    type: 'inside',
                    start: 0,
                    end: 100
                }, {
                    start: 0,
                    end: 100,
                    handleIcon: 'M10.7,11.9v-1.3H9.3v1.3c-4.9,0.3-8.8,4.4-8.8,9.4c0,5,3.9,' +
                        '9.1,8.8,9.4v1.3h1.3v-1.3c4.9-0.3,8.8-4.4,8.8-9.4C19.5,16.3,15.6,' +
                        '12.2,10.7,11.9z M13.3,24.4H6.7V23h6.6V24.4z M13.3,19.6H6.7v-1.4h6.6V19.6z',
                    handleSize: '100%',
                    handleStyle: {
                        color: '#fff',
                        shadowBlur: 3,
                        shadowColor: 'rgba(0, 0, 0, 0.6)',
                        shadowOffsetX: 2,
                        shadowOffsetY: 2
                    }
                }],
                graphic: [],
                series: [
                    {
                        name: '收益率',
                        type: 'line',
                        smooth: true,
                        sampling: 'average',
                        itemStyle: {
                            color: 'rgb(255, 70, 131)',
                        },
                        /*
                        areaStyle: {
                            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{
                                offset: 0,
                                color: 'rgb(255, 158, 68)'
                            }, {
                                offset: 1,
                                color: 'rgb(255, 70, 131)'
                            }])
                        },

                         */
                        data: data['profit_line']
                    },
                    {
                        name: '基准收益率',
                        type: 'line',
                        smooth: true,
                        sampling: 'average',
                        itemStyle: {
                            color: '#0938f7',
                        },
                        /*
                        areaStyle: {
                            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{
                                offset: 0,
                                color: '#11c2ee'
                            }, {
                                offset: 1,
                                color: '#0938f7'
                            }])
                        },
                         */
                        data: data['basic_profit_line']
                    }
                ]
            };
            text = ["收益率 "+data['profit_line'][data['profit_line'].length-1]+"%"];
            text.push("基准收益率 "+data['basic_profit_line'][data['basic_profit_line'].length-1]+"%");
            text.push("夏普比率 "+data['sharpe_ratio']);
            text.push("最大回撤 "+data['max_drawdown']+"%");
        }
    });
    renderText(profitLine, option, text);
    profitLine.setOption(option);
    return option;
}

function renderText(chart, option, text){
    function getTextGraphic(x, y, text, color, textAlign, fontSize){
        var style = {
            text: text,
            color: color,
            textAlign: textAlign,
            fontSize: fontSize,
            x: x,
            y: y
        };
        return {
            type: "text",
            style: style
        };
    }
    function setGraphicToGroup(group, graphic){
        group.children.push(graphic);
    }
    var zr = chart.getZr();
    var x = zr.getWidth();
    var y = zr.getHeight();
    var group = {
        type: 'group',
        children: []
    };
    setGraphicToGroup(group, getTextGraphic(x * 0.2, y * 0.05, text[0], '#333', 'center', 16));
    setGraphicToGroup(group, getTextGraphic(x * 0.4, y * 0.05, text[1], '#333', 'center', 16));
    setGraphicToGroup(group, getTextGraphic(x * 0.6, y * 0.05, text[2], '#333', 'center', 16));
    setGraphicToGroup(group, getTextGraphic(x * 0.8, y * 0.05, text[3], '#333', 'center', 16));
    var graphicArr = [];
    graphicArr.push(group);
    option.graphic = graphicArr;
}