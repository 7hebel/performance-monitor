const MONITORS_LIST = document.getElementById("monitorsList");
const MONITORS_CONTENTS = document.getElementById("monitorContents");
const defined_page_containers = [];
const categoryColors = {};


function handlePerformanceUpdatePacket(packet) {
    Object.entries(packet).forEach(
        ([id, value]) => {
            const element = document.getElementById(id);
            if (element === null) updateChart(id, value);
            else document.getElementById(id).textContent = value;
        }
    );
}

function clearPerformancePage(noLoader=false) {
    Object.keys(REGISTERED_CHARTS).forEach(chartKey => delete REGISTERED_CHARTS[chartKey])

    Array.from(MONITORS_LIST.children).forEach(monitor => {
        if (monitor.id !== "performanceTimingInfo") monitor.remove();
    })
    Array.from(MONITORS_CONTENTS.children).forEach(monitorContent => {
        monitorContent.remove();
    })

    if (!noLoader) {
        MONITORS_CONTENTS.innerHTML = `
            <div class="loaderContainer">
                <div class="code-loader">
                    <span>{</span><span>}</span>
                </div>
            </div>
        `;
    }
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


function buildDataPage(monitorId, targetTitle, productInfo, color, metrics, _forTravelMode=false) {
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
                if (_forTravelMode && !travelModePlaybackType && rowMetric.type == "chart") return;
                let targetContainer = row;
                if (_forTravelMode && !travelModePlaybackType && rowMetric.type == "keyvalue" && rowMetric.details.important) targetContainer = metricsContaienr
                buildMetric(rowMetric.type, rowMetric.identificator, rowMetric.title, rowMetric.details, color, targetContainer, _forTravelMode);
            })
        } else {
            if (_forTravelMode && !travelModePlaybackType && metric.type == "chart") return;
            buildMetric(metric.type, metric.identificator, metric.title, metric.details, color, metricsContaienr, _forTravelMode)
        }

    })

    MONITORS_CONTENTS.appendChild(monitorView);
    defined_page_containers.push(monitorView);

    const category = metrics[0].identificator.split(".", 1)[0].toUpperCase();
    categoryColors[category] = color;
    if (category in trackersPerCategory) {
        trackersPerCategory[category].forEach(elId => document.getElementById(elId).style = `--category-color: ${color}`)
    }

    initializeCharts();
}


function switchMonitor(monitorId) {
    defined_page_containers.forEach(m => m.setAttribute("active", "0"));

    const newMonitor = document.getElementById(`view-${monitorId}`);
    newMonitor.setAttribute("active", "1");
    
    const newColor = newMonitor.getAttribute("color");
    document.documentElement.style.setProperty("--accent-color", newColor);
    document.getElementById("perf-tab").setAttribute("tabColor", newColor);
}


function buildMetric(type, identificator, title, details, color, container, _travelModeChart=false) {
    if (type == "chart") {
        const chartMetric = document.createElement("div");
        chartMetric.className = "chartMetric";
        container.appendChild(chartMetric);

        const categoryId = identificator.split('.')[0];
        let previewChartEl = document.getElementById(categoryId).querySelector(".chartPreview");
        if (_travelModeChart && !travelModePlaybackType) previewChartEl = null;

        generateChartMetric(identificator, title, color, chartMetric, previewChartEl, _travelModeChart);
    }

    if (type == "keyvalue") {
        if (!REALTIME_MODE && !travelModePlaybackType && details.important) {
            return buildMetric("chart", identificator, title, details, color, container, true);
        }
        
        const kvMetric = document.createElement("div");
        kvMetric.className = (details.important) ? "kvMetricImportant" : "kvMetricStandard";
        container.appendChild(kvMetric);
        
        const value = details.initValue ?? '-';
        kvMetric.innerHTML = `
            <p class="metricTitle">${title}</p>
            <p class="metricValue" id="${identificator}">${value}</p>
        `;
        
        const trackedEl = document.getElementById(`tracker-${identificator}`);
        if (trackedEl) trackedEl.textContent = value;
    }
}

