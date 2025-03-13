let socket = null;
let reconnectTimeout = null;
let gotComposition = false;

const EV_COMPOSITION_DATA = "composition-data";
const EV_METRICS_UPDATE = "metrics-update";
const EV_RAISE_ALERT = "raise-alert";
const EV_MONITOR_CHANGE = "monitor-change";


function onSocketFailure() {
    if (reconnectTimeout) return;

    reconnectTimeout = setTimeout(() => {
        reconnectTimeout = null;
        setupSocket();
    }, 1000);
}

function setupSocket() {
    socket = new WebSocket('ws://localhost:50505');
    
    socket.addEventListener('message', (event) => {
        const message = JSON.parse(event.data);
        handleMessage(message.event, message.data);
    });
    
    socket.addEventListener('close', (event) => {
        console.log('Connection closed:', event);
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
    if (evtype == EV_COMPOSITION_DATA) {
        if (gotComposition) return;
        gotComposition = true;
        
        for (monitor of data) {
            addMonitorHeader(monitor.categoryId, monitor.targetTitle);
            buildDataPage(monitor.categoryId, monitor.targetTitle, monitor.productInfo, monitor.color, monitor.metrics);
        }
    }

    if (evtype == EV_METRICS_UPDATE) {
        Object.entries(data).forEach(
            ([id, value]) => {
                const element = document.getElementById(id);
                if (element === null) updateChart(id, value);
                else document.getElementById(id).textContent = value;
            }
        )
    }
}

function announceMonitorChange(monitorId) {
    _sendMessageToServer(EV_MONITOR_CHANGE, monitorId)
}
