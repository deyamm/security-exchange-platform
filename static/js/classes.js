function StockInfo(stockCode, stockName, stockPrice) {
    this.stockCode = stockCode;
    this.stockName = stockName;
    this.stockPrice = stockPrice;
    StockInfo.prototype.createPanel = function () {
        let infoDiv = document.createElement("div");
        $(infoDiv).addClass("stockinfo-div");
        let code = document.createElement("p");
        code.innerHTML = this.stockCode;
        $(code).addClass("stock-code");
        let name = document.createElement("p");
        name.innerHTML = this.stockName;
        $(name).addClass("stock-name");
        let price = document.createElement("p");
        price.innerHTML = this.stockPrice;
        $(price).addClass("stock-price");
        infoDiv.append(code);
        infoDiv.append(name);
        infoDiv.append(price);
        return infoDiv;
    }
}

function DropdownCheckbox(indicators, targetId, parentId) {
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
    DropdownCheckbox.prototype.createDropdown = function () {
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
                $(input).attr("data-value", key);
                $(input).attr("value", this.listData[key]);
                $(input).attr("type", "checkbox");
                if (this.listStates[key] === 1) {
                    $(input).attr("checked", "true");
                }
                $(input).click(function () {
                    options.self.updateCheckbox($(this).attr("data-value"));
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

function StockUnit(stockData) {
    this.stockData = stockData;
    // 为每支个股unit分配相应的id
    this.unitId = "stock-unit-" + this.stockData['ts_code'].substring(0, 6);
    // 存储在复选框中被选中的选项，并在重新绘制复选框时提供初始选项
    this.selectedIndicator = {'roe': 1, 'bps': 1};
    let indicatorDict = new IndicatorDict();

    StockUnit.prototype.createPanel = function () {
        let unit = document.createElement("div");
        $(unit).attr("id", this.unitId);
        unit.self = this;
        $(unit).addClass("stock-unit col-sm-3");
        //
        let dropdownButton = document.createElement("button");
        $(dropdownButton).attr("id", "dropdown-button-" + this.stockData["ts_code"].substring(0, 6));
        $(dropdownButton).addClass("glyphicon glyphicon-chevron-down dropdown-buttons");
        $(dropdownButton).click(function () {
            let dropdownDiv = $("#dropdown-div");
            let dropdownButton = $(this);
            //console.log(dropdownDiv);
            // 当点击箭头向上的按钮时，更改按钮图案并将复选框隐藏
            if (dropdownButton.attr("status") === "1") { //当复选框为打开状态，则删去复选框并更改按钮图案
                //console.log(dropdownButton.attr("id"));
                dropdownDiv.css("display", "none");
                dropdownButton.attr("status", 0);
                dropdownButton.removeClass("glyphicon-chevron-up");
                dropdownButton.addClass("glyphicon-chevron-down");
                removeChild("dropdown-div");
            } else { //当复选框为关闭状态，则创建复选框并更改按钮图案
                dropdownDiv.css("display", "flex");
                //console.log(dropdownButton);
                // 该函数用于将所有按钮置于关闭状态，之后将被点击的按钮置于打开状态
                resetButtonStatus(dropdownButton.attr("id"));
                //console.log($(unit));
                new DropdownCheckbox(unit.self.getSelectedIndicator(), $(this).attr("id"), $(unit).attr("id")).createDropdown();
            }
        });
        $(unit).append(new StockInfo(this.stockData['ts_code'], this.stockData['name'], this.stockData['close']).createPanel());
        let indicators = this.getSelectedIndicator();
        for (let i = 0; i < indicators.length; i++) {
            $(unit).append(new Indicator(indicatorDict.getIndicatorName(indicators[i]), this.stockData[indicators[i]]).createPanel());
        }
        $(unit).append(dropdownButton);
        return unit;
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

    // 移去子元素，如果指定类名，则只删去包含指定类的子元素
    function removeChild(unitId, delUnitClass = null) {
        let unit = document.getElementById(unitId);
        if (delUnitClass === null) {
            while (unit.hasChildNodes()) {
                unit.removeChild(unit.firstChild);
            }
        } else {
            let children = unit.children;
            let delChildren = [];
            for (let i = 0; i < children.length; i++) {
                if ($(children[i]).hasClass(delUnitClass)) {
                    delChildren.push(children[i]);
                }
            }
            for (let i = 0; i < delChildren.length; i++) {
                unit.removeChild(delChildren[i]);
            }
        }
    }

    function resetButtonStatus(selectedId) {
        let buttons = document.getElementsByClassName("dropdown-buttons");
        //console.log(buttons);
        removeChild("dropdown-div");
        for (let i = 0; i < buttons.length; i++) {
            $(buttons[i]).removeClass("glyphicon-chevron-up");
            $(buttons[i]).addClass("glyphicon-chevron-down");
            $(buttons[i]).attr("status", 0);
        }
        let selectedB = document.getElementById(selectedId);
        $(selectedB).removeClass("glyphicon-chevron-down");
        $(selectedB).addClass("glyphicon-chevron-up");
        $(selectedB).attr("status", 1);
    }
}

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

function Indicator(indicator, value) {
    this.indicator = indicator;
    this.value = value;
    Indicator.prototype.createPanel = function () {
        let indicatorDiv = document.createElement("div");
        $(indicatorDiv).addClass("indicator-div");
        let indicatorName = document.createElement("p");
        indicatorName.innerHTML = this.indicator;
        $(indicatorName).addClass("indicator-name");
        let indicatorValue = document.createElement("p");
        $(indicatorValue).attr("value", this.value);
        //indicatorValue.innerHTML = this.value;
        $(indicatorValue).addClass("fa fa-check-circle indicator-value");
        $(indicatorValue).attr("title", this.value);
        $(indicatorValue).click(function () {
            console.log($(this).attr("value"));
        });
        $(indicatorDiv).append(indicatorName);
        $(indicatorDiv).append(indicatorValue);
        return indicatorDiv;
    };
}

function OptionUnit(indicatorName) {
    this.indicatorName = indicatorName;

    OptionUnit.prototype.createPanel = function () {
        let unit = document.createElement("div");
        unit.self = this;
        $(unit).addClass("option-unit");
        let label = document.createElement("label");
        console.log(this.indicatorName);
        label.innerHTML = indicatorDict.getIndicatorName(this.indicatorName);
        $(label).attr("indicator", this.indicatorName);
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
        $(removeButton).addClass("glyphicon glyphicon-remove button-style-1");
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