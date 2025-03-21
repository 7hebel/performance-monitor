from modules import identificators
from modules import state
from modules import logs

from collections.abc import Callable
from dataclasses import dataclass
from threading import Thread
import time

type MetricT = ChartMetric | KeyValueMetric
type MetricValueT = str | int | float


class StaticValueGetter:
    """
    Callable getter that returns same, predefined value.
    Useful in cases like disk's type, size - the values that won't change.
    """
    def __init__(self, value: MetricValueT) -> None:
        self.value = value

    def __call__(self) -> MetricValueT:
        return self.value


def lazy_static_getter(identificator: identificators.Identificator, getter: Callable[[], MetricValueT]) -> StaticValueGetter:
    """
    If obtaining an static information takes too long, using this getter is recomended.
    Creates StaticValueGetter with a placeholder value, starts background evaluation job and
      immediately returns a blank getter. When desired value is calculated in the background process,
      it reports itself to the updates buffer and the change is sent in the next updates packet.
      The value is also assigned to the previously created blank getter, so in case of Frontend
      reconnection it doesn't have to be reevaluated.
    """
    target_static_getter = StaticValueGetter("-")
    timer = logs.CodeTimer()

    def evaluate_and_report() -> None:
        value = getter()
        target_static_getter.value = value
        state.perf_metrics_updates_buffer.insert_update(identificator, value)
        logs.log("LazyGetter", "info", f"Lazy StaticValueGetter finished job for: {identificator.full()} in: {timer.measure()}")

    executor = Thread(target=evaluate_and_report, daemon=True)
    executor.start()

    return target_static_getter


class AsyncReportingValueGetter:
    def __init__(self, metric: MetricT) -> None:
        self.metric = metric
        self._prev_value: MetricValueT | None = None
        self._last_report_t: int | None = None

        self.threaded_getter = Thread(target=self.async_getter_worker, daemon=True)
        self.threaded_getter.start()

    def report_update(self, value: MetricValueT) -> None:
        if self._last_report_t and int(time.time()) - self._last_report_t < 1:
            return # Last report was less than second ago.

        self._last_report_t = int(time.time())
        state.perf_metrics_updates_buffer.insert_update(self.metric.identificator, value)

    def async_getter_worker(self) -> None:
        while True:
            time.sleep(0.1)

            if getattr(self.metric, "_abort_getter", False):
                return

            try:
                new_value = self.metric.getter()

            except Exception as error:
                if not self.metric.suppress_errors:
                    logs.log("AsyncGetterWorker", "error", f"getter of {self.metric.identificator.full()} raised exception: {error}")
                    continue

            # Dont send update if value has not been changed and it is not a chart.
            if not isinstance(self.metric, ChartMetric):
                if new_value == self._prev_value:
                    continue

            self._prev_value = new_value
            self.report_update(new_value)


@dataclass
class ChartMetric:
    identificator: identificators.Identificator
    title: str
    getter: Callable[[], float]
    suppress_errors: bool = False

    def __post_init__(self) -> None:
        AsyncReportingValueGetter(self)


@dataclass
class KeyValueMetric:
    identificator: identificators.Identificator
    title: str
    getter: Callable[[], MetricValueT] | StaticValueGetter
    important_item: bool = False  # Changes style on frontend.
    suppress_errors: bool = False
    trackable: bool = False
    trackable_formatter: Callable[[MetricValueT], int | float] | None = None  
    # ^ Formats .getter()'s readable output to numeric value.
    
    def __post_init__(self) -> None:
        from modules import tracking
        
        if not isinstance(self.getter, StaticValueGetter):
            AsyncReportingValueGetter(self)
            
        if self.trackable:
            tracking.register_trackable_metric(self)


class MetricsRow:
    def __init__(self, *metrics: list[MetricT]) -> None:
        self.metrics = metrics

    def get_all(self) -> list[MetricT]:
        return self.metrics
