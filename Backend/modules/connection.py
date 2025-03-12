from modules import monitor

from enum import StrEnum
import fastapi
import uvicorn


class EventType(StrEnum):
    COMPOSITION_DATA = "composition-data"
    COMPONENTS_UPDATE = "components-update"
    RAISE_ALERT = "raise-alert"


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


async def handle_message(msg: dict) -> None:
    print(msg)
    event = msg.get("event")
    data = msg.get("data")
    

def start_server(port: int = 50505):
    print(f"* Starting WS server on localhost:{port}")

    uvicorn.run(
        server, 
        host="localhost", 
        port=port, 
        log_level="critical"
    )

