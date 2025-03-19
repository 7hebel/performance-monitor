import asyncio
import json
import os

DATA_PATH = "./data/"
HISTORY_PATH = DATA_PATH + "history/"
LOGS_PATH = DATA_PATH + "logs/"
TRACKERS_PATH = DATA_PATH + "trackers.json"
ALERTS_HISTORY_PATH = DATA_PATH + "alerts_history.txt"

if not os.path.exists(DATA_PATH): os.mkdir(DATA_PATH)
if not os.path.exists(HISTORY_PATH): os.mkdir(HISTORY_PATH)
if not os.path.exists(LOGS_PATH): os.mkdir(LOGS_PATH)
if not os.path.exists(TRACKERS_PATH): 
    with open(TRACKERS_PATH, "a+") as file:
        json.dump({}, file)
if not os.path.exists(ALERTS_HISTORY_PATH): open(ALERTS_HISTORY_PATH, "a+").close()

if os.name == "nt":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


from modules import connection
import monitors

exit()
# connection.start_server()
