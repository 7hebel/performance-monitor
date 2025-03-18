const HTTP_PROTO = "http";
const API_ADDRESS = "localhost:50506";

let socket = null;
let reconnectTimeout = null;
let gotPerfComposition = false;

const EV_PERF_COMPOSITION_DATA = "perf-composition-data";
const EV_UPDATE_PACKET = "update-packet"
const EV_PERF_ADD_MONITOR = "perf-add-monitor";
const EV_PERF_REMOVE_MONITOR = "perf-remove-monitor";
const EV_RAISE_ALERT = "raise-alert";
const EV_MONITOR_CHANGE = "monitor-change";
const EV_PROCESSES_LIST = "proc-list-packet";
const EV_REQUEST_COMPOSITION = "perf-composition-request";
const EV_REQUEST_PROC_KILL = "proc-kill-request";
const EV_REQUEST_ALL_PROCESSES = "all-processes-request";
const EV_REMOVE_TRACKER = "remove-tracker";

const PACKET_PERFORMANCE = "perf-metrics";
const PACKET_PROCESSES = "proc-stats";
const PACKET_TRACKERS = "trackers-approx-data";


function setConnectionStatus(status) {
    let statusEl = document.getElementById("connectionStatus");
    statusEl.setAttribute("status", (status) ? "1" : "0");
}

function onSocketFailure() {
    if (reconnectTimeout) return;
    if (gotPerfComposition) window.location.reload();
    
    setConnectionStatus(false);
    reconnectTimeout = setTimeout(() => {
        reconnectTimeout = null;
        setupSocket();
    }, 1000);
}

function setupSocket() {
    socket = new WebSocket(`ws://${API_ADDRESS}/ws-stream`);

    socket.addEventListener('open', (event) => {
        console.log("Connection opened");
        _sendMessageToServer(EV_REQUEST_COMPOSITION);
        _sendMessageToServer(EV_REQUEST_ALL_PROCESSES);
        fetchHistoricalAlerts();
        fetchTrackableMetrics();
        fetchActiveTrackers();
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

function _sendMessageToServer(evtype, data = {}) {
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
        
        clearPerformancePage(true);

        for (monitor of data) {
            addMonitorHeader(monitor.categoryId, monitor.targetTitle);
            buildDataPage(monitor.categoryId, monitor.targetTitle, monitor.productInfo, monitor.color, monitor.metrics);
        }

        console.log(`Built ${data.length} performance monitors.`);
    }

    if (evtype == EV_UPDATE_PACKET) {
        if (!REALTIME_MODE) return;

        Object.entries(data).forEach(
            ([packetId, updates]) => {
                if (packetId == PACKET_PERFORMANCE) handlePerformanceUpdatePacket(updates);
                if (packetId == PACKET_PROCESSES) handleProcessesUpdatePacket(updates);
                if (packetId == PACKET_TRACKERS) handleTrackersUpdatePacket(updates);
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

    if (evtype == EV_PROCESSES_LIST) {
        handleProcessesUpdatePacket(data);
    }

    if (evtype == EV_RAISE_ALERT) {
        const notificationTitle = `${data.category} - ${data.title}`;
        const notificationDesc = `The alert has been raised for: ${data.title} as: ${data.reason}`;
        sendNotification(notificationTitle, notificationDesc);
        addRaisedAlert(data.category, data.title, data.reason, data.timeinfo, 1);
    }
    
}

