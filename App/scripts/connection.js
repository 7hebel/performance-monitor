const HTTP_PROTO = "http";
// const ROUTER_ADDRESS = "space7.smallhost.pl:50507";
const ROUTER_ADDRESS = "localhost:50507";
let HOSTNAME = null;
let API_ADDRESS = "";

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
const EV_CLEAR_ALERTS_HISTORY = "clear-alerts-history";

const PACKET_PERFORMANCE = "perf-metrics";
const PACKET_PROCESSES = "proc-stats";
const PACKET_TRACKERS = "trackers-approx-data";


function setConnectionStatus(status) {
    let statusEl = document.getElementById("connectionStatus");
    statusEl.setAttribute("status", (status) ? "1" : "0");
}

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
        Object.entries(data).forEach(
            ([packetId, updates]) => {
                if (packetId == PACKET_PERFORMANCE && REALTIME_MODE) handlePerformanceUpdatePacket(updates);
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


function requestConnection() {
    const hostname = document.getElementById("connectionHostname").value;
    const password = document.getElementById("connectionPassword").value;
    
    socket = new WebSocket(`ws://${ROUTER_ADDRESS}/ws-bridge-client/${hostname}?password=${window.btoa(password)}`);

    socket.addEventListener('open', (event) => {
        console.log("Connection opened");
    });
    
    socket.addEventListener('message', (event) => {
        if (event.data == "INIT-ERR") {
            document.getElementById("connectionError").textContent = "Invalid credentials.";
            return;
        }
        if (event.data == "INIT-OK") { return; }
        if (event.data == "INIT-OK-HOST") {
            document.getElementById("connectionPanel").setAttribute("active", "0");
            setConnectionStatus(true);
            HOSTNAME = hostname;

            _sendMessageToServer(EV_REQUEST_COMPOSITION);
            _sendMessageToServer(EV_REQUEST_ALL_PROCESSES);
            fetchHistoricalAlerts();
            fetchTrackableMetrics();
            fetchActiveTrackers();
            return;
        }
        
        const message = JSON.parse(event.data);
        handleMessage(message.event, message.data);
    });

    socket.addEventListener('close', (event) => {
        console.log('Connection closed:', event);
        window.location.reload();
    });

    socket.addEventListener('error', (error) => { console.error(error) });

}
