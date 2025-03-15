const MONITORS_LIST = document.getElementById("monitorsList");
const MONITORS_CONTENTS = document.getElementById("monitorContents");
const defined_page_containers = [];


function handlePerformanceUpdatePacket(packet) {
    Object.entries(packet).forEach(
        ([id, value]) => {
            const element = document.getElementById(id);
            if (element === null) updateChart(id, value);
            else document.getElementById(id).textContent = value;
        }
    );
}


function clearPerformancePage() {
    Object.keys(REGISTERED_CHARTS).forEach(chartKey => delete REGISTERED_CHARTS[chartKey])

    Array.from(MONITORS_LIST.children).forEach(monitor => {
        if (monitor.id !== "performanceTimingInfo") monitor.remove();
    })
    Array.from(MONITORS_CONTENTS.children).forEach(monitorContent => {
        monitorContent.remove();
    })
}

function addMonitorHeader(monitorId, targetTitle) {
    const entry = document.createElement("div");
    entry.className = "monitorEntry";
    entry.id = monitorId;
    entry.onclick = () => {
        switchMonitor(monitorId);
    }

    const title = document.createElement("h4");
    title.className = "monitorTitle";
    title.textContent = targetTitle;

    const chartPreview = document.createElement("div");
    chartPreview.className = "chartPreview";

    entry.appendChild(title);
    entry.appendChild(chartPreview);
    MONITORS_LIST.appendChild(entry);
}


function buildDataPage(monitorId, targetTitle, productInfo, color, metrics) {
    const monitorView = document.createElement("div");
    monitorView.className = "monitorView";
    monitorView.id = `view-${monitorId}`;
    monitorView.setAttribute("active", "0");
    monitorView.setAttribute("color", color);

    monitorView.innerHTML = `
        <div class="panelHeader">
            <h3>${targetTitle}</h3>
            <h3 class="productInfo">${productInfo}</h3>
        </div>
    `;

    const metricsContaienr = document.createElement("div");
    metricsContaienr.className = "metricsContainer";
    monitorView.appendChild(metricsContaienr);

    metrics.forEach(metric => {
        if (Array.isArray(metric)) { // MetricsRow
            const row = document.createElement("div");
            row.className = "metricsRow";
            metricsContaienr.appendChild(row);

            metric.forEach(rowMetric => {
                buildMetric(rowMetric.type, rowMetric.identificator, rowMetric.title, rowMetric.details, color, row);
            })
        } else {
            buildMetric(metric.type, metric.identificator, metric.title, metric.details, color, metricsContaienr)
        }

    })

    MONITORS_CONTENTS.appendChild(monitorView);
    defined_page_containers.push(monitorView);

    initializeCharts();
}


function switchMonitor(monitorId) {
    announceMonitorChange(monitorId);

    defined_page_containers.forEach(m => m.setAttribute("active", "0"));

    const newMonitor = document.getElementById(`view-${monitorId}`);
    newMonitor.setAttribute("active", "1");
    
    const newColor = newMonitor.getAttribute("color");
    document.documentElement.style.setProperty("--accent-color", newColor);
}


function buildMetric(type, identificator, title, details, color, container) {
    if (type == "chart") {
        const chartMetric = document.createElement("div");
        chartMetric.className = "chartMetric";
        container.appendChild(chartMetric);

        const categoryId = identificator.split('.')[0];
        const previewChartEl = document.getElementById(categoryId).querySelector(".chartPreview");

        generateChartMetric(identificator, title, color, chartMetric, previewChartEl);
    }

    if (type == "keyvalue") {
        const value = details.initValue ?? '-';
        const kvMetric = document.createElement("div");
        kvMetric.className = (details.important) ? "kvMetricImportant" : "kvMetricStandard";
        kvMetric.innerHTML = `
            <p class="metricTitle">${title}</p>
            <p class="metricValue" id="${identificator}">${value}</p>
        `;
        
        container.appendChild(kvMetric);
    }
}

