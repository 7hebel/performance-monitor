from modules import history
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
    top_processes = []
    
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
        self.evaluate_top_processes(cpu_usage / CPUS_COUNT)
        
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

    def evaluate_top_processes(self, cpu_usage: float) -> None:
        """ Update list of TOP 3 most processor using processes. """
        if cpu_usage < 3:  # Ignore processes using less than 3% of cpu
            return
        
        for (proc_usage, proc_name) in ProcessesObserver.top_processes:
            if proc_name == self.name:
                ProcessesObserver.top_processes.remove((proc_usage, proc_name))
        
        if not ProcessesObserver.top_processes:
            return ProcessesObserver.top_processes.append((cpu_usage, self.name))
        
        if cpu_usage > ProcessesObserver.top_processes[-1][0] or len(ProcessesObserver.top_processes) < 3:
            new_top_processes = [*ProcessesObserver.top_processes, (cpu_usage, self.name)]
            new_top_processes.sort(key=lambda v: v[0], reverse=True)
            new_top_processes = new_top_processes[:3]
            ProcessesObserver.top_processes = new_top_processes
            

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
            

def top_processes_reporter() -> None:
    logs.log("Process", "info", "Starting top processes reporter...")
    
    while True:
        top_processes = []
        for (cpu_usage, name) in ProcessesObserver.top_processes:
            top_processes.append(f"{name}: {round(cpu_usage)}%")

        history.include_top_processes(top_processes)
        time.sleep(1)
