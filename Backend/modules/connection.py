from modules import monitor
from modules import state

from enum import StrEnum
import threading
import fastapi
import asyncio
import uvicorn
import time


class EventType(StrEnum):
    # Send:
    COMPOSITION_DATA = "composition-data"
    COMPONENTS_UPDATE = "components-update"
    RAISE_ALERT = "raise-alert"
    
    # Receive:
    MONIOR_CHANGE = "monitor-change"


server = fastapi.FastAPI()
client: fastapi.WebSocket | None = None


@server.websocket("/")
async def handle_ws_connection(websocket: fastapi.WebSocket):
    global client
    
    await websocket.accept()
    client = websocket    
    print(f"* Accepted client connection from: {websocket.client.port}")
    
    try:
        composition_data = monitor.prepare_composition_data()
        initial_message = {
            "event": EventType.COMPOSITION_DATA,
            "data": composition_data
        }
        await websocket.send_json(initial_message)
        
        while True:
            data = await websocket.receive_json()
            await handle_message(data)

    except fastapi.WebSocketDisconnect:
        print(f"- Disconnected: {websocket.client.port}.")
        await websocket.close()
        client = None


async def handle_message(msg: dict) -> None:
    event = msg.get("event")
    data = msg.get("data")
    
    if event == EventType.MONIOR_CHANGE:
        print(f"Changed displayed category to: {data}")
        state.DISPLAYED_CATEGORY = data
    

def start_server(port: int = 50505):
    print(f"* Starting WS server on localhost:{port}")

    uvicorn.run(
        server, 
        host="localhost", 
        port=port, 
        log_level="critical",
    )


def updates_sender() -> None:
    """ Sent all updates from last second and clean updates queue. """
    while True:
        if client is None:
            continue
        
        updates = state.UPDATES_BUFFER.flush()
        message = {
            "event": EventType.COMPONENTS_UPDATE,
            "data": updates
        }

        asyncio.run(client.send_json(message))
        time.sleep(1)


threading.Thread(target=updates_sender, daemon=True).start()
