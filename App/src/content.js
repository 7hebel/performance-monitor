const MONITORS_LIST = document.getElementById("monitorsList");
const MONITORS_CONTENTS = document.getElementById("monitorContents");
const defined_page_containers = [];


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


function buildDataPage(monitorId, targetTitle, productInfo, color, components) {
    const monitorView = document.createElement("div");
    monitorView.className = "monitorView";
    monitorView.id = `view-${monitorId}`;
    monitorView.setAttribute("active", "0");
    monitorView.setAttribute("color", color);

    monitorView.innerHTML = `
        <div class="monitorHeader">
            <h3>${targetTitle}</h3>
            <h3 class="productInfo">${productInfo}</h3>
        </div>
    `;

    const componentsContainer = document.createElement("div");
    componentsContainer.className = "componentsContainer";
    monitorView.appendChild(componentsContainer);

    components.forEach(component => {
        if (Array.isArray(component)) { // ComponentsRow
            const row = document.createElement("div");
            row.className = "componentsRow";
            componentsContainer.appendChild(row);

            component.forEach(rowComponent => {
                buildComponent(rowComponent.type, rowComponent.identificator, rowComponent.title, rowComponent.details, color, row);
            })
        } else {
            buildComponent(component.type, component.identificator, component.title, component.details, color, componentsContainer)
        }

    })

    MONITORS_CONTENTS.appendChild(monitorView);
    defined_page_containers.push(monitorView);

    initializeCharts();
}


function switchMonitor(monitorId) {
    defined_page_containers.forEach(m => m.setAttribute("active", "0"));

    const newMonitor = document.getElementById(`view-${monitorId}`);
    newMonitor.setAttribute("active", "1");
    
    const newColor = newMonitor.getAttribute("color");
    document.documentElement.style.setProperty("--accent-color", newColor);
}


function buildComponent(type, identificator, title, details, color, container) {
    if (type == "chart") {
        const chartComponent = document.createElement("div");
        chartComponent.className = "chartComponent";
        container.appendChild(chartComponent);

        const categoryId = identificator.split('.')[0];
        const previewChartEl = document.getElementById(categoryId).querySelector(".chartPreview");

        generateChartComponent(identificator, title, color, chartComponent, previewChartEl);
    }
    if (type == "keyvalue") {
        const value = details.staticValue ?? '-';
        const kvComponent = document.createElement("div");
        kvComponent.className = (details.important) ? "kvComponentImportant" : "kvComponentStandard";
        kvComponent.innerHTML = `
            <p class="componentTitle">${title}</p>
            <p class="componentValue" id="${identificator}">${value}</p>
        `;
        
        container.appendChild(kvComponent);
    }
}
