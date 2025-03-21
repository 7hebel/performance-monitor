from modules import state
from modules import logs

from dataclasses import dataclass, asdict
import psutil
import time


CPUS_COUNT = psutil.cpu_count(logical=False)


@dataclass
class ProcessData:
    name: str
    cpu_usage: float
    mem_use_mb: float
    threads: int
    proc_count: int
    status: bool = True


class ProcessesObserver:
    observers: dict[str, "ProcessesObserver"] = {}
    
    def __init__(self, process: psutil.Process) -> None:
        self.name = process.name()
        self.processes: dict[int, psutil.Process] = {process.pid: process}
        self.__prev_data: ProcessData | None = None
        
        ProcessesObserver.observers[self.name] = self
        
    def add_process(self, process: psutil.Process) -> None:
        self.processes[process.pid] = process
        
    def grab_processes_data(self) -> ProcessData:
        cpu_usage = 0
        mem_usage = 0
        threads = 0
        
        lost_processes = []
        
        for process in self.processes.copy().values():
            try:
                with process.oneshot():
                    cpu_usage += process.cpu_percent()
                    mem_usage += process.memory_info().rss
                    threads += process.num_threads()
            except (ProcessLookupError, psutil.Error):
                lost_processes.append(process.pid)
                
        for lost_proc_pid in lost_processes:
            self.processes.pop(lost_proc_pid, None)
            
        if not self.processes:
            state.processes_stats_updates_buffer.insert_update(self.name, {"status": False})
            ProcessesObserver.observers.pop(self.name, None)
                
        proc_count = len(self.processes)
        
        return ProcessData(
            name=self.name,
            cpu_usage=f"{round(cpu_usage / CPUS_COUNT, 2)}%",
            mem_use_mb=str(round(mem_usage / (1024 * 1024), 2)) + " Mb",
            threads=threads,
            proc_count=proc_count,
            status=True
        )

    def try_kill(self) -> None:
        for process in self.processes.copy().values():
            try:
                process.kill()
                self.processes.pop(process.pid)
            except (ProcessLookupError, psutil.Error):
                logs.log("Process", "warn", f"Failed to kill: {process.pid} (not found/no permission)")

    def report_updates(self) -> None:        
        try:
            data = self.grab_processes_data()
            if self.__prev_data != data:
                state.processes_stats_updates_buffer.insert_update(self.name, asdict(data))
            
            self.__prev_data = data
            
        except (ProcessLookupError, psutil.Error):
            state.processes_stats_updates_buffer.insert_update(self.name, {"status": False})
            ProcessesObserver.observers.pop(self.name)


SKIP_PROCESS_NAMES = ["svchost.exe", "System Idle Process", "System", ""]
        
        
def processes_checker() -> None:
    logs.log("Process", "info", "Starting processes observers...")
    
    while True:
        for process in psutil.process_iter():
            try:
                if process is None or process.name() in SKIP_PROCESS_NAMES:
                    continue
                
                observer = ProcessesObserver.observers.get(process.name())
                if observer is None:
                    ProcessesObserver(process)
                    
                elif process.pid not in observer.processes:
                    observer.add_process(process)
    
            except psutil.NoSuchProcess:
                continue
        
        time.sleep(2)
        
        for observer in ProcessesObserver.observers.copy().values():
            observer.report_updates()
            
