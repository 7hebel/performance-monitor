import threading
import bcrypt
import json
import os

DATA_PATH = "./data/"
CONFIG_PATH = "./config.json"
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
if not os.path.exists(CONFIG_PATH):
    print("[ Config file not found ]")
    hostname = input("Host name: ")
    password = input("Password (optional): ")
    if password:
        password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    else:
        password = False
    
    with open(CONFIG_PATH, "a+") as file:
        json.dump({
            "router_address": "",
            "hostname": hostname,
            "password": password
        }, file)


from modules import connection
from modules import processes
import monitors


threading.Thread(target=processes.processes_checker, daemon=True).start()

connection.start_server()
