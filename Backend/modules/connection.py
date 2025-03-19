from modules import processes
from modules import tracking
from modules import history
from modules import monitor
from modules import state
from modules import logs

from starlette.websockets import WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dataclasses import asdict
from pydantic import BaseModel
from enum import StrEnum
import threading
import fastapi
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

ws_clients: list[fastapi.WebSocket] = []


class EventType(StrEnum):
    # Send:
    PERF_COMPOSITION_DATA = "perf-composition-data"
    PERF_REMOVE_MONITOR = "perf-remove-monitor"
    PERF_METRICS_UPDATE = "perf-metrics-update"
    PERF_ADD_MONITOR = "perf-add-monitor"
    PROC_LIST_PACKET = "proc-list-packet"
    UPDATE_PACKET = "update-packet"
    RAISE_ALERT = "raise-alert"

    # Receive:
    PERF_COMPOSITION_REQUEST = "perf-composition-request"
    ALL_PROCESSES_REQUEST = "all-processes-request"
    CLEAR_ALERTS_HISTORY = "clear-alerts-history"
    KILL_PROC_REQUEST = "proc-kill-request"
    REMOVE_TRACKER = "remove-tracker"


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

@server.get("/trackers/get-trackable")
async def get_trackable_metrics(request: fastapi.Request) -> JSONResponse:
    """ Returns all trackable metrics' names and ids groupped by category. """
    trackable = tracking.prepare_trackable_metrics_per_category()
    logs.log("Tracking", "info", f"Sent trackable metrics to: {request.client.host}:{request.client.port}")
    return JSONResponse(trackable)

@server.get("/trackers/get-active-trackers")
async def get_active_trackers(request: fastapi.Request) -> JSONResponse:
    """ Returns all active trackers' brief information. """
    active_trackers = tracking.prepare_active_trackers()
    logs.log("Tracking", "info", f"Sent {len(active_trackers)} active trackers data to: {request.client.host}:{request.client.port}")
    return JSONResponse(active_trackers)

@server.get("/trackers/get-historical-alerts")
async def get_historical_alerts(request: fastapi.Request) -> JSONResponse:
    """ Returns all previously recorded alerts. """
    historical_alerts = tracking.load_historical_alerts()
    logs.log("Tracking", "info", f"Sent {len(historical_alerts)} historical alerts to: {request.client.host}:{request.client.port}")
    return JSONResponse(historical_alerts)


class CreateTrackerRequestModel(BaseModel):
    trackedId: str
    stmtOp: str
    limitValue: int | float
    

@server.post("/trackers/create")
async def create_tracker(tracker: CreateTrackerRequestModel, request: fastapi.Request) -> JSONResponse:
    """ Create new tracker using sent data. Returns {'status': True/False, 'err_msg': '...'} based on validation status. """
    metric = tracking.TRACKABLE_METRICS.get(tracker.trackedId)
    if metric is None:
        logs.log("Tracking", "error", f"{request.client.host}:{request.client.port} attempted to create alert on: `{tracker.trackedId}` which is not registered as trackable.")
        return JSONResponse({"status": False, "err_msg": "Invalid metric. (May not exist anymore)"})
    
    if tracker.trackedId in tracking.TRACKERS:
        logs.log("Tracking", "error", f"{request.client.host}:{request.client.port} attempted to create alert on: `{tracker.trackedId}` which is already tracked by another tracker.")
        return JSONResponse({"status": False, "err_msg": "This metric is already tracked."})
    
    if tracker.stmtOp not in "<>":
        logs.log("Tracking", "error", f"{request.client.host}:{request.client.port} attempted to create alert on: `{tracker.trackedId}` but provided invalid statement op: `{tracker.stmtOp}`.")
        return JSONResponse({"status": False, "err_msg": "Invalid statement operator (</>)."})
    
    tracker_meta = tracking.TrackerMeta(
        tracked_id=metric.identificator.full(),
        tracked_name=metric.title,
        target_category=metric.identificator.category,
        stmt_op=tracker.stmtOp,
        stmt_value=tracker.limitValue,
    )
    tracking.add_tracker(tracker_meta)
    
    return JSONResponse({"status": True, "err_msg": ""})


@server.websocket("/ws-stream")
async def handle_ws_connection(websocket: fastapi.WebSocket):
    global ws_clients

    # Accept incoming connection and finish handshake.
    await websocket.accept()
    await websocket.send_json({})
    ws_clients.append(websocket)
    logs.log("Connection", "info", f"Accepted incoming WS connection from: {websocket.client.host}:{websocket.client.port} (total clients: {len(ws_clients)})")

    # Listen to incoming WS message and delegate them to handler. Detect client's disconnection.
    while True:
        try:
            data = await websocket.receive_json()
            await handle_ws_message(websocket, data)

        except fastapi.WebSocketDisconnect:
            logs.log("Connection", "warn", f"Disconnected WS connection with: {websocket.client.host}:{websocket.client.port} (reading error)")
            await websocket.close()
            ws_clients.remove(websocket)


async def handle_ws_message(client: fastapi.WebSocket, msg: dict) -> None:
    """ Handle messages coming from WebSocket's client. """
    event = msg.get("event")
    data = msg.get("data")

    match event:
        case EventType.PERF_COMPOSITION_REQUEST:
            logs.log("Connection", "info", f"Client: {client.client.host}:{client.client.port} requested performance composition data.")
    
            message = {
                "event": EventType.PERF_COMPOSITION_DATA,
                "data": monitor.prepare_composition_data()
            }
            await client.send_json(message)

        case EventType.ALL_PROCESSES_REQUEST:
            logs.log("Connection", "info", f"Client: {client.client.host}:{client.client.port} requested all processes data.")
    
            processes_packet = {}
            for pid, process_observer in processes.ProcessObserver.observers.copy().items():
                process_data = process_observer.grab_processes_data()
                if process_data is not None:
                    processes_packet[pid] = asdict(process_data)
    
            message = {
                "event": EventType.PROC_LIST_PACKET,
                "data": processes_packet
            }
            await client.send_json(message)

        case EventType.KILL_PROC_REQUEST:
            observer = processes.ProcessObserver.observers.get(data)
            if observer is None:
                return logs.log("Connection", "error", f"Client: {client.client.host}:{client.client.port} requested process kill: {data} but no observer is observing this process.")
    
            logs.log("Connection", "info", f"Client: {client.client.host}:{client.client.port} requested process kill: {data}")
            observer.try_kill()
        
        case EventType.REMOVE_TRACKER:
            tracking.remove_tracker(data)
            logs.log("Tracking", "warn", f"Client: {client.client.host}:{client.client.port} removed tracker: {data}")
    
        case EventType.CLEAR_ALERTS_HISTORY:
            tracking.clear_historical_alerts()
            logs.log("Tracking", "info", "Client: {client.client.host}:{client.client.port} cleared alerts history")


def updates_sender() -> None:
    """ Sent awaiting updates packets from all buffers. """
    global ws_clients

    while True:
        time.sleep(1)
        if not ws_clients:
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
            for ws_client in ws_clients:
                asyncio.run(ws_client.send_json(message))
        except (RuntimeError, WebSocketDisconnect):
            logs.log("Connection", "warn", f"Disconnected from: {ws_client.client.host}:{ws_client.client.port} (write error)")
            ws_clients.remove(ws_client)


def start_server(port: int = 50506):
    threading.Thread(target=updates_sender, daemon=True).start()
    
    uvicorn.run(
        server,
        host="localhost",
        port=port,
        log_level="critical",
    )
