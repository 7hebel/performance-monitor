from modules.identificators import Identificator
from modules import components
from modules import monitor

import psutil
import wmi

mem_info = psutil.virtual_memory()
MEM_SPEED = wmi.WMI().Win32_PhysicalMemory()[0].Speed


class MEM_Monitor(monitor.MonitorBase):
    def __init__(self) -> None:
        self.target_title = "Memory"
        self.product_info = self.readable_format(mem_info.total)
        self.hex_color = "#a86b32"
        self.components_register = [
            components.ChartComponent(
                identificator=Identificator("mem", "usage-chart"),
                title="Usage (%)",
                min_value=0,
                max_value=100,
                getter=lambda: psutil.virtual_memory().percent,
                main_chart=True
            ),
            
            components.ComponentsRow(
                components.KeyValueComponent(
                    identificator=Identificator("mem", "usage-value"),
                    title="Usage",
                    getter=lambda: f"{psutil.virtual_memory().percent}%",
                    important_item=True
                ),
                components.KeyValueComponent(
                    identificator=Identificator("mem", "used"),
                    title="Used",
                    getter=lambda: self.readable_format(psutil.virtual_memory().used),
                    important_item=True
                ),
                components.KeyValueComponent(
                    identificator=Identificator("mem", "free"),
                    title="Free",
                    getter=lambda: self.readable_format(psutil.virtual_memory().free),
                    important_item=True
                )
            ),
            
            components.KeyValueComponent(
                identificator=Identificator("mem", "speed"),
                title="Speed",
                getter=components.StaticValueGetter(f"{MEM_SPEED} MT/s"),
                important_item=True
            )
        ]
        
        self.register_monitor()
        
    def readable_format(self, b: int) -> str:
        for unit in ("b", "Kb", "Mb", "Gb", "Tb", "Pb"):
            if abs(b) < 1024.0:
                return f"{b:3.1f} {unit}"
            b /= 1024.0

    
MEM_Monitor()
