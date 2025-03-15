from typing import TYPE_CHECKING, Callable
if TYPE_CHECKING:
    from modules import identificators
    from modules import metrics 
    

BUFFERS = []


class _ValueUpdatesBuffer[KeyT, ValT]:
    """
    Contain multiple updates from different services. 
    Buffer is flushed by the thread responsible for sync data sending. 
    A flush pipe function can be attached. It will be called with updated contents of this buffer
      every time it's flushed.
    """
    def __init__(self, buffer_name: str) -> None:
        self.buffer_name = buffer_name
        self.updates: dict[KeyT, ValT] = {}
        self._flush_pipe_fn: Callable | None = None
        BUFFERS.append(self)

    def insert_update(self, metric_id: KeyT, value: ValT) -> None:
        self.updates[metric_id.full()] = value

    def attach_flush_listener(self, listener_fn: Callable[[dict[KeyT, ValT]], None]) -> None:
        self._flush_pipe_fn = listener_fn
        
    def flush(self) -> dict[str: dict[KeyT, ValT]]:
        updates = self.updates.copy()
        self.updates.clear()
        if self._flush_pipe_fn is not None:
            self._flush_pipe_fn(updates)
        
        return { self.buffer_name: updates }


perf_metrics_updates_buffer = _ValueUpdatesBuffer["identificators.Identificator", "metrics.MetricValueT"]("perf-metrics")
# perf_metrics_updates_buffer.attach_flush_listener(history.handle_updates)

processes_stats_updates_buffer = _ValueUpdatesBuffer[str, dict]("proc-stats")
