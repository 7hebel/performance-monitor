from modules import connection
from modules import state
from modules import logs

from typing import TYPE_CHECKING, Literal
if TYPE_CHECKING:
    from modules import metrics

from dataclasses import dataclass, asdict, field
import time
import json


@dataclass
class TrackerMeta:
    tracked_id: str
    tracked_name: str
    target_category: str
    stmt_op: Literal[">", "<"]
    stmt_value: int | float
    _values: list[int | float] = field(default_factory=lambda: [])  # Store and analyze values from this session


TRACKERS_FILEPATH = "./data/trackers.json"
TRACKABLE_METRICS: dict[str, "metrics.KeyValueMetric"] = {}
TRACKERS: dict[str, TrackerMeta] = {}

def register_trackable_metric(metric: "metrics.KeyValueMetric") -> None:
    TRACKABLE_METRICS[metric.identificator.full()] = metric
    
def load_trackers() -> list[TrackerMeta]:
    with open(TRACKERS_FILEPATH, "r") as trackers_file:
        saved_trackers = json.load(trackers_file)
        
        for (tracker_id, tracker_meta) in saved_trackers.items():
            tracker = TrackerMeta(
                tracked_id=tracker_id,
                tracked_name=tracker_meta["tracked_name"],
                target_category=tracker_meta["target_category"].upper(),
                stmt_op=tracker_meta["stmt_op"],
                stmt_value=tracker_meta["stmt_value"],
            )
            
            TRACKERS[tracker_id] = tracker

    logs.log("Tracking", "info", f"Loaded {len(TRACKERS)} trackers.")

load_trackers()

def add_tracker(tracker_meta: TrackerMeta) -> None:
    with open(TRACKERS_FILEPATH, "r") as trackers_file:
        saved_trackers = json.load(trackers_file)
        
    saved_trackers[tracker_meta.tracked_id] = asdict(tracker_meta)
    saved_trackers[tracker_meta.tracked_id].pop("_values")
    
    with open(TRACKERS_FILEPATH, "w") as trackers_file:
        json.dump(saved_trackers, trackers_file)

    TRACKERS[tracker_meta.tracked_id] = tracker_meta
    logs.log("Tracking", "info", f"Created tracker of asset: {tracker_meta.tracked_id} ({tracker_meta.tracked_name}) {tracker_meta.stmt_op} {tracker_meta.stmt_value}")        
    
def remove_tracker(tracked_id) -> None:
    if tracked_id not in TRACKERS:
        return logs.log("Tracking", "error", f"Failed to remove tracker: `{tracked_id}` (not found in active trackers)")
    
    TRACKERS.pop(tracked_id)

    with open(TRACKERS_FILEPATH, "r") as trackers_file:
        saved_trackers = json.load(trackers_file)
        
    saved_trackers.pop(tracked_id)
    
    with open(TRACKERS_FILEPATH, "w") as trackers_file:
        json.dump(saved_trackers, trackers_file)

    logs.log("Tracking", "info", f"Removed tracker: `{tracked_id}`")

    
def prepare_trackable_metrics_per_category() -> list[dict]:
    trackable_metrics: dict[str, list[list[str, str]]] = {}

    for metric in TRACKABLE_METRICS.values():
        category = metric.identificator.category
        metric_data = [metric.identificator.full(), metric.title]

        if category not in trackable_metrics:
            trackable_metrics[category] = [metric_data]
        else:
            trackable_metrics[category].append(metric_data)
    
    return trackable_metrics

def prepare_active_trackers() -> list[dict]:
    active_trackers = []
    
    for tracker in TRACKERS.values():
        trigger_stmt = f"{tracker.stmt_op} {tracker.stmt_value}"
        tracker_data = {
            "trackedId": tracker.tracked_id,
            "trackedName": tracker.tracked_name,
            "category": tracker.target_category,
            "triggerStmt": trigger_stmt,
        }

        active_trackers.append(tracker_data)

    return active_trackers
    

def raise_alert(metric_name: str, body: str) -> None:
    message = {
        "event": connection.EventType.RAISE_ALERT,
        "data": {
            "title": f"🔔 | {metric_name}",
            "body": body
        }
    }

    try:
        connection.asyncio.run(connection.ws_client.send_json(message))
    except (RuntimeError, connection.WebSocketDisconnect):
        logs.log("Connection", "warn", f"Disconnected from: {connection.ws_client.client.host}:{connection.ws_client.client.port} (alert write error)")
        connection.ws_client = None


def pipe_updates_to_trackers(updates: dict[str, str | int | float]) -> None:
    for metric_id, value in updates.items():
        if metric_id not in TRACKABLE_METRICS or metric_id not in TRACKERS:
            continue
        
        tracked_metric = TRACKABLE_METRICS.get(metric_id)
        if tracked_metric.trackable_formatter:
            value = tracked_metric.trackable_formatter(value)
        
        tracker = TRACKERS.get(metric_id)
        
        tracker._values.append(value)
        if len(tracker._values) == 61:
            tracker._values.pop(0)
            
        avg_value = sum(tracker._values) / len(tracker._values)
        values_ratio = (avg_value / tracker.stmt_value) if tracker.stmt_op == ">" else (tracker.stmt_value / avg_value)
        
        state.trackers_approx_values_updates_buffer.insert_update(metric_id, {
            "value": round(avg_value, 2),
            "ratio": round(values_ratio, 2)
        })
        
        if len(tracker._values) > 58:
            if tracker.stmt_op == "<" and avg_value < tracker.stmt_value:
                logs.log("Tracking", "warn", f"Raising alert for: {tracker.tracked_id} as condition met: {avg_value}<{tracker.stmt_value}")
                raise_alert(f"{tracker.target_category} - {tracker.tracked_name}", f"The value of {tracker.tracked_name}: {avg_value} exceeded alerting limit (<{tracker.stmt_value})")
                tracker._values.clear()
                
            if tracker.stmt_op == ">" and avg_value > tracker.stmt_value:
                print("alert 1")
                logs.log("Tracking", "warn", f"Raising alert for: {tracker.tracked_id} as condition met: {avg_value}>{tracker.stmt_value}")
                raise_alert(f"{tracker.target_category} - {tracker.tracked_name}", f"The value of {tracker.tracked_name}: {avg_value} exceeded alerting limit (>{tracker.stmt_value})")
                print("alert 2")
                tracker._values.clear()
            

state.perf_metrics_updates_buffer.attach_flush_listener(pipe_updates_to_trackers)

