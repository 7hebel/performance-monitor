from modules import metrics
from modules import logs


class MonitorBase:
    target_title: str
    product_info: str
    hex_color: str
    metrics_struct: list[metrics.MetricT | metrics.MetricsRow]
    
    def register_monitor(self) -> None:
        MONITORS_REGISTER.append(self)
        logs.log("Monitor", "info", f"Registered monitor: {self.target_title}")

    def destroy_monitor(self) -> None:
        """ Disable all monitor's getters, remove monitor from register. """
        if self in MONITORS_REGISTER:
            MONITORS_REGISTER.remove(self)
        disabled_metrics_count = 0

        for metric_or_row in self.metrics_struct:
            if isinstance(metric_or_row, metrics.MetricsRow):
                for metric in metric_or_row.get_all():
                    metric._abort_getter = True
                    disabled_metrics_count += 1
            else:
                metric_or_row._abort_getter = True
                disabled_metrics_count += 1
                
        logs.log("Monitor", "warn", f"Destroyed monitor: {self.target_title} ({disabled_metrics_count} AsyncGetters disabled)")
        
    def get_category(self) -> str:
        return self.metrics_struct[0].identificator.category
            

MONITORS_REGISTER: list[MonitorBase] = [] 
    
    
def export_metric(metric: metrics.MetricT) -> dict:
    metric_data = {
        "identificator": metric.identificator.full(),
        "title": metric.title,
        "type": None,
        "details": {
            "initValue": None
        }
    }
    
    if isinstance(metric, metrics.ChartMetric):
        metric_data["type"] = "chart"
    
    if isinstance(metric, metrics.KeyValueMetric):
        metric_data["type"] = "keyvalue"
        metric_data["details"]["important"] = metric.important_item
        metric_data["details"]["initValue"] = metric.getter()
    
    return metric_data
    
    
def export_monitor(monitor: MonitorBase) -> dict:
    monitor_data = {
        "targetTitle": monitor.target_title,
        "productInfo": monitor.product_info,
        "categoryId": monitor.get_category(),
        "color": monitor.hex_color,
        "metrics": []
    }
    
    for metric_or_row in monitor.metrics_struct:
        if not isinstance(metric_or_row, metrics.MetricsRow):
            metric_data = export_metric(metric_or_row)
            monitor_data["metrics"].append(metric_data)
            continue
        
        row_metrics = [export_metric(m) for m in metric_or_row.get_all()]
        monitor_data["metrics"].append(row_metrics)
        
    return monitor_data


def prepare_composition_data() -> list[dict]:
    monitors = []
    
    for monitor in MONITORS_REGISTER:
        monitor_data = export_monitor(monitor)
        monitors.append(monitor_data)
        
    return monitors
