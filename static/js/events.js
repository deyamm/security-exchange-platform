import {removeChild} from "./functions.js";
import {LIST_LARGE, LIST_SMALL} from "./variables.js";
import {DropdownCheckbox, OptionUnit, StockDetail, TabularStock} from "./classes.js";

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
        $(selectDiv).css("top", window.innerHeight / 4 - $(selectDiv).height() / 4);
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
 * backtest.html
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