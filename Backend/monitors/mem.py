from dmi import dmi_provider

from modules.identificators import Identificator
from modules import metrics
from modules import monitor

import psutil

dmi_mem_data = dmi_provider.DMI_DATA["memory device"][0]
mem_info = psutil.virtual_memory()


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
                    title="Usage (%)",
                    getter=lambda: f"{psutil.virtual_memory().percent}%",
                    important_item=True,
                    trackable=True,
                    trackable_formatter=lambda usage: float(usage[:-1])
                ),
                metrics.KeyValueMetric(
                    identificator=Identificator("mem", "used"),
                    title="Used (Gb)",
                    getter=lambda: self.readable_format(psutil.virtual_memory().used),
                    important_item=True,
                    trackable=True,
                    trackable_formatter=lambda v: float(v.split(" ", 1)[0])
                ),
                metrics.KeyValueMetric(
                    identificator=Identificator("mem", "free"),
                    title="Free (Gb)",
                    getter=lambda: self.readable_format(psutil.virtual_memory().free),
                    important_item=True,
                    trackable=True,
                    trackable_formatter=lambda v: float(v.split(" ", 1)[0])
                )
            ),
            
            metrics.KeyValueMetric(
                identificator=Identificator("mem", "speed"),
                title="Speed",
                getter=metrics.StaticValueGetter(dmi_mem_data["Speed"]),
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
