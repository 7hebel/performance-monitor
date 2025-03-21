import hosts
import logs

from starlette.websockets import WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import fastapi
import uvicorn
import asyncio
import uuid
import json


api = fastapi.FastAPI()
api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

awaiting_assoc_requests: dict[str, dict] = {}


@api.websocket("/ws-host/{hostname}")
async def host_waitroom(hostname: str, host_socket: fastapi.WebSocket) -> None:
    await host_socket.accept()
    logs.log("info", f"Accepted WS host waitroom connection from host: `{hostname}`")

    if hostname in hosts.REGISTERED_HOSTS:
        logs.log("warn", f"Cannot accept incoming WS host waitroom connection as `{hostname}` is already registered.")
        await host_socket.send_text("INIT-ERR")
        return

    host = hosts.Host(hostname, host_socket)
    hosts.REGISTERED_HOSTS[hostname] = host
    logs.log("info", f"Registered host: `{hostname}` ({host_socket.client.host}:{host_socket.client.port})")

    await host_socket.send_text("INIT-OK")

    while True:
        try:
            data = await host_socket.receive_text()
            content = json.loads(data)
            
            if content["event"] == "rejectBridge":
                bridge_id = content["data"]
                await host.ws_bridges[bridge_id]["client"].send_text("INIT-ERR")
                logs.log("warn", f"Host: `{hostname}` actively rejected bridge request: {bridge_id}")
    
            if content["event"] == "assocResponse":
                request_id = content["data"]["_requestId"]
                response = content["data"]["response"]
                awaiting_assoc_requests[request_id] = response
                logs.log("info", f"Host: `{hostname}` fullfiled assocRequest: {request_id}")

        except (RuntimeError, WebSocketDisconnect):
            hosts.REGISTERED_HOSTS.pop(hostname, None)
            logs.log("warn", f"Host: `{hostname}` disconnected abnormally.")
            return
            
            
@api.websocket("/ws-bridge-client/{hostname}")
async def ws_bridge_client(client_socket: fastapi.WebSocket, hostname: str, password: str = None) -> None:
    await client_socket.accept()
        
    host = hosts.REGISTERED_HOSTS.get(hostname)
    if host is None:
        logs.log("warn", f"Cannot accept incoming client bridge request to: {hostname} not found.")
        await client_socket.send_text("INIT-ERR")
        return

    bridge_id = uuid.uuid4().hex
    logs.log("info", f"Accepted client ws bridge request to: {hostname} (bridge: {bridge_id})")    
    await host.awaiting_ws_bridge(bridge_id, client_socket, password)
    await client_socket.send_text("INIT-OK")
    
    while True:
        try:
            message = await client_socket.receive_text()
            host_socket = host.ws_bridges[bridge_id]["host"]
            if host_socket is not None:
                await host_socket.send_text(message)
        except (RuntimeError, WebSocketDisconnect) as error:
            logs.log("error", f"WS-Bridge: `{bridge_id}` error: {error}")
            host.ws_bridges.pop(bridge_id, None)
            return


@api.websocket("/ws-bridge-host/{hostname}/{bridge_id}")
async def ws_bridge_host(hostname: str, bridge_id: str, host_socket: fastapi.WebSocket) -> None:
    await host_socket.accept()

    host = hosts.REGISTERED_HOSTS.get(hostname)
    await host_socket.send_text("INIT-OK")

    host.ws_bridges[bridge_id]["host"] = host_socket

    client_socket = host.ws_bridges[bridge_id]["client"]
    await client_socket.send_text("INIT-OK-HOST")
    
    while True:
        try:
            message = await host_socket.receive_text()
            await client_socket.send_text(message)
        except (RuntimeError, WebSocketDisconnect) as error:
            logs.log("error", f"WS-Bridge: `{bridge_id}` error: {error}")
            host.ws_bridges.pop(bridge_id, None)
            return
    
    
@api.get("/keep-alive/{hostname}")
async def keep_alive_host(hostname: str) -> JSONResponse:
    if hostname not in hosts.REGISTERED_HOSTS:
        logs.log("warn", f"Received keep-alive request for host: {hostname} that is not registered.")
        return JSONResponse({"status": False, "err_msg": f"Host: `{hostname}` is not registered."})
    
    hosts.REGISTERED_HOSTS[hostname].keep_alive()

    
@api.get("/api/{hostname}/{path:path}")
async def bridge_get_request(hostname: str, path: str) -> JSONResponse:
    host = hosts.REGISTERED_HOSTS.get(hostname)
    if host is None:
        logs.log("warn", f"Received bridge GET request: {hostname}/{path} for invalid host.")
        return JSONResponse({"status": False, "err_msg": f"Host: {hostname} not found."})
    
    request_id = uuid.uuid4().hex
    awaiting_assoc_requests[request_id] = None
    
    await host.waitroom_ws.send_json({
        "event": "assocRequest",
        "data": {
            "function": path,
            "_requestId": request_id
        }
    }) 
    
    logs.log("info", f"Sent assocReqeust to exec function `{path}` to: `{hostname}`. Awaitng response: {request_id} ...")
    
    while awaiting_assoc_requests[request_id] is None:
        await asyncio.sleep(0.1)
    
    response = awaiting_assoc_requests[request_id]
    return JSONResponse(response)
    
    
@api.post("/api/{hostname}/{path:path}")  
async def bridge_post_request(hostname: str, path: str, request: fastapi.Request) -> JSONResponse:
    payload = await request.json()
    print(payload)

    host = hosts.REGISTERED_HOSTS.get(hostname)
    if host is None:
        logs.log("warn", f"Received bridge POST request: {hostname}/{path} for invalid host.")
        return JSONResponse({"status": False, "err_msg": f"Host: {hostname} not found."})
    
    request_id = uuid.uuid4().hex
    awaiting_assoc_requests[request_id] = None
    
    await host.waitroom_ws.send_json({
        "event": "assocRequest",
        "data": {
            "function": path,
            "payload": payload,
            "_requestId": request_id
        }
    }) 
    
    logs.log("info", f"Sent assocReqeust to exec function `{path}` to: `{hostname}`. Awaitng response: {request_id} ...")
    
    while awaiting_assoc_requests[request_id] is None:
        await asyncio.sleep(0.1)
    
    response = awaiting_assoc_requests[request_id]
    return JSONResponse(response)


uvicorn.run(api, host="0.0.0.0", port=50507)
