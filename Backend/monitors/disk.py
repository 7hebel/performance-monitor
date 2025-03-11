from modules.identificators import Identificator
from modules import components
from modules import monitor

import psutil


class DISK_Monitor(monitor.MonitorBase):
    def __init__(self, mountpoint: str, fstype: str) -> None:
        self.mountpoint = mountpoint
        
        self.target_title = f"Disk: {mountpoint}"
        self.product_info = mountpoint
        self.hex_color = "#fc9003"
        self.components_register = [
            components.ChartComponent(
                identificator=Identificator(f"disk-{mountpoint}", "space-chart"),
                title="Used space (%)",
                min_value=0,
                max_value=100,
                getter=lambda: self.get_usage().percent,
                main_chart=True
            ),
            
            components.ComponentsRow(
                components.KeyValueComponent(
                    identificator=Identificator(f"disk-{mountpoint}", "total-size"),
                    title="Usage",
                    getter=lambda: f"{self.get_usage().percent}%",
                    important_item=True
                ),
                components.KeyValueComponent(
                    identificator=Identificator(f"disk-{mountpoint}", "total-size"),
                    title="Capacity",
                    getter=components.StaticValueGetter(self.format_size(self.get_usage().total)),
                    important_item=False
                ),
                components.KeyValueComponent(
                    identificator=Identificator(f"disk-{mountpoint}", "used-size"),
                    title="Used",
                    getter=lambda: self.format_size(self.get_usage().used),
                    important_item=False
                ),
                components.KeyValueComponent(
                    identificator=Identificator(f"disk-{mountpoint}", "free-size"),
                    title="Free",
                    getter=lambda: self.format_size(self.get_usage().free),
                    important_item=False
                )
            ),
            
            components.KeyValueComponent(
                identificator=Identificator(f"disk-{mountpoint}", "fs-type"),
                title="Filesystem type",
                getter=components.StaticValueGetter(fstype),
                important_item=False
            )
        ]
        
        self.register_monitor()
        
    def get_usage(self) -> object:
        return psutil.disk_usage(self.mountpoint)
            
    def format_size(self, b: int) -> str:
        for unit in ("b", "Kb", "Mb", "Gb", "Tb", "Pb"):
            if abs(b) < 1024.0:
                return f"{b:3.1f} {unit}"
            b /= 1024.0
            
            
for partition in psutil.disk_partitions():
    DISK_Monitor(partition.mountpoint, partition.fstype)
