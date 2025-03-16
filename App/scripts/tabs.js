const TABS_CONTAINER = document.getElementById("tabsContainer");
const TABS_VIEWS = document.getElementById("tabsViews");
let currentTabId = "tab-performance";


function switchTab(tabEl, tabId) {
    if (tabId == currentTabId) return;
    currentTabId = tabId;

    Array.from(TABS_CONTAINER.children).forEach(tab => {
        tab.setAttribute("active", "0");
    })
    tabEl.setAttribute("active", "1");

    Array.from(TABS_VIEWS.children).forEach(view => {
        view.setAttribute("active", "0")
    })
    document.getElementById(tabId).setAttribute("active", "1");
}


