import logs

from dataclasses import dataclass
from fastapi import WebSocket
import threading
import time


@dataclass
class Host:
    hostname: str
    waitroom_ws: WebSocket

    def __post_init__(self) -> None:
        self.__keep_alive_t = int(time.time())
        self.ws_bridges: dict[str, dict[str, WebSocket]] = {}  # {bridgeId: {"client": WS, "host": WS}}

    
    async def awaiting_ws_bridge(self, bridge_id: str, client_socket: WebSocket, password: str) -> None:
        await self.waitroom_ws.send_json({
            "event": "awaitingBridgeWS",
            "data": {
                "bridgeId": bridge_id,
                "password": password
            }
        })
        self.ws_bridges[bridge_id] = {"client": client_socket, "host": None}
        logs.log("info", f"Informed host: {self.hostname} about awaiting WS Bridge: {bridge_id}")

        
    def keep_alive(self) -> None:
        self.__keep_alive_t = int(time.time())
    
    def is_alive(self) -> bool:
        return int(time.time()) - self.__keep_alive_t < (60 * 3)
    
    
REGISTERED_HOSTS: dict[str, Host] = {}


def alive_checker() -> None:
    while True:
        for hostname, host in REGISTERED_HOSTS.copy().items():
            if not host.is_alive():
                logs.log("warn", f"Disconnecting not alive host: {hostname}")
                REGISTERED_HOSTS.pop(hostname)
                
        time.sleep(60 * 3)
        
threading.Thread(target=alive_checker, daemon=True).start()
