import os
from datetime import datetime
import json

def log_event(event_type: str, track_id: int, config_path: str = 'config.json'):
    "Append event to logs/events.log as timestamp | event | id"
    os.makedirs('logs', exist_ok=True)
    log_file = 'logs/events.log'
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_entry = f"{timestamp} | {event_type} | {track_id}\n"
    
    with open(log_file, 'a') as f:
        f.write(log_entry)
    print(f"Logged: {log_entry.strip()}")

def get_logs(limit: int = 10) -> list:
    # Get recent log lines.
    try:
        with open('logs/events.log', 'r') as f:
            lines = f.readlines()[-limit:]
        return lines
    except FileNotFoundError:
        return []
