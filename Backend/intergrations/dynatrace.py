from dmi import dmi_provider

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from modules.logs import LogEntity

from dotenv import dotenv_values
import requests


env_config = dotenv_values("../.env")
DYNATRACE_ENVIRONMENT_ID = env_config.get("DT-EnvId")
DYNATRACE_API_KEY = env_config.get("DT-API")
MACHINE_ID = dmi_provider.DMI_DATA["system"][0]["UUID"]

ENABLE_INTEGRATION = DYNATRACE_ENVIRONMENT_ID and DYNATRACE_API_KEY


def save_log_to_dynatrace(log: "LogEntity") -> None:
    if not ENABLE_INTEGRATION:
        return

    url = f"https://{DYNATRACE_ENVIRONMENT_ID}.live.dynatrace.com/api/v2/logs/ingest"
    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "Authorization": f"Api-Token {DYNATRACE_API_KEY}",
    }
    data = [
        {
            "content": log.content,
            "status": log.status,
            "timestamp": log.timestamp,
            "service.name": log.subject,
        }
    ]

    response = requests.post(url, headers=headers, json=data)
    if response.status_code != 204:
        print(f"[DYNATRACE] Saving log resulted in abnormal status_code: {response.status_code} - {response.text}")


def send_metric_to_dynatrace(metric_id: str, value: str | int | float) -> None:
    if not ENABLE_INTEGRATION:
        return
    
    url = f"https://{DYNATRACE_ENVIRONMENT_ID}.live.dynatrace.com/api/v2/metrics/ingest"
    headers = {
        "Content-Type": "text/plain; charset=utf-8",
        "Authorization": f"Api-Token {DYNATRACE_API_KEY}",
    }
    data = f"{metric_id.replace(":", "")},machine={MACHINE_ID} {value}"
    
    response = requests.post(url, headers=headers, data=data)
    
    if response.status_code != 202:
        print(f"[DYNATRACE] Saving metric resulted in abnormal status_code: {response.status_code} - {response.text}")
