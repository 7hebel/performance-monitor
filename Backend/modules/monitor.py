from modules import components


class MonitorBase:
    target_title: str
    product_info: str
    hex_color: str
    components_register: list[components.ComponentT | components.ComponentsRow]

    def register_monitor(self) -> None:
        MONITORS_REGISTER.append(self)
        print(f"Registered monitor: {self.target_title}")

    def get_category(self) -> str:
        return self.components_register[0].identificator.category
            

MONITORS_REGISTER: list[MonitorBase] = [] 
    
    
def parse_component(component: components.ComponentT) -> dict:
    component_data = {
        "identificator": component.identificator.full(),
        "title": component.title,
        "type": None,
        "details": {
            "staticValue": None
        }
    }
    
    if isinstance(component, components.ChartComponent):
        component_data["type"] = "chart"
    
    if isinstance(component, components.KeyValueComponent):
        component_data["type"] = "keyvalue"
        component_data["details"]["important"] = component.important_item
        
        if isinstance(component.getter, components.StaticValueGetter):
            component_data["details"]["staticValue"] = component.getter()
    
    return component_data
    

def prepare_composition_data() -> list[dict]:
    monitors = []
    
    for monitor in MONITORS_REGISTER:
        monitor_data = {
            "targetTitle": monitor.target_title,
            "productInfo": monitor.product_info,
            "categoryId": monitor.get_category(),
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
    
