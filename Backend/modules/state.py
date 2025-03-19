from typing import TYPE_CHECKING, Callable
if TYPE_CHECKING:
    from modules import identificators
    from modules import metrics 
    

class UpdatesBuffer[KeyT, ValT]:
    """
    Contain multiple updates from different services. 
    Buffer is flushed by the thread responsible for sync data sending. 
    A flush pipe function can be attached. It will be called with updated contents of this buffer
      every time it's flushed.
    """
    def __init__(self, buffer_name: str) -> None:
        self.buffer_name = buffer_name
        self.updates: dict[KeyT, ValT] = {}
        self._flush_pipe_fn: list[Callable] | None = []
        BUFFERS.append(self)

    def insert_update(self, identifier: KeyT, value: ValT) -> None:
        self.updates[str(identifier)] = value

    def attach_flush_listener(self, listener_fn: Callable[[dict[KeyT, ValT]], None]) -> None:
        self._flush_pipe_fn.append(listener_fn)
        
    def flush(self) -> dict[str: dict[KeyT, ValT]]:
        updates = self.updates.copy()
        self.updates.clear()
        for flush_pipe_fn in self._flush_pipe_fn:
            flush_pipe_fn(updates)
        
        return { self.buffer_name: updates }


BUFFERS: list[UpdatesBuffer] = []

perf_metrics_updates_buffer = UpdatesBuffer["identificators.Identificator | str", "metrics.MetricValueT"]("perf-metrics")
processes_stats_updates_buffer = UpdatesBuffer[str, dict]("proc-stats")
trackers_approx_values_updates_buffer = UpdatesBuffer[str, dict]("trackers-approx-data")
