from modules.identificators import Identificator
from modules import connection
from modules import metrics
from modules import monitor
from modules import logs

import threading
import asyncio
import psutil
import time


class DISK_Monitor(monitor.MonitorBase):
    def __init__(self, mountpoint: str, fstype: str) -> None:
        self.mountpoint = mountpoint.removesuffix("\\")
        self.target_title = f"Disk {self.mountpoint}"
        self.product_info = self.format_size(self.get_usage().total)
        self.hex_color = "#70db77"
        self.metrics_struct = [
            metrics.ChartMetric(
                identificator=Identificator(f"disk-{self.mountpoint}", "space-chart"),
                title="Used space (%)",
                getter=lambda: self.get_usage().percent,
                suppress_errors=True
            ),
            
            metrics.KeyValueMetric(
                identificator=Identificator(f"disk-{self.mountpoint}", "usage-percent"),
                title="Usage",
                getter=lambda: f"{self.get_usage().percent}%",
                important_item=True,
                suppress_errors=True
            ),
            
            metrics.MetricsRow(
                metrics.KeyValueMetric(
                    identificator=Identificator(f"disk-{self.mountpoint}", "total-size"),
                    title="Capacity",
                    getter=metrics.StaticValueGetter(self.format_size(self.get_usage().total)),
                    important_item=False,
                    suppress_errors=True
                ),
                metrics.KeyValueMetric(
                    identificator=Identificator(f"disk-{self.mountpoint}", "used-size"),
                    title="Used",
                    getter=lambda: self.format_size(self.get_usage().used),
                    important_item=False,
                    suppress_errors=True,
                    trackable=True,
                    trackable_formatter=lambda _: self.get_usage().used
                ),
                metrics.KeyValueMetric(
                    identificator=Identificator(f"disk-{self.mountpoint}", "free-size"),
                    title="Free",
                    getter=lambda: self.format_size(self.get_usage().free),
                    important_item=False,
                    suppress_errors=True,
                    trackable=True,
                    trackable_formatter=lambda _: self.get_usage().free
                )
            ),
            
            metrics.KeyValueMetric(
                identificator=Identificator(f"disk-{self.mountpoint}", "fs-type"),
                title="Filesystem type",
                getter=metrics.StaticValueGetter(fstype),
                important_item=False,
                suppress_errors=True
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


registered_partitions = {}
            
for partition in psutil.disk_partitions():
    part_monitor = DISK_Monitor(partition.mountpoint, partition.fstype)
    registered_partitions[partition] = part_monitor


def disk_updates_checker():
    while True:
        current_partitions = psutil.disk_partitions()
        
        for partition in current_partitions:
            if partition not in registered_partitions:
                logs.log("PartitionsChecker", "info", f"Detected new disk partition: {partition.mountpoint}")
                part_monitor = DISK_Monitor(partition.mountpoint, partition.fstype)
                registered_partitions[partition] = part_monitor
                
                monitor_data = monitor.export_monitor(part_monitor)
                message = {
                    "event": connection.EventType.PERF_ADD_MONITOR,
                    "data": monitor_data
                }
                if connection.ws_client:
                    asyncio.run(connection.ws_client.send_json(message))
        
        removed_partitons = []
        for reg_partition in registered_partitions:
            if reg_partition not in current_partitions:
                logs.log("PartitionsChecker", "info", f"Removed disk partition: {reg_partition.mountpoint}")
                reg_monitor = registered_partitions[reg_partition]
                reg_monitor.destroy_monitor()
                removed_partitons.append(reg_partition)

                message = {
                    "event": connection.EventType.PERF_REMOVE_MONITOR,
                    "data": reg_monitor.get_category()
                }
                if connection.ws_client:
                    asyncio.run(connection.ws_client.send_json(message))

        for rm_partition in removed_partitons:
            registered_partitions.pop(rm_partition)
        
        time.sleep(1)
    

checker = threading.Thread(target=disk_updates_checker, daemon=True)
checker.start()
