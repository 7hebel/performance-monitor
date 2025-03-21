import hosts
import logs

from starlette.websockets import WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import requests
import fastapi
import uvicorn
import uuid


api = fastapi.FastAPI()
api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@api.websocket("/ws-host-waitroom/{hostname}")
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
    await host_socket.receive()


@api.websocket("/ws-bridge-client/{hostname}")
async def ws_bridge_client(hostname: str, client_socket: fastapi.WebSocket) -> None:
    await client_socket.accept()
        
    host = hosts.REGISTERED_HOSTS.get(hostname)
    if host is None:
        logs.log("warn", f"Cannot accept incoming client bridge request to: {hostname} not found.")
        await client_socket.send_text("INIT-ERR")
        return

    bridge_id = uuid.uuid4().hex
    logs.log("info", f"Accepted client ws bridge request to: {hostname} (bridge: {bridge_id})")    
    await host.awaiting_ws_bridge(bridge_id, client_socket)
    await client_socket.send_text("INIT-OK")

    while True:
        message = await client_socket.receive_text()
        host_socket = host.ws_bridges[bridge_id]["host"]
        if host_socket is not None:
            await host_socket.send_text(message)


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
        except WebSocketDisconnect:
            logs.log("error", f"Host: {hostname} disconnected from bridge: {bridge_id}")
            hosts.REGISTERED_HOSTS.pop(hostname, None)

    
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
    
    print(path)
    
    host_adress = f"http://{host.waitroom_ws.client.host}:50506/"
    if host.waitroom_ws.client.host == "::1":
        host_adress = f"http://localhost:50506/"
        
    host_resp = requests.get(host_adress + path).json()
    return JSONResponse(host_resp)
    
    

uvicorn.run(api, host="0.0.0.0", port=50507)
# uvicorn.run(api, host="localhost", port=50507)
