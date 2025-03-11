from modules import components

from abc import ABC


class MonitorBase(ABC):
    target_title: str
    product_name: str
    hex_color: str
    components_register: list[components.ComponentT | components.ComponentsRow]

    def register_monitor(self) -> None:
        MONITORS_REGISTER.append(self)
    def get_main_chart(self) -> components.ChartComponent | None:
        """ Returns ChartComponent flagged as `main` if any. """
        for component in self.components_register.values():
            if getattr(component, 'main_chart') == True:
                return component
            

MONITORS_REGISTER: list[MonitorBase] = [] 
    
