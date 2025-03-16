from modules import state
from modules import logs

from dataclasses import dataclass, asdict
from datetime import datetime
import threading
import psutil
import time


CPUS_COUNT = psutil.cpu_count(logical=False)


@dataclass
class ProcessData:
    pid: int
    name: str
    cpu_usage: float
    mem_use_mb: float
    threads: int
    started: str
    status: bool = True


class ProcessObserver:
    observers: dict[int, "ProcessObserver"] = {}
    
    def __init__(self, process: psutil.Process) -> None:
        self.process = process
        self.name = process.name()
        self.started = datetime.fromtimestamp(int(process.create_time())).strftime("%d/%m/%Y %H:%M")
        
        self.__prev_data: ProcessData | None = None
        self.__abort_observer = False
        
        ProcessObserver.observers[self.process.pid] = self
        threading.Thread(target=self.observe, daemon=True).start()
        
    def __format_size(self, b: int) -> str:
        for unit in ("b", "Kb", "Mb", "Gb", "Tb", "Pb"):
            if abs(b) < 1024.0:
                return f"{b:3.1f} {unit}"
            b /= 1024.0
        
    def fetch_process_data(self) -> ProcessData | None:
        return ProcessData(
            self.process.pid,
            self.name,
            f"{round(self.process.cpu_percent(0.5) / CPUS_COUNT, 2)}%",
            self.__format_size(self.process.memory_info().rss),
            self.process.num_threads(),
            self.started
        )

    def try_kill(self) -> None:
        try:
            self.process.kill()
        except (ProcessLookupError, psutil.Error):
            logs.log("Process", "warn", f"Failed to kill: {self.process.pid} (not found/no permission)")

    def observe(self) -> None:
        while True:
            time.sleep(0.1)
            
            if self.__abort_observer:
                return ProcessObserver.observers.pop(self.process.pid)
            
            try:
                data = self.fetch_process_data()
                if self.__prev_data is None or self.__prev_data != data:
                    state.processes_stats_updates_buffer.insert_update(data.pid, asdict(data))
                
            except (ProcessLookupError, psutil.Error):
                state.processes_stats_updates_buffer.insert_update(self.process.pid, {"status": False})
                return ProcessObserver.observers.pop(self.process.pid)
                
            self.__prev_data = data
            

SKIP_PROCESS_NAMES = ["svchost.exe", "System Idle Process", "System", ""]
        

def get_filtered_process(process: psutil.Process) -> psutil.Process:
    """ Filter lowest level processes. """
    try:
        if process.parent() is None:
            return process
        return process.parent()

    except psutil.NoSuchProcess:
        return None


def processes_checker() -> None:
    logs.log("Process", "info", "Started processes observers")
    
    while True:
        for process in psutil.process_iter():
            
            try:
                filtered_proc = get_filtered_process(process)
                if filtered_proc is None or filtered_proc.name() in SKIP_PROCESS_NAMES:
                    continue
                
                if filtered_proc.pid not in ProcessObserver.observers:
                    ProcessObserver(filtered_proc)

            except psutil.NoSuchProcess:
                continue
        
        time.sleep(1)


threading.Thread(target=processes_checker, daemon=True).start()
