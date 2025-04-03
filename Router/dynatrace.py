from dotenv import dotenv_values
import requests
import time


env_config = dotenv_values(".env")
DYNATRACE_ENVIRONMENT_ID = env_config.get("DT-EnvId")
DYNATRACE_API_KEY = env_config.get("DT-API")

# ENABLE_INTEGRATION = DYNATRACE_ENVIRONMENT_ID and DYNATRACE_API_KEY
ENABLE_INTEGRATION = False

def save_log_to_dynatrace(status: str, content: str) -> None:
    if not ENABLE_INTEGRATION:
        return

    url = f"https://{DYNATRACE_ENVIRONMENT_ID}.live.dynatrace.com/api/v2/logs/ingest"
    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "Authorization": f"Api-Token {DYNATRACE_API_KEY}",
    }
    data = [
        {
            "content": content,
            "status": status,
            "timestamp": int(time.time()),
            "service.name": "Router",
        }
    ]

    response = requests.post(url, headers=headers, json=data)
    if response.status_code != 204:
        print(f"[DYNATRACE] Saving log resulted in abnormal status_code: {response.status_code} - {response.text}")
