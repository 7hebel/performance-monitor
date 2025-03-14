let socket = null;
let reconnectTimeout = null;
let gotPerfComposition = false;

const EV_PERF_COMPOSITION_DATA = "perf-composition-data";
const EV_PERF_METRICS_UPDATE = "perf-metrics-update";
const EV_PERF_ADD_MONITOR = "perf-add-monitor";
const EV_PERF_REMOVE_MONITOR = "perf-remove-monitor";
const EV_RAISE_ALERT = "raise-alert";
const EV_MONITOR_CHANGE = "monitor-change";

function setConnectionStatus(status) {
    let statusEl = document.getElementById("connectionStatus");

    if (status) {
        statusEl.setAttribute("status", "1");
        statusEl.textContent = "";
    } else {
        statusEl.setAttribute("status", "0");
        statusEl.textContent = "Disconnected";
    }
}

function onSocketFailure() {
    if (reconnectTimeout) return;

    setConnectionStatus(false);
    reconnectTimeout = setTimeout(() => {
        reconnectTimeout = null;
        setupSocket();
    }, 1000);
}

function setupSocket() {
    socket = new WebSocket('ws://localhost:50505');
    socket.addEventListener('open', (event) => {
        console.log("Connection opened") 
        if (gotPerfComposition) {
            window.location.reload()
        }
    });
    socket.addEventListener('message', (event) => {
        setConnectionStatus(true);
        const message = JSON.parse(event.data);
        handleMessage(message.event, message.data);
    });
    
    socket.addEventListener('close', (event) => {
        if (event.code !== 1006) console.log('Connection closed:', event);
        onSocketFailure();
    });

    socket.addEventListener('error', (error) => { onSocketFailure(); });
}

setupSocket();

function _sendMessageToServer(evtype, data) {
    const message = {
        event: evtype,
        data: data
    };

    socket.send(JSON.stringify(message));
}

async function handleMessage(evtype, data) {
    if (evtype == EV_PERF_COMPOSITION_DATA) {
        if (gotPerfComposition) return;
        gotPerfComposition = true;
        
        for (monitor of data) {
            addMonitorHeader(monitor.categoryId, monitor.targetTitle);
            buildDataPage(monitor.categoryId, monitor.targetTitle, monitor.productInfo, monitor.color, monitor.metrics);
        }

        console.log(`Built ${data.length} performance monitors.`);
    }

    if (evtype == EV_PERF_METRICS_UPDATE) {
        Object.entries(data).forEach(
            ([id, value]) => {
                const element = document.getElementById(id);
                if (element === null) updateChart(id, value);
                else document.getElementById(id).textContent = value;
            }
        )
    }

    if (evtype == EV_PERF_ADD_MONITOR) {
        addMonitorHeader(data.categoryId, data.targetTitle);
        buildDataPage(data.categoryId, data.targetTitle, data.productInfo, data.color, data.metrics);
        console.log(`Dynamically added new performance monitor: ${data.targetTitle}`);
    }

    if (evtype == EV_PERF_REMOVE_MONITOR) {
        document.getElementById(data).remove();
        document.getElementById("view-" + data).remove();
        console.log(`Dynamically removed performance monitor: ${data}`);
    }
}

function announceMonitorChange(monitorId) {
    _sendMessageToServer(EV_MONITOR_CHANGE, monitorId)
}
