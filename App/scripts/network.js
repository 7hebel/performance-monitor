
function measurePing() {
    const resultEl = document.getElementById("pingResult"); 
    const address = document.getElementById("pingDest").value;

    const options = {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            address: address
        })
    };
    
    
    fetch(HTTP_PROTO + "://" + ROUTER_ADDRESS + "/api/" + HOSTNAME + "/net/ping", options)
        .then(response => response.json())
        .then(result => {
            if (!result.status) {
                resultEl.textContent = resultEl.err_msg;
            } else {
                resultEl.textContent = result.ping + " " + result.host + " " + result.ip;
            }
        })
        .catch(error => {
            console.error('Error while sending PING request', error);
        });
}


function traceRoute() {
    const address = document.getElementById("traceDest").value;
    _sendMessageToServer(EV_TRACE_ROUTE, address);
    Array.from(document.getElementById("traceRoute").children).forEach(el => {
        if (el.className != "trackersInfo") el.remove();
    })
}


