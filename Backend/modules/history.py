from modules import monitor
from modules import metrics
from modules import logs

from datetime import datetime as Datetime
from dataclasses import dataclass
import json
import time
import os


@dataclass
class RichTimestamp:
    timestamp: int
    cluster: int
    dump: int
    

def get_timestamp() -> RichTimestamp:
    timestamp = int(time.time())
    return RichTimestamp(
        timestamp=timestamp,
        cluster=timestamp // 60 // 60,
        dump=timestamp // 60
    )

def get_dumps_range_for_cluster(cluster_number: int) -> range:
    start = cluster_number * 60
    end = (cluster_number + 1) * 60
    return range(start, end)
    
def cluster_filepath(timestamp: RichTimestamp) -> str:
    return "./data/history/" + str(timestamp.cluster) + ".json"
    
def generate_cluster_file(timestamp: RichTimestamp, composition: dict) -> None:
    cluster_dumps_range = get_dumps_range_for_cluster(timestamp.cluster)
    cluster_dumps = {dump_number: {} for dump_number in cluster_dumps_range if dump_number >= get_timestamp().dump}
    
    with open(cluster_filepath(timestamp), "a+") as file:
        data = {
            "composition": composition,
            "dumps": cluster_dumps
        }
        json.dump(data, file)

    logs.log("History", "info", f"Generated history cluster file: {timestamp.cluster}")

def ensure_cluster_file(timestamp: RichTimestamp) -> None:
    if not os.path.exists(cluster_filepath(timestamp)):
        generate_cluster_file(timestamp, monitor.prepare_composition_data())


minute_updates_buffer: dict[str, list[metrics.MetricValueT]] = {}
minute_updates_timestamp = get_timestamp()  # Used to flush buffer when current minute exceeds.

def _flush_updates_buffer() -> None:
    """ Save changes made in minute to specified cluster file. """
    global minute_updates_timestamp
    
    ensure_cluster_file(minute_updates_timestamp)
    buffer = minute_updates_buffer.copy()
    target_dump_number = str(minute_updates_timestamp.dump)
    
    with open(cluster_filepath(minute_updates_timestamp), "r") as cluster_file:
        content = json.load(cluster_file)
        
    with open(cluster_filepath(minute_updates_timestamp), "w") as cluster_file:
        content["dumps"][target_dump_number] = buffer
        json.dump(content, cluster_file)
    
    minute_updates_buffer.clear()
    minute_updates_timestamp = get_timestamp()


def handle_updates(updates: dict[str, metrics.MetricValueT]) -> None:
    timestamp = get_timestamp()
    
    if timestamp.dump > minute_updates_timestamp.dump:
        _flush_updates_buffer()
        
    for metric_id, value in updates.items():
        if metric_id in minute_updates_buffer:
            minute_updates_buffer[metric_id].append(value)
        else:
            minute_updates_buffer[metric_id] = [value]
            
    
def get_all_clusters() -> list[int]:
    clusters = []
    for file in os.listdir("./data/history/"):
        cluster, _ = file.split(".", 1)
        clusters.append(int(cluster))
        
    return clusters


def prepare_dated_clusters(clusters: list[int]) -> dict[str, list[dict]]:
    """ Create dictionary with readable date as a key and list of suitable clusters and their readable form. """
    dated_clusters = {}
    clusters.sort()
    
    for cluster in clusters:
        cluster_date = Datetime.fromtimestamp(cluster * 60 * 60).strftime("%d/%m/%Y")
        if cluster_date not in dated_clusters:
            dated_clusters[cluster_date] = []
        
        cluster_dumps = list(get_dumps_range_for_cluster(cluster))
        hour = Datetime.fromtimestamp(cluster_dumps[0] * 60).strftime("%H")
        start_h = Datetime.fromtimestamp(cluster_dumps[0] * 60).strftime("%H:%M")
        end_h = Datetime.fromtimestamp(cluster_dumps[-1] * 60).strftime("%H:%M")
        
        dated_clusters[cluster_date].append({
            "cluster": cluster,
            "timeinfo": f"{start_h} - {end_h}",
            "hour": hour
        })
            
    return dated_clusters
    

def get_cluster(cluster: int) -> dict | None:
    filepath = "./data/history/" + str(cluster) + ".json"
    if not os.path.exists(filepath):
        return None
    
    with open(filepath, "r") as file:
        return json.load(file)
    
