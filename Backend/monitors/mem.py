from modules.identificators import Identificator
from modules import metrics
from modules import monitor

import psutil


mem_info = psutil.virtual_memory()

def get_mem_speed() -> str:
    import wmi
    speed = wmi.WMI().Win32_PhysicalMemory()[0].Speed
    return f"{speed} MT/s"


class MEM_Monitor(monitor.MonitorBase):
    def __init__(self) -> None:
        self.target_title = "Memory"
        self.product_info = self.readable_format(mem_info.total)
        self.hex_color = "#eb923f"
        self.metrics_struct = [
            metrics.ChartMetric(
                identificator=Identificator("mem", "usage-chart"),
                title="Usage (%)",
                getter=lambda: psutil.virtual_memory().percent,
            ),
            
            metrics.MetricsRow(
                metrics.KeyValueMetric(
                    identificator=Identificator("mem", "usage-value"),
                    title="Usage",
                    getter=lambda: f"{psutil.virtual_memory().percent}%",
                    important_item=True
                ),
                metrics.KeyValueMetric(
                    identificator=Identificator("mem", "used"),
                    title="Used",
                    getter=lambda: self.readable_format(psutil.virtual_memory().used),
                    important_item=True
                ),
                metrics.KeyValueMetric(
                    identificator=Identificator("mem", "free"),
                    title="Free",
                    getter=lambda: self.readable_format(psutil.virtual_memory().free),
                    important_item=True
                )
            ),
            
            metrics.KeyValueMetric(
                identificator=Identificator("mem", "speed"),
                title="Speed",
                getter=metrics.lazy_static_getter(Identificator("mem", "speed"), get_mem_speed),
                important_item=False
            )
        ]
        
        self.register_monitor()
        
    def readable_format(self, b: int) -> str:
        for unit in ("b", "Kb", "Mb", "Gb", "Tb", "Pb"):
            if abs(b) < 1024.0:
                return f"{b:3.1f} {unit}"
            b /= 1024.0

    
MEM_Monitor()
