import logs

from dataclasses import dataclass
import requests


@dataclass
class Host:
    host_name: str
    host: str
    port: int
    authorization: bool
    
    def connect_client(self, password: str | None) -> dict:
        try:
            host_connection_resp = requests.post(f"http://{self.host}:{self.port}/connect", json={
                "password": password
            })
            
            if host_connection_resp.status_code == 200:
                return {"status": True, "err_msg": "", "host": f"{self.host}:{self.port}"}
            
            if host_connection_resp.status_code == 403:
                return {"status": False, "err_msg": "Invalid password."}
            
            logs.log(f"Host: {self.host_name} returned invalid response: {host_connection_resp.status_code} ({host_connection_resp.text})")
            return {"status": False, "err_msg": "Invalid host response."}
            
        except Exception as error:
            logs.log(f"Connecting client to: {self.host_name} failed: {error}")
            return {"status": False, "err_msg": "Internal error."}
    
    
REGISTERED_HOSTS: dict[str, Host] = {}
