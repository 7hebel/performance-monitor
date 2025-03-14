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
client: fastapi.WebSocket | None = None


@server.websocket("/")
async def handle_ws_connection(websocket: fastapi.WebSocket):
    global client
    
    if client:
        logs.log("Connection", "warn", f"Refused incoming WS connection from: {websocket.client.host}:{websocket.client.port} as current has not been closed.")
        return
        
    await websocket.accept()
    client = websocket 
    
    # Uncommenting this log breaks code...   
    # logs.log("Connection", "info", f"Accepted incoming WS connection from: {websocket.client.host}:{websocket.client.port}")
    
    try:
        composition_data = monitor.prepare_composition_data()
        initial_message = {
            "event": EventType.PERF_COMPOSITION_DATA,
            "data": composition_data
        }
        
        await websocket.send_json(initial_message)
        logs.log("Connection", "info", f"Sent initial message containing {len(composition_data)} monitors.")
        
        while True:
            try:
                data = await websocket.receive_json()
                await handle_message(data)
                
            except fastapi.WebSocketDisconnect:
                logs.log("Connection", "warn", f"Disconnected WS connection with: {websocket.client.host}:{websocket.client.port} (reading error)")
                await websocket.close()
                client = None

    except fastapi.WebSocketDisconnect:
        logs.log("Connection", "warn", f"Disconnected WS connection with: {websocket.client.host}:{websocket.client.port} (connection error)")
        await websocket.close()
        client = None


async def handle_message(msg: dict) -> None:
    event = msg.get("event")
    data = msg.get("data")
    
    if event == EventType.MONIOR_CHANGE:
        logs.log("Connection", "info", f"Switched active category to: `{data}`")
        state.DISPLAYED_CATEGORY = data
    
    
def send_add_monitor(new_monitor: monitor.MonitorBase) -> None:
    if client is None:
        return
    
    monitor_data = monitor.export_monitor(new_monitor)
    message = {
        "event": EventType.PERF_ADD_MONITOR,
        "data": monitor_data
    }
    
    asyncio.run(client.send_json(message))
    logs.log("Connection", "info", f"Sent add-monitor request for monitor: {new_monitor.target_title}")
    
    
def send_remove_monitor(category_id: str) -> None:
    if client is None:
        return
    
    message = {
        "event": EventType.PERF_REMOVE_MONITOR,
        "data": category_id
    }
    
    asyncio.run(client.send_json(message))
    logs.log("Connection", "info", f"Sent remove-monitor request for category: {category_id}")


def start_server(port: int = 50505):
    uvicorn.run(
        server, 
        host="localhost", 
        port=port, 
        log_level="critical",
    )


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
