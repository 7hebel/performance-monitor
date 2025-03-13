from modules import metrics


class MonitorBase:
    target_title: str
    product_info: str
    hex_color: str
    metrics_struct: list[metrics.MetricT | metrics.MetricsRow]

    def register_monitor(self) -> None:
        MONITORS_REGISTER.append(self)
        print(f"Registered monitor: {self.target_title}")

    def get_category(self) -> str:
        return self.metrics_struct[0].identificator.category
            

MONITORS_REGISTER: list[MonitorBase] = [] 
    
    
def export_metric(metric: metrics.MetricT) -> dict:
    metric_data = {
        "identificator": metric.identificator.full(),
        "title": metric.title,
        "type": None,
        "details": {
            "staticValue": None
        }
    }
    
    if isinstance(metric, metrics.ChartMetric):
        metric_data["type"] = "chart"
    
    if isinstance(metric, metrics.KeyValueMetric):
        metric_data["type"] = "keyvalue"
        metric_data["details"]["important"] = metric.important_item
        
        if isinstance(metric.getter, metrics.StaticValueGetter):
            metric_data["details"]["staticValue"] = metric.getter()
    
    return metric_data
    

def prepare_composition_data() -> list[dict]:
    monitors = []
    
    for monitor in MONITORS_REGISTER:
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
            
        monitors.append(monitor_data)    
        
    return monitors
