from modules import logs

from typing import TYPE_CHECKING, Literal
if TYPE_CHECKING:
    from modules import metrics

from dataclasses import dataclass, asdict, field
import json


@dataclass
class TrackerMeta:
    tracked_id: str
    tracked_name: str
    target_category: str
    stmt_op: Literal[">", "<"]
    stmt_value: int | float
    avg_period: Literal["minute", "hour"]
    _values: list[int | float] = field(default_factory=lambda: [])  # Store and analyze values from this session
    

TRACKERS_FILEPATH = "./data/trackers.json"
TRACKABLE_METRICS: list["metrics.KeyValueMetric"] = []
TRACKERS: list[TrackerMeta] = []

def register_trackable_metric(metric: "metrics.KeyValueMetric") -> None:
    TRACKABLE_METRICS.append(metric)
    
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
                avg_period=tracker_meta["avg_period"]
            )
            
            TRACKERS.append(tracker)

    logs.log("Tracking", "info", f"Loaded {len(TRACKERS)} trackers.")

load_trackers()

def add_tracker(tracker_meta: TrackerMeta) -> None:
    with open(TRACKERS_FILEPATH, "r") as trackers_file:
        saved_trackers = json.load(trackers_file)
        
    saved_trackers[tracker_meta.tracked_id] = asdict(tracker_meta)
    saved_trackers[tracker_meta.tracked_id].pop("_values")
    
    with open(TRACKERS_FILEPATH, "w") as trackers_file:
        json.dump(saved_trackers, trackers_file)

    TRACKERS.append(tracker_meta)
    logs.log("Tracking", "info", f"Created tracker of asset: {tracker_meta.tracked_id} ({tracker_meta.tracked_name}) {tracker_meta.stmt_op} {tracker_meta.stmt_value} ({tracker_meta.avg_period})")        
    
def remove_tracker(tracked_id) -> None:
    for tracker in TRACKERS:
        if tracker.tracked_id == tracked_id:
            break
    else:
        return logs.log("Tracking", "error", f"Failed to remove tracker: `{tracked_id}` (not found in active trackers)")
    
    TRACKERS.remove(tracker)

    with open(TRACKERS_FILEPATH, "r") as trackers_file:
        saved_trackers = json.load(trackers_file)
        
    saved_trackers.pop(tracked_id)
    
    with open(TRACKERS_FILEPATH, "w") as trackers_file:
        json.dump(saved_trackers, trackers_file)

    logs.log("Tracking", "info", f"Removed tracker: `{tracked_id}`")

    
def prepare_trackable_metrics_per_category() -> list[dict]:
    trackable_metrics: dict[str, list[list[str, str]]] = {}

    for metric in TRACKABLE_METRICS:
        category = metric.identificator.category
        metric_data = [metric.identificator.full(), metric.title]

        if category not in trackable_metrics:
            trackable_metrics[category] = [metric_data]
        else:
            trackable_metrics[category].append(metric_data)
    
    return trackable_metrics

def prepare_active_trackers() -> list[dict]:
    active_trackers = []
    
    for tracker in TRACKERS:
        trigger_stmt = f"{tracker.stmt_op} {tracker.stmt_value} for a {tracker.avg_period}"
        tracker_data = {
            "trackedId": tracker.tracked_id,
            "trackedName": tracker.tracked_name,
            "category": tracker.target_category,
            "triggerStmt": trigger_stmt,
        }

        active_trackers.append(tracker_data)

    return active_trackers
