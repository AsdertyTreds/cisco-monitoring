import json
import os

""" Direcroties """
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESOURCES_DIR = os.path.join(BASE_DIR, "resources")
WEB_DIR = os.path.join(RESOURCES_DIR, "web")
LOG_DIR = os.path.join(BASE_DIR, "log")
DB_DIR = os.path.join(RESOURCES_DIR, "db")

DISCOVERY_PERIOD_SEC = 120

config_file = os.path.join(RESOURCES_DIR, "config.json")

""" Date Time"""
format_dt = "%d-%m-%Y %H:%M:%S"
format_dt = format_dt.replace('%-', '%#') if os.name == 'nt' else format_dt



with open(config_file, 'r', encoding='utf-8') as f:
    s_values = json.loads(f.read())
