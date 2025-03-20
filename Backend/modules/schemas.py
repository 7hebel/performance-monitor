from pydantic import BaseModel


class CreateTrackerRequestModel(BaseModel):
    trackedId: str
    stmtOp: str
    limitValue: int | float


class ClientConnectSchema(BaseModel):
    password: str | None
