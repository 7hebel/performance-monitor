from pydantic import BaseModel


class RegisterHostSchema(BaseModel):
    host_name: str
    api_port: int
    authorization: bool
    

class ConnectToHostSchema(BaseModel):
    host_name: str
    password: str | None
    