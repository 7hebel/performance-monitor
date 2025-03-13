from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from modules import identificators
    from modules import metrics 
    

DISPLAYED_CATEGORY: str | None = None


class _ValueUpdatesBuffer:
    """
    Dynamic metrics will report their updates to this buffer which will be flushed
    by the connection manager and sent as one packet to the frontend.
    """
    def __init__(self) -> None:
        self.updates: dict["identificators.Identificator", "metrics.MetricValueT"] = {}

    def insert_update(self, metric_id: "identificators.Identificator", value: "metrics.MetricValueT") -> None:
        self.updates[metric_id.full()] = value
        
    def flush(self) -> dict["identificators.Identificator", "metrics.MetricValueT"]:
        updates = self.updates.copy()
        self.updates.clear()
        return updates


UPDATES_BUFFER = _ValueUpdatesBuffer()
