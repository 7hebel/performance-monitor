import threading
import json
import os

DATA_PATH = "./data/"
HISTORY_PATH = DATA_PATH + "history/"
LOGS_PATH = DATA_PATH + "logs/"
TRACKERS_PATH = DATA_PATH + "trackers.json"

if not os.path.exists(DATA_PATH): os.mkdir(DATA_PATH)
if not os.path.exists(HISTORY_PATH): os.mkdir(HISTORY_PATH)
if not os.path.exists(LOGS_PATH): os.mkdir(LOGS_PATH)
if not os.path.exists(TRACKERS_PATH): 
    with open(TRACKERS_PATH, "a+") as file:
        json.dump({}, file)


from modules import connection
from modules import processes
import monitors

threading.Thread(target=processes.processes_checker, daemon=True).start()

connection.start_server()

