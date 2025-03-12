from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from modules import identificators
    from modules import components 
    

DISPLAYED_CATEGORY: str | None = None


class ValueUpdatesBuffer:
    """
    Dynamic components will report their updates to this buffer which will be flushed
    by the connection manager and sent as one packet to the frontend.
    """
    
    def __init__(self) -> None:
        self.updates: dict["identificators.Identificator", "components.ComponentValT"] = {}

    def insert_update(self, component_id: "identificators.Identificator", value: "components.ComponentValT") -> None:
        self.updates[component_id.full()] = value
        
    def flush(self) -> dict["identificators.Identificator", "components.ComponentValT"]:
        updates = self.updates.copy()
        self.updates.clear()
        return updates


UPDATES_BUFFER = ValueUpdatesBuffer()

