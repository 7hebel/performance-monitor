from modules import processes
from modules import tracking
from modules import history
from modules import monitor
from modules import state
from modules import logs

from urllib.parse import unquote
from dataclasses import asdict
from enum import StrEnum
import websocket
import threading
import requests
import base64
import bcrypt
import time
import json
import sys


with open("./config.json", "r") as file:
    CONFIG = json.load(file)

router_address = CONFIG.get("router_address") + ":50507"
ws_clients: list[websocket.WebSocket] = []
host_ws: websocket.WebSocket | None = None


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


def connect_to_router() -> None:
    """
    Establish connection with the Router's ws-host server.
    Register this host, keep connection alive, handle messages from router.
    Connect to clients via Router's WS-Bridges.
    Execute and respond to the associative requests. 
    """
    global host_ws
    
    def _keep_alive():
        while True:
            time.sleep(60)
            requests.get(f"http://{router_address}/keep-alive/{CONFIG["hostname"]}")
    
    try:
        host_ws = websocket.create_connection("ws://" + router_address + f"/ws-host/{CONFIG["hostname"]}")
        connection_resp = host_ws.recv()
        if connection_resp != "INIT-OK":
            logs.log("Hosting", "error", f"Failed to register this host to router: {router_address} (received: `{connection_resp}`)")
            sys.exit(1)
            
        logs.log("Hosting", "info", f"Successful host: `{CONFIG["hostname"]}` registration to router: {router_address}")
        threading.Thread(target=_keep_alive, daemon=True).start()
        
    except ConnectionRefusedError:
        logs.log("Hosting", "error", f"Couldn't register host to the router: {router_address} as it refused connection. (Might be closed)")
        sys.exit(1)

    while True:
        try:
            router_command = json.loads(host_ws.recv())
            handle_router_message(router_command["event"], router_command["data"])
        except ConnectionResetError:
            logs.log("Hosting", "error", f"Connection closed by the router: {router_address}")
            sys.exit(1)
            

def send_assoc_request_response(request_id: str, data: dict) -> None:
    host_ws.send_text(json.dumps({
        "event": "assocResponse",
        "data": {
            "response": data,
            "_requestId": request_id
        }
    }))
    

def handle_router_message(event: str, data: dict | str) -> None:
    if event == "awaitingBridgeWS":
        bridge_id = data["bridgeId"]
        password = base64.b64decode(unquote(data["password"]))

        hashed_password = CONFIG.get("password")
        if hashed_password:
            if not bcrypt.checkpw(password, hashed_password.encode()):
                logs.log("Hosting", "warn", "Client provided invalid password via router connection.")
                host_ws.send_text(json.dumps({
                    "event": "rejectBridge",
                    "data": bridge_id,
                }))
                return
        
        logs.log("Hosting", "info", f"Initalizing awaiting bridge connection: {bridge_id}")
        threading.Thread(target=connect_to_bridge_connection, args=(bridge_id,), daemon=True).start()

    if event == "assocRequest":
        request_id = data["_requestId"]
        function = data["function"]

        if function == "perf-history/points":
            send_assoc_request_response(
                request_id, history.prepare_dated_clusters()
            )

        if function == "trackers/get-trackable":
            send_assoc_request_response(
                request_id, tracking.prepare_trackable_metrics_per_category()
            )

        if function == "trackers/get-active-trackers":
            send_assoc_request_response(
                request_id, tracking.prepare_active_trackers()
            )
            
        if function == "trackers/get-historical-alerts":
            send_assoc_request_response(
                request_id, tracking.load_historical_alerts()
            )
            
        if function.startswith("perf-history/query-cluster/"):
            cluster_number = int(function.split("/")[-1])
            cluster_data = history.get_cluster(cluster_number)
            send_assoc_request_response(request_id, cluster_data)
            
        if function == "trackers/create":
            data = data["payload"]
            metric = tracking.TRACKABLE_METRICS.get(data["trackedId"])
            if metric is None:
                logs.log("Tracking", "error", f"Client attempted to create alert on: `{data["trackedId"]}` which is not registered as trackable.")
                send_assoc_request_response(
                    request_id, {"status": False, "err_msg": "Invalid metric. (May not exist anymore)"}
                )
            
            if data["trackedId"] in tracking.TRACKERS:
                logs.log("Tracking", "error", f"Client attempted to create alert on: `{data["trackedId"]}` which is already tracked by another tracker.")
                send_assoc_request_response(
                    request_id, {"status": False, "err_msg": "This metric is already tracked."}
                )
            
            if data["stmtOp"] not in "<>":
                logs.log("Tracking", "error", f"Client attempted to create alert on: `{data["trackedId"]}` but provided invalid statement op: `{data["stmtOp"]}`.")
                send_assoc_request_response(
                    request_id, {"status": False, "err_msg": "Invalid statement operator (</>)."}
                )
            
            tracker_meta = tracking.TrackerMeta(
                tracked_id=metric.identificator.full(),
                tracked_name=metric.title,
                target_category=metric.identificator.category,
                stmt_op=data["stmtOp"],
                stmt_value=data["limitValue"],
            )
            tracking.add_tracker(tracker_meta)
            
            send_assoc_request_response(
                request_id, {"status": True, "err_msg": ""}
            )


def connect_to_bridge_connection(bridge_id: str) -> None:
    bridge_ws = websocket.create_connection("ws://" + router_address + "/ws-bridge-host/" + CONFIG["hostname"] + "/" + bridge_id)
    connection_resp = bridge_ws.recv()
    if connection_resp != "INIT-OK":
        logs.log("Hosting", "error", f"Failed to create bridge connection: {bridge_id}")
        return

    ws_clients.append(bridge_ws)
    logs.log("Hosting", "info", f"Initialized bridge WS connection: {bridge_id}")
    
    while True:
        try:
            client_message = bridge_ws.recv()
            handle_client_ws_message(bridge_ws, json.loads(client_message))
        except Exception as error:
            logs.log("Hosting", "error", f"WS-Bridge: {bridge_id} connection failed: {error}")
            ws_clients.remove(bridge_ws)
            return
    
def handle_client_ws_message(client: websocket.WebSocket, msg: dict) -> None:
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
            for pid, process_observer in processes.ProcessesObserver.observers.copy().items():
                process_data = process_observer.grab_processes_data()
                if process_data is not None:
                    processes_packet[pid] = asdict(process_data)
    
            message = {
                "event": EventType.PROC_LIST_PACKET,
                "data": processes_packet
            }
            client.send_text(json.dumps(message))

        case EventType.KILL_PROC_REQUEST:
            observer = processes.ProcessesObserver.observers.get(data)
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


def updates_packet_sender() -> None:
    """ Sent update packets from all buffers. """
    global ws_clients

    while True:
        time.sleep(1)
        if not ws_clients:
            continue
        
        # Prepare non-blank buffers packet.
        updates_packet = {}
        for buffer in state.UPDATES_BUFFERS:
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
        except Exception:
            logs.log("Connection", "warn", f"Disconnected from client (write error)")
            ws_clients.remove(ws_client)


def start_server():
    threading.Thread(target=updates_packet_sender, daemon=True).start()

    try:
        connect_to_router()
    except Exception as error:
        logs.log("Hosting", "error", f"Router connection error: {error}")
        sys.exit(1)

