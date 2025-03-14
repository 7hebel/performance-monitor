const MONITORS_LIST = document.getElementById("monitorsList");
const MONITORS_CONTENTS = document.getElementById("monitorContents");
const defined_page_containers = [];
let REALTIME_MODE = true;


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


function switchTiming() {
    REALTIME_MODE = !REALTIME_MODE;
    if (REALTIME_MODE) {
        document.getElementById("performanceTimingName").textContent = "Realtime";
        document.getElementById("performanceHistoryBtn").className = "fa-solid fa-clock-rotate-left";
        document.documentElement.style.setProperty("--perf-timing-color", "#97c47e");

        hideTimeTravelPanel();
    } else {
        document.getElementById("performanceTimingName").textContent = "Time Travel mode";
        document.getElementById("performanceHistoryBtn").className = "fa-solid fa-arrow-left";
        document.documentElement.style.setProperty("--perf-timing-color", "#ca6565");

        fetchAndApplyHistoryPoints();
    }
}

function fetchAndApplyHistoryPoints() {
    const options = {
        method: 'GET',
        headers: {'Content-Type': 'application/json'},
    };
    console.log(HTTP_PROTO + "://" + API_ADDRESS + "/perf-history/points")
    fetch(HTTP_PROTO + "://" + API_ADDRESS + "/perf-history/points", options)
        .then(response => response.json())
        .then(historyPoints => {
            setupTimeTravelPanel(historyPoints);

        })
        .catch(error => {
            console.error('Error while fetching performanceHistoryPoints', error);
            switchTiming();
        });
}

function hideTimeTravelPanel() {
    const panel = document.getElementById("performanceTimetravelPanel");
    const datesContainer = document.getElementById("timetravelDate");
    const hoursContainer = document.getElementById("timetravelHours");
    panel.setAttribute("hidden", "1");

    Array.from(hoursContainer.children).forEach(opt => {
        if (opt.value != 0) opt.remove();
    })
    Array.from(datesContainer.children).forEach(opt => {
        if (opt.value != 0) opt.remove();
    })

}

function setupTimeTravelPanel(historyPoints) {
    const panel = document.getElementById("performanceTimetravelPanel");
    const datesContainer = document.getElementById("timetravelDate");
    const hoursContainer = document.getElementById("timetravelHours");
    
    panel.setAttribute("hidden", "0");

    Object.keys(historyPoints).forEach(date => {
        const option = document.createElement("option");
        option.textContent = date;
        option.value = date;
        datesContainer.appendChild(option);
    })

    datesContainer.onchange = (e) => {
        Array.from(hoursContainer.children).forEach(opt => {
            if (opt.value != 0) opt.remove();
        })
        if (datesContainer.value == 0) return;

        historyPoints[datesContainer.value].forEach(clusterData => {
            const option = document.createElement("option");
            option.textContent = clusterData.timeinfo;
            option.value = clusterData.cluster;
            hoursContainer.appendChild(option);
        })
    }
}

function queryTravelData() {
    const cluster = document.getElementById("timetravelHours").value;
    if (cluster == 0) return;

    console.log(cluster)
}

