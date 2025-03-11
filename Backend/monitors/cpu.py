from modules.identificators import Identificator
from modules import components
from modules import monitor

import psutil
import cpuinfo
import wmi

wmi_client = wmi.WMI().Win32_Processor()[0]
cpu_info = cpuinfo.get_cpu_info()


class CPU_Monitor(monitor.MonitorBase):
    def __init__(self) -> None:
        self.target_title = "CPU"
        self.product_name = cpu_info["brand_raw"]
        self.hex_color = "#368ccf"
        self.components_register = [
            components.ChartComponent(
                identificator=Identificator("cpu", "usage-chart"),
                title="Usage (%)",
                min_value=0,
                max_value=100,
                getter=lambda: psutil.cpu_percent(interval=1),
                main_chart=True
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
                    getter=components.StaticValueGetter(psutil.cpu_count)
                ),
                components.KeyValueComponent(
                    identificator=Identificator("cpu", "physical-cores"),
                    title="Physical cores",
                    getter=components.StaticValueGetter(self.get_physical_cores)
                )
            ),
            
            components.ComponentsRow(
                components.KeyValueComponent(
                    identificator=Identificator("cpu", "l2-size"),
                    title="L2 Cache size",
                    getter=components.StaticValueGetter(wmi_client.L2CacheSize)
                ),
                components.KeyValueComponent(
                    identificator=Identificator("cpu", "l3-size"),
                    title="L3 Cache size",
                    getter=components.StaticValueGetter(wmi_client.L3CacheSize)
                )
            )
        ]
        
        self.register_monitor()

    def get_cpu_usage(self) -> str:
        return f"{psutil.cpu_percent(interval=1)} %"

    def get_processes_count(self) -> int:
        return len(list(psutil.process_iter()))
    
    def get_physical_cores(self) -> int:
        return psutil.cpu_count(logical=False)
    
    
CPU_Monitor()
