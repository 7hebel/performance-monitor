import fastapi.middleware
import fastapi.middleware.cors
from modules import history
from modules import monitor
from modules import state
from modules import logs

from enum import StrEnum
import threading
import fastapi
import asyncio
import uvicorn
import time


class EventType(StrEnum):
    # Send:
    PERF_COMPOSITION_DATA = "perf-composition-data"
    PERF_ADD_MONITOR = "perf-add-monitor"
    PERF_REMOVE_MONITOR = "perf-remove-monitor"
    PERF_METRICS_UPDATE = "perf-metrics-update"
    RAISE_ALERT = "raise-alert"
    
    # Receive:
    MONIOR_CHANGE = "monitor-change"


server = fastapi.FastAPI()
server.add_middleware(
    fastapi.middleware.cors.CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client: fastapi.WebSocket | None = None


@server.get("/perf-history/points")
async def get_performance_history_points(request: fastapi.Request) -> fastapi.responses.JSONResponse:
    """
    Return format: 
    {
        "31/12/2025": [
            {
                "cluster": 483875,
                "timeinfo": "12:00 - 12:59"    
            }
        ],
        "01/01/2026": [...]
    }
    """
    all_clusters = history.get_all_clusters()
    dated_clusters = history.prepare_dated_clusters(all_clusters)
    logs.log("History", "info", f"Prepared and sent history points to: {request.client.host}:{request.client.port}")
    return fastapi.responses.JSONResponse(dated_clusters)


@server.websocket("/ws-stream")
async def handle_ws_connection(websocket: fastapi.WebSocket):
    global client
    
    if client:
        logs.log("Connection", "warn", f"Refused incoming WS connection from: {websocket.client.host}:{websocket.client.port} as current has not been closed.")
        return
        
    composition_data = monitor.prepare_composition_data()
    initial_message = {
        "event": EventType.PERF_COMPOSITION_DATA,
        "data": composition_data
    }
    
    logs.log("Connection", "info", f"Accepting incoming WS connection from: {websocket.client.host}:{websocket.client.port}")
    
    await websocket.accept()
    client = websocket 
    
    try:
        await websocket.send_json(initial_message)
        logs.log("Connection", "info", f"Sent initial message containing {len(composition_data)} monitors.")
        
        while True:
            try:
                data = await websocket.receive_json()
                await handle_ws_message(data)
                
            except fastapi.WebSocketDisconnect:
                logs.log("Connection", "warn", f"Disconnected WS connection with: {websocket.client.host}:{websocket.client.port} (reading error)")
                await websocket.close()
                client = None

    except fastapi.WebSocketDisconnect:
        logs.log("Connection", "warn", f"Disconnected WS connection with: {websocket.client.host}:{websocket.client.port} (connection error)")
        await websocket.close()
        client = None


async def handle_ws_message(msg: dict) -> None:
    event = msg.get("event")
    data = msg.get("data")
    
    if event == EventType.MONIOR_CHANGE:
        logs.log("Connection", "info", f"Switched active category to: `{data}`")
        state.DISPLAYED_CATEGORY = data
    

def updates_sender() -> None:
    """ Sent all updates from last second and clean updates queue. """
    global client
    
    while True:
        if client is None:
            continue
        
        updates = state.UPDATES_BUFFER.flush()
        history.handle_updates(updates)
        
        message = {
            "event": EventType.PERF_METRICS_UPDATE,
            "data": updates
        }

        try:
            asyncio.run(client.send_json(message))
        except RuntimeError:
            logs.log("Connection", "warn", f"Disconnected WS connection with: {client.client.host}:{client.client.port} (write error)")
            client = None
            
        time.sleep(1)


threading.Thread(target=updates_sender, daemon=True).start()

def start_server(port: int = 50506):
    uvicorn.run(
        server, 
        host="localhost", 
        port=port, 
        log_level="critical",
    )

