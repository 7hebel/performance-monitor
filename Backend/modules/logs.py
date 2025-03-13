from intergrations import dynatrace
from modules import timestamp

from dataclasses import dataclass
from typing import Literal
from enum import StrEnum
from pathlib import Path
import colorama
import inspect
import os

colorama.init(autoreset=True)


class LogStatus(StrEnum):
    info="info"
    warn="warn"
    error="error"


@dataclass
class LogEntity:
    status: LogStatus | Literal['info', 'warn', 'error']
    content: str
    subject: str
    call_origin: str
    call_stack: str
    timestamp: int


def _get_call_stack() -> tuple[str, str]:
    """ 
    Get information about place in code where log method was called. 
    Returns (finalCaller, callStack).
    """
    def _caller_info_from_frame(frame) -> str:
        """ Grab caller's information from frame and format it into: DIR.FILE::FUNC#LineNo """
        pardir = Path(frame.filename).parent.name
        caller_info = pardir + "." + os.path.basename(frame.filename).removesuffix(".py")
        if frame.function != "<module>":
            caller_info += f"::{frame.function}" 
        caller_info += f"#{frame.lineno}"

        return caller_info

    caller_frames = inspect.stack()[2:][::-1]
    call_origin = _caller_info_from_frame(caller_frames[-1])
    call_stack = ""
    
    for item_no, frame in enumerate(caller_frames, 1):
        caller_info = _caller_info_from_frame(frame)        
        call_stack += caller_info

        if item_no < len(caller_frames):
            call_stack += " -> "

    return call_origin, call_stack


def _get_log_filepath() -> str:
    if not os.path.exists("./logs/"):
        os.mkdir("./logs/")
        
    filepath = "./logs/" + timestamp.get_date_file_format() + ".log"
    return filepath
   
        
def _print_log(log: LogEntity) -> None:
    log_content = f"({log.subject}) "
    
    if log.status == LogStatus.info:
        log_content += f"{colorama.Fore.BLUE}INFO:{colorama.Fore.RESET}  "
    if log.status == LogStatus.warn:
        log_content += f"{colorama.Fore.YELLOW}WARN:{colorama.Fore.RESET}  "
    if log.status == LogStatus.error:
        log_content += f"{colorama.Fore.RED}ERROR:{colorama.Fore.RESET}  "
        
    log_content += log.content
    log_content += f"{colorama.Fore.LIGHTBLACK_EX} | {log.call_origin}"
    print(log_content)


def _save_log(log: LogEntity) -> None:
    filepath = _get_log_filepath()
    log_content = f"({log.subject}) {log.status}:  {log.content} | {log.call_stack}\n"
    with open(filepath, "a+") as file:
        file.write(log_content)
    

def log(subject: str, status: LogStatus | Literal['info', 'warn', 'error'], content: str) -> None:
    call_origin, call_stack = _get_call_stack()
    log_entity = LogEntity(status, content, subject, call_origin, call_stack, timestamp.generate_timestamp())

    _print_log(log_entity)
    _save_log(log_entity)
    dynatrace.save_log_to_dynatrace(log_entity)
