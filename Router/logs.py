import dynatrace

from typing import Literal
from enum import StrEnum
import colorama

colorama.init()


class LogStatus(StrEnum):
    info="info"
    warn="warn"
    error="error"


def log(status: LogStatus | Literal['info', 'warn', 'error'], content: str) -> None:    
    if status == LogStatus.info:
        log_content = f"{colorama.Fore.BLUE}INFO:{colorama.Fore.RESET}  "
    if status == LogStatus.warn:
        log_content = f"{colorama.Fore.YELLOW}WARN:{colorama.Fore.RESET}  "
    if status == LogStatus.error:
        log_content = f"{colorama.Fore.RED}ERROR:{colorama.Fore.RESET}  "
        
    log_content += content + colorama.Fore.RESET
    print(log_content)

    dynatrace.save_log_to_dynatrace(status, content)
