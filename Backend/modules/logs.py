from intergrations import dynatrace

from datetime import datetime as Datetime
from dataclasses import dataclass
from typing import Literal
from enum import StrEnum
import colorama
import time

colorama.init()


class CodeTimer:
    """ Used to measure code execution time. """

    def __init__(self) -> None:
        self.start = int(time.time())
        
    def measure(self) -> str:
        seocnds = int(time.time()) - self.start        
        return f"{seocnds}s"


class LogStatus(StrEnum):
    info="info"
    warn="warn"
    error="error"


@dataclass
class LogEntity:
    status: LogStatus | Literal['info', 'warn', 'error']
    content: str
    subject: str
    timestamp: int

        
def _print_log(log: LogEntity) -> None:
    log_content = f"({log.subject}) "
    
    if log.status == LogStatus.info:
        log_content += f"{colorama.Fore.BLUE}INFO:{colorama.Fore.RESET}  "
    if log.status == LogStatus.warn:
        log_content += f"{colorama.Fore.YELLOW}WARN:{colorama.Fore.RESET}  "
    if log.status == LogStatus.error:
        log_content += f"{colorama.Fore.RED}ERROR:{colorama.Fore.RESET}  "
        
    log_content += log.content + colorama.Fore.RESET
    print(log_content)


def _save_log(log: LogEntity) -> None:
    filepath = "./data/logs/" + Datetime.now().strftime("%Y_%m_%d") + ".log"
    time_info = Datetime.now().strftime("%Y/%m/%d %H:%M:%S")
    log_content = f"{time_info} ({log.subject}) {log.status}:  {log.content}\n"
    
    with open(filepath, "a+") as file:
        file.write(log_content)
    

def log(subject: str, status: LogStatus | Literal['info', 'warn', 'error'], content: str) -> None:    
    log_entity = LogEntity(status, content, subject, int(time.time()))

    _print_log(log_entity)
    _save_log(log_entity)
    dynatrace.save_log_to_dynatrace(log_entity)
