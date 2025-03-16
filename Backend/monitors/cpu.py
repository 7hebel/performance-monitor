from dmi import dmi_provider

from modules.identificators import Identificator
from modules import metrics
from modules import monitor

import psutil

dmi_cpu_data = dmi_provider.DMI_DATA["processor"][0]
dmi_cache_data = dmi_provider.DMI_DATA["cache"]


class CPU_Monitor(monitor.MonitorBase):
    def __init__(self) -> None:
        self.target_title = "CPU"
        self.product_info = dmi_cpu_data["Version"]
        self.hex_color = "#368ccf"
        self.metrics_struct = [
            metrics.ChartMetric(
                identificator=Identificator("cpu", "usage-chart"),
                title="Usage (%)",
                getter=lambda: psutil.cpu_percent(interval=0.1),
            ),
            
            metrics.MetricsRow(
                metrics.KeyValueMetric(
                    identificator=Identificator("cpu", "usage-value"),
                    title="Usage",
                    getter=self.get_cpu_usage,
                    important_item=True
                ),
                metrics.KeyValueMetric(
                    identificator=Identificator("cpu", "processes"),
                    title="Processes",
                    getter=self.get_processes_count,
                    important_item=True
                )
            ),
            
            metrics.MetricsRow(
                metrics.KeyValueMetric(
                    identificator=Identificator("cpu", "base-freq"),
                    title="Base speed",
                    getter=metrics.StaticValueGetter(dmi_cpu_data["Current Speed"])
                ),
                metrics.KeyValueMetric(
                    identificator=Identificator("cpu", "logical-cores"),
                    title="Logical cores",
                    getter=metrics.StaticValueGetter(dmi_cpu_data["Core Count"])
                ),
                metrics.KeyValueMetric(
                    identificator=Identificator("cpu", "physical-cores"),
                    title="Physical cores",
                    getter=metrics.StaticValueGetter(dmi_cpu_data["Thread Count"])
                )
            ),
            
            metrics.MetricsRow(
                metrics.KeyValueMetric(
                    identificator=Identificator("cpu", "l1-cache"),
                    title="L1 cache",
                    getter=metrics.StaticValueGetter(dmi_cache_data[0]["Installed Size"])
                ),
                metrics.KeyValueMetric(
                    identificator=Identificator("cpu", "l3-cache"),
                    title="L2 cache",
                    getter=metrics.StaticValueGetter(dmi_cache_data[1]["Installed Size"])
                ),
                metrics.KeyValueMetric(
                    identificator=Identificator("cpu", "l3-cache"),
                    title="L3 cache",
                    getter=metrics.StaticValueGetter(dmi_cache_data[2]["Installed Size"])
                )
            ),
        ]
        
        self.register_monitor()
        
    def get_cpu_usage(self) -> str:
        return f"{psutil.cpu_percent(interval=1)}%"

    def get_processes_count(self) -> int:
        return len(list(psutil.process_iter()))
    
    
CPU_Monitor()
