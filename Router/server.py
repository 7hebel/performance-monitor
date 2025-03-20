import req_schemas
import hosts
import logs

from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import fastapi
import uvicorn
import sys


api = fastapi.FastAPI()
api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@api.post("/register-host")
async def post_register_host(data: req_schemas.RegisterHostSchema, request: fastapi.Request) -> JSONResponse:
    if len(data.host_name) < 3:
        return JSONResponse({"status": False, "err_msg": f"host_name must be at least 3 characters long."}, 400)
    if data.host_name in hosts.REGISTERED_HOSTS:
        return JSONResponse({"status": False, "err_msg": f"Host with name `{data.host_name}` is already registered"}, 400)

    host = hosts.Host(data.host_name, request.client.host, data.api_port, data.authorization)
    hosts.REGISTERED_HOSTS[data.host_name] = host
    logs.log("info", f"Registered host: `{host.host_name}` (secure: {host.authorization}) (requested by: {request.client.host}:{request.client.port})")


@api.post("/connect")
async def post_connect(data: req_schemas.ConnectToHostSchema, request: fastapi.Request) -> JSONResponse:
    if data.host_name not in hosts.REGISTERED_HOSTS:
        return JSONResponse({"status": False, "err_msg": f"Host: `{data.host_name}` not found"}, 400)
    
    host = hosts.REGISTERED_HOSTS.get(data.host_name)
    
    if not data.password and host.authorization:
        return JSONResponse({"status": False, "err_msg": f"Host: `{data.host_name}` requires password."}, 400)
    
    response = host.connect_client(data.password)
    return JSONResponse(response)
    

uvicorn.run(api, port=50507)
