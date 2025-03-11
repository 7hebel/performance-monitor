from modules import identificators

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from modules import components

from enum import StrEnum
import fastapi
import asyncio
import uvicorn
import time


class ValueUpdatesBuffer:
    """
    Dynamic components will report their updates to this buffer which will be flushed
    by the connection manager and sent as one packet to the frontend.
    """
    
    def __init__(self) -> None:
        self.updates: dict["identificators.Identificator", "components.ComponentValT"] = {}

    def insert_update(self, component_id: "identificators.Identificator", value: "components.ComponentValT") -> None:
        self.updates[component_id] = value
        
    def flush(self) -> dict["identificators.Identificator", "components.ComponentValT"]:
        updates = self.updates
        self.updates.clear()
        return updates


UPDATES_BUFFER = ValueUpdatesBuffer()


server = fastapi.FastAPI()
client: fastapi.WebSocket | None = None


class EventType(StrEnum):
    COMPOSITION_DATA = "composition-data"
    COMPONENTS_UPDATE = "components-update"
    RAISE_ALERT = "raise-alert"


@server.websocket("/")
async def handle_ws_connection(websocket: fastapi.WebSocket):
    global client
    
    await websocket.accept()
    client = websocket    
    
    try:
        while True:
            data = await websocket.receive_json()
            await handle_message(data)

    except fastapi.WebSocketDisconnect:
        print("Disconnected.")

async def handle_message(msg: dict) -> None:
    event = msg.get("event")
    data = msg.get("data")
    

def start_server():
    uvicorn.run(
        server, 
        host="localhost", 
        port=50505, 
        log_level="critical"
    )
