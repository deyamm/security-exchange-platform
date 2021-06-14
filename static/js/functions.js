/**
 * 移去子元素，如果指定类名，则只删去包含指定类的子元素
 * @param unitId
 * @param delUnitClass
 */
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

export {
    removeChild
};