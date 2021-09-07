import {addLiEvent, addDropdownBtnEvent} from "./events.js";
import {removeChild} from "./functions.js";

function StockUnit(stockData) {
    this.stockData = stockData;
    // 为每支个股unit分配相应的id
    this.unitId = "stock-unit-" + this.stockData['ts_code'].substring(0, 6);
    // 存储在复选框中被选中的选项，并在重新绘制复选框时提供初始选项
    this.selectedIndicator = {'roe': 1, 'bps': 1};
    let indicatorDict = new IndicatorDict();

    StockUnit.prototype.createPanel = function () {
        //在stock-unit外再套一层容器用于bootstrap风格布局
        let container = document.createElement("div");
        $(container).addClass("col-sm-3 stock-ctn");
        $(container).css("padding", "5px");
        let unit = document.createElement("div");
        $(unit).attr("id", this.unitId);
        unit.self = this;
        $(unit).addClass("stock-unit-lg");
        $(unit).append(new StockInfo(this.stockData['ts_code'], this.stockData['name'], this.stockData['close']).createPanel());
        let indicators = this.getSelectedIndicator();
        for (let i = 0; i < indicators.length; i++) {
            $(unit).append(new Indicator(indicatorDict.getIndicatorName(indicators[i]), this.stockData[indicators[i]]).createPanel());
        }
        let dropdownBtn = document.createElement("button");
        addDropdownBtnEvent(dropdownBtn);
        $(dropdownBtn).attr("id", "dropdown-btn-" + this.stockData["ts_code"].substring(0, 6));
        $(dropdownBtn).addClass("glyphicon glyphicon-chevron-down dropdown-btns");
        $(unit).append(dropdownBtn);
        $(container).append(unit);
        return container;
    };

    StockUnit.prototype.updateIndicator = function (indicators, indicatorName) {
        //console.log(indicatorName);
        let unit = document.getElementById(this.unitId);
        this.selectedIndicator = indicators;
        // 先将原有指标删除
        removeChild(this.unitId, "indicator-div");
        for (let key in indicators) {
            if (indicators.hasOwnProperty(key) && indicators[key] === 1) {
                //console.log(key + " " + indicators[key]);
                $(unit).append(new Indicator(indicatorName[key], this.stockData[key]).createPanel());
            }
        }
    };

    StockUnit.prototype.getSelectedIndicator = function () {
        let selectedIndicator = [];
        for (let key in this.selectedIndicator) {
            if (this.selectedIndicator.hasOwnProperty(key) && this.selectedIndicator[key] === 1) {
                selectedIndicator.push(key);
            }
        }
        //console.log(selectedIndicator);
        return selectedIndicator;
    };

    StockUnit.prototype.resetButtonStatus = function (selectedId) {
        let buttons = document.getElementsByClassName("dropdown-btns");
        //console.log(buttons);
        removeChild("dropdown-div");
        for (let i = 0; i < buttons.length; i++) {
            $(buttons[i]).removeClass("glyphicon-chevron-up");
            $(buttons[i]).addClass("glyphicon-chevron-down");
            $(buttons[i]).prop("status", 0);
        }
        let selectedB = document.getElementById(selectedId);
        $(selectedB).removeClass("glyphicon-chevron-down");
        $(selectedB).addClass("glyphicon-chevron-up");
        $(selectedB).prop("status", 1);
    }
}

function DropdownCheckbox(indicators, targetId, parentId) {
    /**
     * 下拉复选框，用于选择显示的财务指标等数据
     */
    this.listData = {
        'current_ratio': '流动比率',
        'quick_ratio': '速动比率',
        'ca_turn': '流动资产周转率',
        'assets_turn': '总资产周转率',
        'debt_to_assets': '资产负债率',
        'netprofit_margin': '销售净利率',
        'grossprofit_margin': '销售毛利率',
        'npta': '总资产净利率',
        'roe': '净资产收益率',
        'eps': '每股收益',
        'pe': '市盈率',
        'bps': '每股净资产',
        'pb': '市净率'
    };
    this.listStates = {
        'current_ratio': 0,
        'quick_ratio': 0,
        'ca_turn': 0,
        'assets_turn': 0,
        'debt_to_assets': 0,
        'netprofit_margin': 0,
        'grossprofit_margin': 0,
        'npta': 0,
        'roe': 0,
        'eps': 0,
        'pe': 0,
        'bps': 0,
        'pb': 0
    };
    this.target = document.getElementById(targetId);
    this.parent = document.getElementById(parentId);
    // 根据构造参数初始化选中的选项
    for (let i = 0; i < indicators.length; i++) {
        if (this.listStates.hasOwnProperty(indicators[i])) {
            this.listStates[indicators[i]] = 1;
        }
    }
    // 当点击选项后，更新状态值
    DropdownCheckbox.prototype.updateCheckbox = function (indicator) {
        //console.log(indicator);
        if (this.listStates[indicator] === 1) {
            this.listStates[indicator] = 0;
        } else {
            this.listStates[indicator] = 1;
        }
        //console.log(this.listData);
        this.parent.self.updateIndicator(this.listStates, this.listData);
    };
    // 创建复选框
    DropdownCheckbox.prototype.createPanel = function () {
        let div = document.getElementById("dropdown-div");
        let targetOffset = $(this.target).offset();
        let parentOffset = $(div).parent().offset();
        //console.log(targetOffset);
        //console.log(parentOffset);
        $(div).css("left", targetOffset.left - parentOffset.left + 20);
        $(div).css("top", targetOffset.top - parentOffset.top + 20);
        // 复选框
        let options = document.createElement("ul");
        $(options).css("list-style", "none");
        $(options).attr("id", "dropdown-option");
        options.self = this;
        for (let key in this.listData) {
            if (this.listData.hasOwnProperty(key)) {
                let li = document.createElement("li");
                let input = document.createElement("input");
                $(input).prop("data-value", key);
                $(input).prop("value", this.listData[key]);
                $(input).attr("type", "checkbox");
                if (this.listStates[key] === 1) {
                    $(input).prop("checked", "true");
                }
                $(input).click(function () {
                    options.self.updateCheckbox($(this).prop("data-value"));
                });
                let span = document.createElement("span");
                $(span).attr("title", this.listData[key]);
                span.innerHTML = this.listData[key];
                $(li).append(input);
                $(li).append(span);
                $(options).append(li);
            }
        }
        $(div).append(options);
    };
}

/**
 * @class IndicatorDict
 * @classdesc 为指标的中文表示和英文表示提供互相转换的功能
 * @constructor
 */
function IndicatorDict() {
    this.indicatorDict = {
        'current_ratio': '流动比率',
        'quick_ratio': '速动比率',
        'ca_turn': '流动资产周转率',
        'assets_turn': '总资产周转率',
        'debt_to_assets': '资产负债率',
        'netprofit_margin': '销售净利率',
        'grossprofit_margin': '销售毛利率',
        'npta': '总资产净利率',
        'roe': '净资产收益率',
        'eps': '每股收益',
        'pe': '市盈率',
        'bps': '每股净资产',
        'pb': '市净率'
    };

    IndicatorDict.prototype.getIndicatorName = function (indicator) {
        if (this.indicatorDict.hasOwnProperty(indicator)) {
            return this.indicatorDict[indicator];
        } else {
            return null;
        }
    };

    IndicatorDict.prototype.getIndicator = function (indicatorName) {
        for (let key of this.indicatorDict) {
            if (this.indicatorDict.hasOwnProperty(key)) {
                if (this.indicatorDict[key] === indicatorName) {
                    return key;
                }
            }
        }
    }
}

/**
 * @class OptionUnit
 * @classdesc 用于创建筛选条件的单元，包括4部分，
 *            分别为指标名称、操作符、具体数值以及删除按键
 */
function OptionUnit(indicatorName) {
    this.indicatorName = indicatorName;

    OptionUnit.prototype.createPanel = function () {
        let unit = document.createElement("div");
        unit.self = this;
        $(unit).addClass("option-unit");
        let label = document.createElement("label");
        console.log(this.indicatorName);
        label.innerHTML = indicatorDict.getIndicatorName(this.indicatorName);
        $(label).prop("indicator", this.indicatorName);
        let select = document.createElement("select");
        let sOptions = [">", "=", "<"];
        for (let i = 0; i < sOptions.length; i++) {
            let option = document.createElement("option");
            option.value = sOptions[i];
            option.innerHTML = sOptions[i];
            $(select).append(option);
        }
        let input = document.createElement("input");
        input.type = "text";
        $(input).val(1);
        let removeButton = document.createElement("button");
        $(removeButton).addClass("glyphicon glyphicon-remove btn-style-1");
        $(removeButton).click(function () {
            let optionSet = document.getElementById("option-set");
            optionSet.removeChild(unit);
        });
        $(unit).append(label);
        $(unit).append(select);
        $(unit).append(input);
        $(unit).append(removeButton);
        return unit;
    }
}

/**
 * 以表格的形式来列出选出的个股以及其信息
 * @param dataset
 * @constructor
 */
function TabularStock(dataset) {
    this.dataset = dataset;
    this.displayIndi = ['ts_code', 'name', 'roe', 'pb', 'pe'];

    TabularStock.prototype.createPanel = function () {
        let tbl = document.createElement("table");
        $(tbl).addClass("table table-striped col-sm-10");
        $(tbl).attr("id", "list-tbl");
        // 表格头
        let thead = document.createElement("thead");
        $(thead).attr("id", 'tbl-head');
        let headline = document.createElement("tr");
        for (let i = 0; i < this.displayIndi.length; i++) {
            let th = document.createElement("th");
            th.innerHTML = this.displayIndi[i];
            if (this.displayIndi[i] !== "name") {
                let bt = document.createElement("button");
                $(bt).addClass("btn-style-1 glyphicon glyphicon-sort sort-btn");
                $(bt).prop("indicator", this.displayIndi[i]);
                $(bt).prop("status", "0");
                addBtnEvent(bt);
                bt.self = this;
                th.append(bt);
            }
            headline.append(th);
        }
        thead.append(headline);
        tbl.append(thead);
        // 表格主体
        let tbody = document.createElement("tbody");
        $(tbody).attr("id", 'tbl-body');
        let lines = Math.min(20, this.dataset.length);
        for (let i = 0; i < lines; i++) {
            let tr = document.createElement("tr");
            let line = this.dataset[i];
            for (let j = 0; j < this.displayIndi.length; j++) {
                let td = document.createElement("td");
                if (line.hasOwnProperty(this.displayIndi[j])) {
                    td.innerHTML = line[this.displayIndi[j]];
                } else {
                    td.innerHTML = "none";
                }
                tr.append(td);
            }
            tbody.append(tr);
        }
        tbl.append(tbody);
        return tbl;
    };

    function addBtnEvent(btn) {
        $(btn).click(function () {
            let btn = $(this);
            if (btn.prop("status") === "0") { // 初始状态转换为降序排列
                btn.prop("status", "1");
                btn.removeClass("glyphicon-sort");
                btn.addClass("glyphicon-sort-by-attributes-alt");
                this.self.dataset.sort(function (x, y) {
                    if (typeof (x[$(btn).prop("indicator")]) === "string") {
                        return -x[$(btn).prop("indicator")].localeCompare(y[$(btn).prop("indicator")]);
                    }
                    return -(x[$(btn).prop("indicator")] - y[$(btn).prop("indicator")]);
                })
            } else if (btn.prop("status") === "1") { // 降序排列转换为升序排列
                btn.prop("status", "2");
                btn.removeClass("glyphicon-sort-by-attributes-alt");
                btn.addClass("glyphicon-sort-by-attributes");
                this.self.dataset.sort(function (x, y) {
                    if (typeof (x[$(btn).prop("indicator")]) === "string") {
                        return x[$(btn).prop("indicator")].localeCompare(y[$(btn).prop("indicator")]);
                    }
                    return x[$(btn).prop("indicator")] - y[$(btn).prop("indicator")];
                })
            } else if (btn.prop("status") === "2") { // 升序排列转换为初始状态
                btn.prop("status", "0");
                btn.removeClass("glyphicon-sort-by-attributes");
                btn.addClass("glyphicon-sort");
            } else {
                alert("未知状态： " + btn.prop("status"));
            }
            //console.log(this.self.dataset);
            this.self.updateTable();
        })
    }

    TabularStock.prototype.updateTable = function () {
        //console.log(this.dataset);
        let lines = Math.min(20, this.dataset.length);
        let tds = $("#tbl-body").find("td");
        //console.log(tds);
        for (let i = 0; i < lines; i++) {
            for (let j = 0; j < this.displayIndi.length; j++) {
                tds[j + i * this.displayIndi.length].innerHTML = this.dataset[i][this.displayIndi[j]];
            }
        }
    };
}

/**
 * @class StockInfo
 * @classdesc 用于创建股票基本信息的div，包括股票名称、股票代码以及价格
 */
function StockInfo(stockCode, stockName, stockPrice) {
    this.stockCode = stockCode;
    this.stockName = stockName;
    this.stockPrice = stockPrice;
    StockInfo.prototype.createPanel = function () {
        let infoDiv = document.createElement("div");
        $(infoDiv).addClass("stockinfo-div col-sm-3");
        let code = document.createElement("p");
        let name = document.createElement("p");
        let price = document.createElement("p");
        code.innerHTML = this.stockCode;
        name.innerHTML = this.stockName;
        price.innerHTML = this.stockPrice;
        $(code).addClass("stock-code-lg");
        $(name).addClass("stock-name-lg");
        $(price).addClass("stock-price-lg");
        infoDiv.append(code);
        infoDiv.append(name);
        infoDiv.append(price);
        return infoDiv;
    }
}

/**
 * @class Indicator
 * @classdesc 用于创建指标及其值的单元，包括指标名称以及其数值
 */
function Indicator(indicator, value) {
    this.indicator = indicator;
    this.value = value;
    Indicator.prototype.createPanel = function () {
        let indicatorDiv = document.createElement("div");
        let indicatorName = document.createElement("p");
        let indicatorValue = document.createElement("p");
        $(indicatorValue).prop("value", this.value);
        indicatorName.innerHTML = this.indicator;
        $(indicatorValue).attr("title", this.value);
        $(indicatorDiv).addClass("indicator-div");
        $(indicatorName).addClass("indicator-name");
        //indicatorValue.innerHTML = this.value;
        $(indicatorValue).addClass("fa fa-check-circle indicator-value");
        $(indicatorValue).click(function () {
            console.log($(this).prop("value"));
        });
        $(indicatorDiv).append(indicatorName);
        $(indicatorDiv).append(indicatorValue);
        return indicatorDiv;
    };
}

/**
 * 翻页功能组件
 * @param params
 * @constructor
 */
function PageTurn(params) {
    this.itemNum = params["itemNum"];
    this.numPerPage = params["numPerPage"];
    let updateMethod = params["updateMethod"];
    let maxButtons = params["maxButtons"];
    let curPage = 1;
    let pages = Math.ceil(this.itemNum / this.numPerPage);

    PageTurn.prototype.createPanel = function () {
        // 翻页组件总容器
        //let div = document.createElement("div");
        let div = document.getElementById("page-turn-div");
        // 页面容器
        let pagesDiv = document.createElement("div");
        $(pagesDiv).addClass("pages-div");
        // 上一页按钮
        let pageDown = document.createElement("button");
        pageDown.innerHTML = "<";
        $(pageDown).attr("id", "pagedown-btn");
        $(pageDown).prop("page-num", "down");
        $(pageDown).addClass("page-btn");
        if (curPage === 1) {
            $(pageDown).prop("disabled", true);
        }
        $(pagesDiv).append(pageDown);
        // 分页按钮
        let specPagesDiv = document.createElement("div");
        $(specPagesDiv).attr("id", "spec-page-div");
        $(specPagesDiv).css("display", "inline");
        let btnFlag = 0;
        for (let i = 0; i < pages; i++) {
            if (i > maxButtons - 2 && i < pages - 1) {
                if (btnFlag === 0) {
                    let label = document.createElement("label");
                    label.innerHTML = "...";
                    $(label).css("margin", "10px");
                    $(specPagesDiv).append(label);
                    btnFlag = 1;
                    continue;
                } else {
                    continue;
                }
            }
            let pageBtn = document.createElement("button");
            pageBtn.innerHTML = (i + 1).toString();
            $(pageBtn).prop("page-num", (i + 1).toString());
            $(pageBtn).addClass("page-btn spec-pages");
            $(pageBtn).css("width", "34px");
            if (i === 0) {
                $(pageBtn).addClass("selected-page-btn");
            }
            $(specPagesDiv).append(pageBtn);
        }
        $(pagesDiv).append(specPagesDiv);
        // 下一页按钮
        let pageUp = document.createElement("button");
        pageUp.innerHTML = ">";
        $(pageUp).attr("id", "pageup-btn");
        $(pageUp).prop("page-num", "up");
        $(pageUp).addClass("page-btn");
        if (curPage === pages) {
            $(pageUp).prop("disabled", true);
        }
        $(pagesDiv).append(pageUp);
        //
        $(div).append(pagesDiv);
        // 跳转子组件
        let jumpDiv = document.createElement("div");
        $(jumpDiv).addClass("jump-div");
        let label1 = document.createElement("label");
        label1.innerHTML = "前往:";
        $(label1).css("margin-left", "10px");
        $(jumpDiv).append(label1);
        //
        let input1 = document.createElement("input");
        input1.type = "text";
        $(input1).attr("id", "target-page");
        $(input1).css("width", "40px");
        $(jumpDiv).append(input1);
        //
        let btn = document.createElement("button");
        $(btn).attr("id", "jump-btn");
        $(btn).prop("page-num", "jump");
        btn.innerHTML = "跳转";
        $(btn).addClass("page-btn");
        $(jumpDiv).append(btn);
        //
        let label2 = document.createElement("label");
        label2.innerHTML = `第${curPage}页/共${pages}页`;
        $(jumpDiv).append(label2);
        //
        $(div).append(jumpDiv);
        pageBtnEvent();
        return div;
    };

    function pageBtnEvent() {
        //$(".page-btn").click(function (){
        $(".pages-div, .jump-div").on("click", ".page-btn", function () {
            let pageNum = $(this).prop("page-num");
            console.log(pageNum);
            let prePage = curPage;
            if (pageNum === "down") { // 上一页按钮
                curPage = curPage - 1;
            } else if (pageNum === "up") { // 下一页按钮
                curPage = curPage + 1;
            } else if (pageNum === "jump") { // 跳转按钮
                let tarPage = parseInt($("#target-page").val());
                if (!isNaN(tarPage) && (tarPage >= 1 && tarPage <= pages)) {
                    curPage = tarPage;
                } else {
                    alert("不合法页数 " + tarPage);
                    return;
                }
            } else { // 具体页面按钮
                curPage = parseInt(pageNum);
            }
            let pageBtns = document.getElementsByClassName("spec-pages");
            for (let i = 0; i < pageBtns.length; i++) {
                let t = $(pageBtns[i]).prop("page-num");
                if (t === prePage.toString()) {
                    $(pageBtns[i]).removeClass("selected-page-btn");
                }
            }
            //调整在页面中显示的按钮
            updateSpecBtns(curPage);
            if (curPage === 1) {
                $("#pagedown-btn").prop("disabled", true);
                $("#pageup-btn").prop("disabled", false);
            } else if (curPage > 1 && curPage < pages) {
                $("#pagedown-btn").prop("disabled", false);
                $("#pageup-btn").prop("disabled", false);
            } else if (curPage === pages) {
                $("#pagedown-btn").prop("disabled", false);
                $("#pageup-btn").prop("disabled", true);
            }
            $(".jump-div").find("label")[1].innerHTML = `第${curPage}页/共${pages}页`;
            updateMethod((curPage - 1) * 20, curPage * 20);
        })
    }

    function updateSpecBtns(curPage) {
        let startNum = curPage - Math.floor(maxButtons / 2) + 1;
        let endNum = curPage + Math.floor(maxButtons / 2) - 1;
        if (startNum <= 1) {
            startNum = 1;
            endNum = Math.min(startNum + maxButtons - 2, pages);
            if (endNum === pages - 1) {
                endNum = pages;
            }
        } else if (endNum >= pages) {
            endNum = pages;
            startNum = Math.max(1, endNum - maxButtons + 2);
            if (startNum === 2) {
                startNum = 1;
            }
        } else if (startNum === 2) {
            startNum--;
            if (maxButtons % 2 === 0)
                endNum--;
        } else if (endNum === pages - 1) {
            if (maxButtons % 2 === 0)
                startNum++;
            endNum++;
        } else {
            if (maxButtons % 2 === 0)
                endNum--;
        }
        removeChild("spec-page-div");
        let specPageDiv = $("#spec-page-div");
        let frontFlag = 0;
        let backFlag = 0;
        for (let i = 1; i <= pages; i++) {
            let pageBtn = document.createElement("button");
            pageBtn.innerHTML = i.toString();
            $(pageBtn).prop("page-num", i.toString());
            $(pageBtn).addClass("page-btn spec-pages");
            $(pageBtn).css("width", "34px");
            if (i === curPage) {
                $(pageBtn).addClass("selected-page-btn");
            }
            //
            let label = document.createElement("label");
            label.innerHTML = "...";
            $(label).css("margin", "10px");
            if (i === 1) {
                specPageDiv.append(pageBtn);
                if (i === curPage) {
                    $(pageBtn).addClass("selected-page-btn");
                }
            } else if (i > 1 && i < startNum) {
                if (frontFlag === 0) {
                    specPageDiv.append(label);
                    frontFlag = 1;
                }
            } else if (i >= frontFlag && i <= endNum) {
                specPageDiv.append(pageBtn);
                if (i === curPage) {
                    $(pageBtn).addClass("selected-page-btn");
                }
            } else if (i > endNum && i < pages) {
                if (backFlag === 0) {
                    specPageDiv.append(label);
                    backFlag = 1;
                }
            } else if (i === pages) {
                specPageDiv.append(pageBtn);
                if (i === curPage) {
                    $(pageBtn).addClass("selected-page-btn");
                }
            }
        }

    }
}

/**
 * 将详细列表的创建封装起来，便于后期的完善
 * @param dataset
 * @constructor
 */
function StockDetail(dataset) {
    this.dataset = dataset;
    let pageTurnDiv = $("#page-turn-div");
    let listContent = $("#list-content");
    let listDiv = $("#list-div");

    StockDetail.prototype.createPanel = function () {
        for (let i = 0; i < Math.min(this.dataset.length, 20); i++) {
            listContent.append(new StockUnit(dataset[i]).createPanel());
        }
        removeChild("page-turn-div");
        pageTurnDiv.append(new PageTurn({
            itemNum: this.dataset.length,
            numPerPage: 20,
            maxButtons: 7,
            updateMethod: this.updatePage
        }).createPanel());
        setCmpPosition()
    };

    StockDetail.prototype.updatePage = function (startIndex, endIndex) {
        console.log(`page update, start: ${startIndex}, end: ${endIndex}`);
        removeChild("list-content");
        endIndex = Math.min(endIndex, dataset.length);
        for (let i = startIndex; i < endIndex; i++) {
            listContent.append(new StockUnit(dataset[i]).createPanel());
        }
    };

    function setCmpPosition() {
        $(pageTurnDiv).css("left", (listDiv.innerWidth() - $(pageTurnDiv).width()) / 2);
    }
}

/**
 * ******************************************************************************
 * multi_indicator.html
 */
function IndicatorList(containerId, indicatorTree, targetId) {
    let container = $(`#${containerId}`);
    let target = $(`#${targetId}`);
    this.indicatorTree = indicatorTree;

    IndicatorList.prototype.createPanel = function () {
        for (let item in this.indicatorTree) {
            if (this.indicatorTree.hasOwnProperty(item)) {
                // 获取该item下的所有指标
                let indicators = this.indicatorTree[item];
                // 放置该item的容器
                let div = document.createElement("div");
                $(div).addClass("list-unit");
                // 该item的标题
                let titleP = document.createElement("p");
                titleP.innerHTML = indicators['name'];
                $(div).append(titleP);
                delete indicators['name']; // 注意此处删除会影响到原先的对象
                // 添加该item下的各个指标
                let ul = document.createElement("ul");
                for (let indicator in indicators) {
                    if (indicators.hasOwnProperty(indicator)) {
                        let li = document.createElement("li");
                        // 获取该指标的具体内容
                        let indicatorInfo = indicators[indicator];
                        li.innerHTML = indicatorInfo['name'];
                        $(li).prop("indicator", indicator);
                        $(li).prop("selected", 0);
                        delete indicatorInfo['name'];
                        addLiEvent(li, indicatorInfo, "selected-indicator");
                        $(ul).append(li);
                    }
                }
                $(div).append(ul);
                $(container).append(div);
            }
        }
        let closeBtn = document.createElement("button");
        $(closeBtn).addClass("glyphicon glyphicon-remove close-btn btn-style-1");
        $(closeBtn).click(function () {
            container.css("display", "none");
        });
        container.append(closeBtn);
    };
}

function StockPoolList(containerId, stockPoolTree) {
    let container = $(`#${containerId}`);
    this.stockPoolTree = stockPoolTree;

    StockPoolList.prototype.createPanel = function () {
        for (let item in this.stockPoolTree) {
            if (this.stockPoolTree.hasOwnProperty(item)) {
                // 获取该item下的所有指标
                let indexCodes = this.stockPoolTree[item];
                // 放置该item的容器
                let div = document.createElement("div");
                $(div).addClass("list-unit");
                // 该item的标题
                let titleP = document.createElement("p");
                titleP.innerHTML = indexCodes['name'];
                $(div).append(titleP);
                delete indexCodes['name']; // 注意此处删除会影响到原先的对象
                // 添加该item下的各个指标
                let ul = document.createElement("ul");
                for (let indexCode in indexCodes) {
                    if (indexCodes.hasOwnProperty(indexCode)) {
                        let li = document.createElement("li");
                        // 获取该指标的具体内容
                        li.innerHTML = indexCodes[indexCode];
                        $(li).prop("indexCode", indexCode);
                        $(li).prop("selected", 0);
                        //delete indicatorInfo['name'];
                        addLiEvent(li, null, "selected-pool");
                        $(ul).append(li);
                    }
                }
                $(div).append(ul);
                $(container).append(div);
            }
        }
        let closeBtn = document.createElement("button");
        $(closeBtn).addClass("glyphicon glyphicon-remove close-btn btn-style-1");
        $(closeBtn).click(function () {
            container.css("display", "none");
        });
        container.append(closeBtn);
    };
}

function StockList(secPool, containerId) {
    this.secPool = secPool;
    let container = $(`#${containerId}`);

    StockList.prototype.createPanel = function () {
        let selectedSec = {};
        let listTb = document.createElement("table");
        $(listTb).addClass("table table-striped");
        let thead = document.createElement("thead");
        let tbody = document.createElement("tbody");
        // 表头
        let headline = document.createElement("tr");
        let codeHead = document.createElement("th");
        codeHead.innerHTML = "股票代码";
        headline.append(codeHead);
        let nameHead = document.createElement("th");
        nameHead.innerHTML = "股票名称";
        headline.append(nameHead);
        let btnHead = document.createElement("th");
        let selectAllBtn = document.createElement("button");
        $(selectAllBtn).prop("selected", 0);
        selectAllBtn.innerHTML = "全部选择";
        $(selectAllBtn).click(function () {
            let btns = $(tbody).find("button");
            //console.log(btns);
            if ($(this).prop("selected") === 1) {
                this.innerHTML = "全部选择";
                $(this).prop("selected", 0);
                for (let i = 0; i < btns.length; i++) {
                    if ($(btns[i]).prop("added") === 1) {
                        //console.log($(btns[i]));
                        $(btns[i]).click();
                    }
                }
            } else {
                this.innerHTML = "取消选择";
                $(this).prop("selected", 1);
                for (let i = 0; i < btns.length; i++) {
                    if ($(btns[i]).prop("added") === 0) {
                        //console.log($(btns[i]));
                        $(btns[i]).click();
                    }
                }
            }
        });
        btnHead.append(selectAllBtn);
        headline.append(btnHead);
        thead.append(headline);
        // 表体
        for (let i = 0; i < this.secPool.length; i++) {
            let tr = document.createElement("tr");
            let sec = this.secPool[i];
            let code = document.createElement("td");
            code.innerHTML = sec['ts_code'];
            tr.append(code);
            let name = document.createElement("td");
            name.innerHTML = sec['name'];
            tr.append(name);
            let btnTd = document.createElement("td");
            let btn = document.createElement("button");
            $(btn).addClass("btn-style-1 glyphicon glyphicon-plus");
            $(btn).prop("secCode", sec['ts_code']);
            $(btn).prop("secName", sec['name']);
            $(btn).prop("added", 0);
            $(btn).click(function () {
                //console.log($(this).prop("secCode"));
                if ($(this).prop("added") === 0) {
                    if (!selectedSec.hasOwnProperty($(this).prop("secCode"))) {
                        selectedSec[$(this).prop("secCode")] = $(this).prop("secName");
                    }
                    $(this).prop("added", 1);
                    $(this).removeClass("glyphicon-plus");
                    $(this).addClass("glyphicon-minus");
                } else if ($(this).prop("added") === 1) {
                    if (selectedSec.hasOwnProperty($(this).prop("secCode"))) {
                        delete selectedSec[$(this).prop("secCode")];
                    }
                    $(this).prop("added", 0);
                    $(this).removeClass("glyphicon-minus");
                    $(this).addClass("glyphicon-plus");
                } else {
                    alert("未知状态： " + $(this).prop("added"));
                }
                container.prop("selectedSec", selectedSec);
            });
            btnTd.append(btn);
            $(tr).append(code);
            $(tr).append(name);
            $(tr).append(btnTd);
            tbody.append(tr);
        }
        listTb.append(thead);
        listTb.append(tbody);
        container.append(listTb);
    }
}

export {
    StockUnit, DropdownCheckbox, IndicatorDict, OptionUnit,
    TabularStock, StockInfo, Indicator, PageTurn, StockDetail,
    IndicatorList, StockPoolList, StockList
};