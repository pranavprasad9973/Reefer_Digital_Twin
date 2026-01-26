# data_logger.py

import csv
import os

LOG_DIR = "logs"
DATASET_FILE = "reefer_dataset.csv"

def ensure_log_dir():
    os.makedirs(LOG_DIR, exist_ok=True)

def init_logger():
    ensure_log_dir()
    filepath = os.path.join(LOG_DIR, DATASET_FILE)

    # Write header only once
    if not os.path.exists(filepath):
        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                "run_id",
                "time_min",
                "temperature_C",
                "humidity_pct",
                "power_on",
                "door_open",
                "risk_index",
                "risk_level",
                "fault_power",
                "fault_door",
                "fault_cooling"
            ])

def log_data(data):
    filepath = os.path.join(LOG_DIR, DATASET_FILE)

    with open(filepath, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(data)
