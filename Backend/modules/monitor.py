from modules import components


class MonitorBase:
    target_title: str
    product_info: str
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
    
    
def parse_component(component: components.ComponentT) -> dict:
    component_data = {
        "identificator": component.identificator.full(),
        "title": component.title,
        "type": None,
        "details": {}
    }
    
    if isinstance(component, components.ChartComponent):
        component_data["type"] = "chart"
        component_data["details"]["min"] = component.min_value
        component_data["details"]["max"] = component.max_value
        component_data["details"]["main"] = component.main_chart
    
    if isinstance(component, components.KeyValueComponent):
        component_data["type"] = "keyvalue"
        component_data["details"]["important"] = component.important_item
    
    return component_data
    

def prepare_composition_data() -> list[dict]:
    monitors = []
    
    print(MONITORS_REGISTER)
    for monitor in MONITORS_REGISTER:
        monitor_data = {
            "target-title": monitor.target_title,
            "product-info": monitor.product_info,
            "color": monitor.hex_color,
            "components": []
        }
        
        for component_or_row in monitor.components_register:
            if not isinstance(component_or_row, components.ComponentsRow):
                component_data = parse_component(component_or_row)
                monitor_data["components"].append(component_data)
                continue
            
            row_components = [parse_component(c) for c in component_or_row.get_all()]
            monitor_data["components"].append(row_components)
            
        monitors.append(monitor_data)    
        
    return monitors
    
