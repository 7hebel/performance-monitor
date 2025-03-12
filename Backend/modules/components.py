from modules import identificators
from modules import state

from collections.abc import Callable
from dataclasses import dataclass
from threading import Thread
import time

type ComponentT = ChartComponent | KeyValueComponent
type ComponentValT = str | int | float


class StaticValueGetter:
    """
    Callable getter that returns same, predefined value.
    Useful in cases like disk's type, size - the values that won't change. 
    """
    def __init__(self, value: ComponentValT) -> None:
        self.value = value
    
    def __call__(self) -> ComponentValT:
        return self.value
    
    
class AsyncReportingValueGetter:
    def __init__(self, component: ComponentT) -> None:
        self.component = component
        self._prev_value: ComponentValT | None = None
        self._last_report_t: int | None = None
        
        self.threaded_getter = Thread(target=self.async_getter_worker, daemon=False)
        self.threaded_getter.start()
            
    def is_value_requested(self) -> bool:
        """
        To avoid unuseful getter's calls, check if value from this getter 
        is required by the app's state.
        """
        return state.DISPLAYED_CATEGORY == self.component.identificator.category or isinstance(self.component, ChartComponent)
            
    def report_update(self, value: ComponentValT) -> None:
        if self._last_report_t and int(time.time()) - self._last_report_t < 1:
            return # Last report was less than second ago.
        
        # print(f"REPORT: {self.component.identificator} :: {value}")
        self._last_report_t = int(time.time())
        state.UPDATES_BUFFER.insert_update(self.component.identificator, value)
            
    def async_getter_worker(self) -> None:
        while True:
            time.sleep(0.01)
            if not self.is_value_requested():
                continue
            
            new_value = self.component.getter()
            
            if not isinstance(self.component, ChartComponent):
                if new_value == self._prev_value:
                    # Dont send update if value has not been changed and it is not a chart.
                    continue
                
            self._prev_value = new_value
            self.report_update(new_value)
            

@dataclass
class ChartComponent:
    identificator: identificators.Identificator
    title: str
    getter: Callable[[], float]    

    def __post_init__(self) -> None:
        AsyncReportingValueGetter(self)
    
    def as_dict(self) -> dict:
        pass
    
    
@dataclass
class KeyValueComponent:
    identificator: identificators.Identificator
    title: str
    getter: Callable[[], ComponentValT] | StaticValueGetter
    important_item: bool = False  # Changes style on frontend.
    
    def __post_init__(self) -> None:
        if not isinstance(self.getter, StaticValueGetter):
            AsyncReportingValueGetter(self)
    
    
class ComponentsRow:
    def __init__(self, *components: list[ComponentT]) -> None:
        self.components = components
        
    def get_all(self) -> list[ComponentT]:
        return self.components


