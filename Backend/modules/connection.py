from modules import processes
from modules import tracking
from modules import schemas
from modules import history
from modules import monitor
from modules import state
from modules import logs

from starlette.websockets import WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dataclasses import asdict
from enum import StrEnum
import websocket
import threading
import requests
import fastapi
import uvicorn
import bcrypt
import time
import json
import sys


with open("./config.json", "r") as file:
    CONFIG = json.load(file)

router_address = CONFIG.get("router_address")

server = fastapi.FastAPI()
server.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ws_clients: list[websocket.WebSocket] = []


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


@server.get("/")
async def get_ping() -> JSONResponse:
    return JSONResponse({"status": True})
        
    
# Client connection.

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

@server.post("/trackers/create")
async def create_tracker(tracker: schemas.CreateTrackerRequestModel, request: fastapi.Request) -> JSONResponse:
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


def handle_ws_message(client: websocket.WebSocket, msg: dict) -> None:
    """ Handle messages coming from WebSocket's client. """
    event = msg.get("event")
    data = msg.get("data")

    match event:
        case EventType.PERF_COMPOSITION_REQUEST:
            logs.log("Connection", "info", f"Client requested performance composition data.")
    
            message = {
                "event": EventType.PERF_COMPOSITION_DATA,
                "data": monitor.prepare_composition_data()
            }
            client.send_text(json.dumps(message))

        case EventType.ALL_PROCESSES_REQUEST:
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
            client.send_text(json.dumps(message))

        case EventType.KILL_PROC_REQUEST:
            observer = processes.ProcessObserver.observers.get(data)
            if observer is None:
                return logs.log("Connection", "error", f"Client requested process kill: {data} but no observer is observing this process.")
    
            logs.log("Connection", "info", f"Client requested process kill: {data}")
            observer.try_kill()
        
        case EventType.REMOVE_TRACKER:
            tracking.remove_tracker(data)
            logs.log("Tracking", "warn", f"Client removed tracker: {data}")
    
        case EventType.CLEAR_ALERTS_HISTORY:
            tracking.clear_historical_alerts()
            logs.log("Tracking", "info", F"Client cleared alerts history")


def updates_sender() -> None:
    """ Sent ng updates packets from all buffers. """
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
                ws_client.send_text(json.dumps(message))
        except (RuntimeError, WebSocketDisconnect):
            logs.log("Connection", "warn", f"Disconnected from: {ws_client.client.host}:{ws_client.client.port} (write error)")
            ws_clients.remove(ws_client)


# Router.

def _keepalive_sender():
    while True:
        time.sleep(60)
        requests.get(f"http://{router_address}/keep-alive/{CONFIG["hostname"]}")


def handle_bridge_connection(bridge_id: str) -> None:
    bridge_ws = websocket.create_connection("ws://" + router_address + "/ws-bridge-host/" + CONFIG["hostname"] + "/" + bridge_id)
    connection_resp = bridge_ws.recv()
    if connection_resp != "INIT-OK":
        logs.log("Hosting", "error", f"Failed to create bridge connection: {bridge_id}")
        return

    ws_clients.append(bridge_ws)
    logs.log("Hosting", "info", f"Initialized bridge WS connection: {bridge_id}")
    
    while True:
        client_message = bridge_ws.recv()
        handle_ws_message(bridge_ws, json.loads(client_message))
        
    
# @server.post("/connect")
# async def post_conenct(data: schemas.ClientConnectSchema, request: fastapi.Request) -> JSONResponse:
#     hashed_password = CONFIG.get("password")
#     if hashed_password:
#         if not bcrypt.checkpw(data.password.encode(), hashed_password.encode()):
#             logs.log("Hosting", "warn", "Client provided invalid password via router connection.")
#             return JSONResponse({"status": False, "err_msg": "Invalid password"}, 403)

#     logs.log("Hosting", "info", "Accepting client's connection request from router.")
#     return JSONResponse({"status": True, "err_msg": ""}, 200)


def connect_to_router() -> None:
    try:
        waitroom_ws = websocket.create_connection("ws://" + router_address + f"/ws-host-waitroom/{CONFIG["hostname"]}")
        connection_resp = waitroom_ws.recv()
        if connection_resp != "INIT-OK":
            logs.log("Hosting", "error", f"Failed to register this host to router: {router_address} (received: `{connection_resp}`)")
            sys.exit(1)
            
        logs.log("Hosting", "info", f"Successful host registration to router: {router_address}")
        threading.Thread(target=_keepalive_sender, daemon=True).start()
        
    except ConnectionRefusedError:
        logs.log("Hosting", "error", f"Couldn't register host to the router: {router_address} as it refused connection. (Might be closed)")
        sys.exit(1)

    while True:
        try:
            router_command = waitroom_ws.recv()
            parsed_command = json.loads(router_command)
            handle_router_message(parsed_command["event"], parsed_command["data"])
        except ConnectionResetError:
            logs.log("Hosting", "error", f"Connection closed by the router: {router_address}")
            sys.exit(1)


def handle_router_message(event: str, data: dict | str) -> None:
    if event == "awaitingBridgeWS":
        bridge_id = data
        logs.log("Hosting", "info", f"Initalizing awaiting bridge connection: {bridge_id}")
        threading.Thread(target=handle_bridge_connection, args=(bridge_id,), daemon=True).start()


def start_server(port: int = 50506):
    threading.Thread(target=updates_sender, daemon=True).start()
    threading.Thread(target=connect_to_router, daemon=True).start()
    uvicorn.run(
        server,
        host="0.0.0.0",
        port=port,
        log_level="critical",
    )
