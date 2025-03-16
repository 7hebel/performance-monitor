from modules import processes
from modules import history
from modules import monitor
from modules import state
from modules import logs

from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import fastapi
from dataclasses import asdict
from enum import StrEnum
import threading
import asyncio
import uvicorn
import time


server = fastapi.FastAPI()
server.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ws_client: fastapi.WebSocket | None = None


class EventType(StrEnum):
    # Send:
    PERF_COMPOSITION_DATA = "perf-composition-data"
    PERF_ADD_MONITOR = "perf-add-monitor"
    PERF_REMOVE_MONITOR = "perf-remove-monitor"
    PERF_METRICS_UPDATE = "perf-metrics-update"
    PROC_LIST_PACKET = "proc-list-packet"
    UPDATE_PACKET = "update-packet"
    RAISE_ALERT = "raise-alert"

    # Receive:
    PERF_COMPOSITION_REQUEST = "perf-composition-request"
    ALL_PROCESSES_REQUEST = "all-processes-request"
    KILL_PROC_REQUEST = "proc-kill-request"


@server.get("/perf-history/points")
async def get_performance_history_points(request: fastapi.Request) -> JSONResponse:
    """ Return saved history metadata groupped by date. """
    dated_clusters = history.prepare_dated_clusters()
    logs.log("History", "info", f"Prepared and sent history points to: {request.client.host}:{request.client.port}")
    return JSONResponse(dated_clusters)


@server.get("/perf-history/query-cluster/{cluster}")
async def query_performance_history_cluster(cluster: int, request: fastapi.Request) -> JSONResponse:
    """ Returns cluster's content containing historical data from a hour. """
    cluster_data = history.get_cluster(cluster)
    if cluster_data is None:
        logs.log("History", "error", f"Cluster: `{cluster}` query failed for: {request.client.host}:{request.client.port} (not found)")
        return JSONResponse({}, 404)

    logs.log("History", "info", f"Sent cluster: `{cluster}` to: {request.client.host}:{request.client.port}")
    return JSONResponse(cluster_data)


@server.websocket("/ws-stream")
async def handle_ws_connection(websocket: fastapi.WebSocket):
    global ws_client
    if ws_client:
        return logs.log("Connection", "warn", f"Refused incoming WS connection from: {websocket.client.host}:{websocket.client.port} as current has not been closed.")

    # Accept incoming connection and finish handshake.
    await websocket.accept()
    await websocket.send_json({})
    ws_client = websocket
    logs.log("Connection", "info", f"Accepted incoming WS connection from: {websocket.client.host}:{websocket.client.port}")

    # Listen to incoming WS message and delegate them to handler. Detect client's disconnection.
    while True:
        try:
            data = await websocket.receive_json()
            await handle_ws_message(data)

        except fastapi.WebSocketDisconnect:
            logs.log("Connection", "warn", f"Disconnected WS connection with: {websocket.client.host}:{websocket.client.port} (reading error)")
            await websocket.close()
            ws_client = None


async def handle_ws_message(msg: dict) -> None:
    """ Handle messages coming from WebSocket's client. """
    event = msg.get("event")
    data = msg.get("data")

    if event == EventType.PERF_COMPOSITION_REQUEST:
        logs.log("Connection", "info", f"Client requested performance composition data.")

        message = {
            "event": EventType.PERF_COMPOSITION_DATA,
            "data": monitor.prepare_composition_data()
        }
        await ws_client.send_json(message)

    if event == EventType.ALL_PROCESSES_REQUEST:
        logs.log("Connection", "info", f"Client requested all processes data.")

        processes_packet = {}
        for pid, process_observer in processes.ProcessObserver.observers.copy().items():
            process_data = process_observer.grab_processes_data()
            if process_data is not None:
                processes_packet[pid] = asdict(process_data)

        message = {
            "event": EventType.PROC_LIST_PACKET,
            "data": processes_packet
        }
        await ws_client.send_json(message)

    if event == EventType.KILL_PROC_REQUEST:
        observer = processes.ProcessObserver.observers.get(data)
        if observer is None:
            return logs.log("Connection", "error", f"Client requested process kill: {data} but no observer is observing this process.")

        logs.log("Connection", "info", f"Client requested process kill: {data}")
        observer.try_kill()


def updates_sender() -> None:
    """ Sent awaiting updates packets from all buffers. """
    global ws_client

    while True:
        time.sleep(1)
        if ws_client is None:
            continue
        
        # Prepare non-blank buffers packet.
        updates_packet = {}
        for buffer in state.BUFFERS:
            buffer_content = buffer.flush()
            if buffer_content[buffer.buffer_name]:
                updates_packet.update(buffer_content)

        message = {
            "event": EventType.UPDATE_PACKET,
            "data": updates_packet
        }

        try:
            asyncio.run(ws_client.send_json(message))
        except RuntimeError:
            logs.log("Connection", "warn", f"Disconnected from: {ws_client.client.host}:{ws_client.client.port} (write error)")
            ws_client = None


def start_server(port: int = 50506):
    threading.Thread(target=updates_sender, daemon=True).start()
    
    uvicorn.run(
        server,
        host="localhost",
        port=port,
        log_level="critical",
    )
