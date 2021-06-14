function stockListEvents() {
    $("body").height(window.innerHeight);
    let optionSet = $("#option-set");
    $(optionSet.find("label")[0]).prop("indicator", "sec_pool");
    $(optionSet.find("label")[1]).prop("indicator", "trade_date");
    $("#list-method-btn").prop("list-method", "1");

    /**
     * 条件添加按钮事件，将条件选择窗口显示到网页中
     */
    $("#option-add-btn").click(function () {
        //console.log("click");
        let selectDiv = document.getElementById("option-select-div");
        $(selectDiv).css("display", "block");
        $(selectDiv).css("left", window.innerWidth / 2 - $(selectDiv).width() / 2);
        $(selectDiv).css("top", window.innerHeight / 3 - $(selectDiv).height() / 3);
    });

    /**
     * 条件选择窗口中的确认条件按钮事件，
     * 点击后隐藏窗口并将选中的条件添加到网页中
     */
    $("#select-ok-btn").click(function () {
        //let selectDiv = document.getElementById("option-select-div");
        $("#option-select-div").css("display", "none");
        let optionName = $("#option-select").val();
        //console.log(optionName);
        //let optionSet = document.getElementById("option-set");
        $("#option-set").append(new OptionUnit(optionName).createPanel());
    });

    /**
     * 条件选择窗口中的取消按钮事件，
     * 点击后将窗口隐藏
     */
    $("#select-cancel-btn").click(function () {
        let selectDiv = document.getElementById("option-select-div");
        $(selectDiv).css("display", "none");
    });

    /**
     * 排列方式选择按钮，用于改变个股的排列方式
     * 目前有两种形式，一种是以每支股票为一单元的详细信息，另一种是表格形式
     */
    $("#list-method-btn").click(function () {
        let listMethod = $(this).prop("list-method");
        if (listMethod == LIST_LARGE) {// 瘵详细信息排列转换为表格排列
            $(this).prop("list-method", LIST_SMALL);
            $(this).addClass("glyphicon-th-list");
            $(this).removeClass("glyphicon-th-large");
            removeChild("list-content");
            $("#list-content").append(new TabularStock(dataset).createPanel());
        } else if (listMethod == LIST_SMALL) { // 将表格排列转换为详细信息排列
            $(this).prop("list-method", LIST_LARGE);
            $(this).addClass("glyphicon-th-large");
            $(this).removeClass("glyphicon-th-list");
            removeChild("list-content");
            new StockDetail(dataset).createPanel();
        } else {
            alert("未知排列方式" + listMethod);
        }
    });
}

function addDropdownBtnEvent(btn) {
    $(btn).click(function () {
        let dropdownDiv = $("#dropdown-div");
        let unit = this.parentNode;
        let dropdownBtn = $(this);
        //console.log(dropdownDiv);
        // 当点击箭头向上的按钮时，更改按钮图案并将复选框隐藏
        if (dropdownBtn.prop("status") === 1) { //当复选框为打开状态，则删去复选框并更改按钮图案
            //console.log(dropdownbtn.attr("id"));
            dropdownDiv.css("display", "none");
            dropdownBtn.prop("status", 0);
            dropdownBtn.removeClass("glyphicon-chevron-up");
            dropdownBtn.addClass("glyphicon-chevron-down");
            removeChild("dropdown-div");
        } else { //当复选框为关闭状态，则创建复选框并更改按钮图案
            dropdownDiv.css("display", "flex");
            //console.log(dropdownbtn);
            // 该函数用于将所有按钮置于关闭状态，之后将被点击的按钮置于打开状态
            unit.self.resetButtonStatus(dropdownBtn.attr("id"));
            //console.log($(unit));
            new DropdownCheckbox(unit.self.getSelectedIndicator(), $(this).attr("id"), $(unit).attr("id")).createPanel();
        }
    });
}

function multiIndiEvents() {
    $("body").height(window.innerHeight);
}

/**
 * *****************************************************************************
 * multi_indicator.html
 */
function addLiEvent(li, childItems, containerId) {
    $(li).click(function () {
        if ($(this).prop("selected") === 1) {
            return;
        }
        let container = document.getElementById(containerId);
        let div = document.createElement("div");
        $(div).addClass("selected-unit");
        let label = document.createElement("label");
        if (typeof ($(this).prop("indicator")) == "undefined") {
            $(label).prop("indexCode", $(this).prop("indexCode"));
        }
        if (typeof ($(this).prop("indexCode")) == "undefined") {
            $(label).prop("indicator", $(this).prop("indicator"));
        }
        $(this).css("color", "#999999");
        $(this).prop("selected", 1);
        label.innerHTML = li.innerHTML;
        $(div).append(label);
        //
        let closeBtn = document.createElement("Button");
        $(closeBtn).addClass("glyphicon glyphicon-remove btn-style-1");
        $(closeBtn).css("padding", 2);
        $(closeBtn).click(function () {
            $(this).parent().remove();
            $(li).css("color", "#000000");
            $(li).prop("selected", 0);
        });
        $(div).append(closeBtn);
        //
        $(container).append(div);

    })
}

export {
    stockListEvents, addDropdownBtnEvent, multiIndiEvents, addLiEvent
};