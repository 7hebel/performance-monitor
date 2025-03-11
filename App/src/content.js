const MONITORS_LIST = document.getElementById("monitorsList");


function addMonitorHeader(monitorId, targetTitle) {
    const entry = document.createElement("div");
    entry.className = "monitorEntry";
    entry.id = monitorId;

    const title = document.createElement("h4");
    title.className = "monitorTitle";
    title.textContent = targetTitle;

    const chartPreview = document.createElement("div");

    entry.appendChild(title);
    entry.appendChild(chartPreview);
    MONITORS_LIST.appendChild(entry);
}

