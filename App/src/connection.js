let socket = null;
let reconnectTimeout = null;

function onSocketFailure() {
    if (reconnectTimeout) return;

    console.log("Connection failed. Attempting to reconnect in 5 seconds...");
    reconnectTimeout = setTimeout(() => {
        reconnectTimeout = null;
        setupSocket();
    }, 5000);
}

function setupSocket() {
    if (socket) {
        try {
            socket.close();
        } catch (e) {
            console.warn("Error closing previous socket:", e);
        }
    }

    socket = new WebSocket('ws://localhost:50505');
    console.log(socket)

    socket.addEventListener('open', (event) => {
        console.log('Connected to WebSocket server on ws://localhost:50505');
    });

    socket.addEventListener('message', (event) => {
        console.log('Received:', event.data);
    });

    socket.addEventListener('close', (event) => {
        console.log('Connection closed:', event.reason);
        onSocketFailure();
    });

    socket.addEventListener('error', (error) => {
        console.error('WebSocket error:', error);
        onSocketFailure();
    });
}

setupSocket();

function _sendMessageToServer(evtype, data) {
    const message = {
        event: evtype,
        data: data
    };

    socket.send(JSON.stringify(message));
}
