from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from modules.logs import LogEntity

from dotenv import dotenv_values
import requests


env_config = dotenv_values("../.env")
DYNATRACE_ENVIRONMENT_ID = env_config.get("DT-EnvId")
DYNATRACE_LOGS_INGEST_API_KEY = env_config.get("DT-Logs")

    
def save_log_to_dynatrace(log: "LogEntity"):
    if DYNATRACE_ENVIRONMENT_ID is None or DYNATRACE_LOGS_INGEST_API_KEY is None:
        return
    
    url = f"https://{DYNATRACE_ENVIRONMENT_ID}.live.dynatrace.com/api/v2/logs/ingest"
    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "Authorization": f"Api-Token {DYNATRACE_LOGS_INGEST_API_KEY}",
    }
    data = [
        {
            "content": log.content,
            "status": log.status,
            "service.name": log.subject,
            "log.source": log.call_stack,
            'log.source.origin': log.call_origin
        }
    ]
    
    response = requests.post(url, headers=headers, json=data)
    if response.status_code != 204:
        print(f"[DYNATRACE] Saving log resulted in abnormal status_code: {response.status_code} - {response.text}")
    