from modules.identificators import Identificator
from modules import components
from modules import monitor

import psutil
import cpuinfo

cpu_info = cpuinfo.get_cpu_info()


class CPU_Monitor(monitor.MonitorBase):
    def __init__(self) -> None:
        self.target_title = "CPU"
        self.product_info = cpu_info["brand_raw"]
        self.hex_color = "#368ccf"
        self.components_register = [
            components.ChartComponent(
                identificator=Identificator("cpu", "usage-chart"),
                title="Usage (%)",
                getter=lambda: psutil.cpu_percent(interval=0.1),
            ),
            
            components.ComponentsRow(
                components.KeyValueComponent(
                    identificator=Identificator("cpu", "usage-value"),
                    title="Usage",
                    getter=self.get_cpu_usage,
                    important_item=True
                ),
                components.KeyValueComponent(
                    identificator=Identificator("cpu", "processes"),
                    title="Processes",
                    getter=self.get_processes_count,
                    important_item=True
                )
            ),
            
            components.ComponentsRow(
                components.KeyValueComponent(
                    identificator=Identificator("cpu", "base-freq"),
                    title="Base speed",
                    getter=components.StaticValueGetter(cpu_info["hz_actual_friendly"])
                ),
                components.KeyValueComponent(
                    identificator=Identificator("cpu", "logical-cores"),
                    title="Logical cores",
                    getter=components.StaticValueGetter(psutil.cpu_count())
                ),
                components.KeyValueComponent(
                    identificator=Identificator("cpu", "physical-cores"),
                    title="Physical cores",
                    getter=components.StaticValueGetter(psutil.cpu_count(logical=False))
                )
            ),
        ]
        
        self.register_monitor()

    def get_cpu_usage(self) -> str:
        return f"{psutil.cpu_percent(interval=1)}%"

    def get_processes_count(self) -> int:
        return len(list(psutil.process_iter()))
    
    
CPU_Monitor()
