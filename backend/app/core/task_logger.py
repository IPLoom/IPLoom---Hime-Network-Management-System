import logging
import json
import os
import uuid
import threading
import queue
from logging.handlers import RotatingFileHandler
from datetime import datetime, timezone
from app.core.date_utils import now as utc_now
import traceback
import asyncio
from app.core.notifications import manager
from app.core.db import get_connection, commit
from app.core.config import get_settings

# --- Notification Queue Worker ---
class NotificationWorker(threading.Thread):
    def __init__(self):
        super().__init__(daemon=True, name="NotificationWorker")
        self.queue = queue.Queue()
        self._stop_event = threading.Event()
        self.conn = None

    def stop(self):
        self._stop_event.set()
        self.queue.put(None)

    def run(self):
        from app.core.db import get_connection, commit
        
        while not self._stop_event.is_set():
            item = self.queue.get()
            if item is None: break # Shutdown
            
            try:
                # Use the shared connection cursor
                conn = get_connection()
                try:
                    conn.execute("""
                        INSERT INTO notifications (id, type, task_type, event_type, message, level, target, details, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, [
                        item['id'], item['type'], item['task_type'], item['event_type'],
                        item['message'], item['level'], item['target'], 
                        json.dumps(item['details']) if item['details'] else None,
                        item['created_at']
                    ])
                    # Auto-commits single statement
                finally:
                    conn.close()
            except Exception as e:
                logging.error(f"NotificationWorker failed to save notification: {e}")
            finally:
                self.queue.task_done()
        
        logging.info("NotificationWorker stopped.")

_worker = NotificationWorker()
_worker.start()

def get_log_path():
    from app.core.config import get_settings
    from pathlib import Path
    settings = get_settings()
    data_dir = Path(settings.db_path).parent
    data_dir.mkdir(parents=True, exist_ok=True)
    return str(data_dir / "tasks.jsonl")

LOG_FILE = get_log_path()

class JsonFormatter(logging.Formatter):
    """
    Formatter that outputs JSON strings with structured event data
    """
    def format(self, record):
        # Base log entry
        log_entry = {
            "timestamp": utc_now().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
        }
        
        # Add extra fields if present in log record (passed via extra={...})
        if hasattr(record, 'task_type'):
            log_entry['task_type'] = record.task_type
        if hasattr(record, 'event_type'):
            log_entry['event_type'] = record.event_type
        if hasattr(record, 'target'):
            log_entry['target'] = record.target
        if hasattr(record, 'duration_ms'):
            log_entry['duration_ms'] = record.duration_ms
        if hasattr(record, 'details'):
            log_entry['details'] = record.details
            
        # Include exception info if present
        if record.exc_info:
            log_entry["exception"] = "".join(traceback.format_exception(*record.exc_info))
            
        return json.dumps(log_entry)

def setup_task_logger():
    """
    Configure and return the dedicated task activity logger
    """
    logger = logging.getLogger("task_events")
    logger.setLevel(logging.INFO)
    
    # Avoid adding multiple handlers if setup is called multiple times
    if logger.handlers:
        return logger
        
    # Rotate at 5MB, keep 1 backup (delete older)
    handler = RotatingFileHandler(LOG_FILE, maxBytes=5*1024*1024, backupCount=1, encoding='utf-8')
    handler.setFormatter(JsonFormatter())
    
    logger.addHandler(handler)
    logger.propagate = False # Don't propagate to root logger (avoid duplication in system logs)
    
    return logger

# Create the logger instance
task_logger = setup_task_logger()

def log_task_event(task_type, event_type, message, target=None, details=None, duration_ms=None, level="INFO"):
    """
    Helper function to log a structured task event
    """
    extra = {
        'task_type': task_type,
        'event_type': event_type,
    }
    
    if target:
        extra['target'] = target
    if details:
        extra['details'] = details
    if duration_ms is not None:
        extra['duration_ms'] = duration_ms
        
    if level.upper() == "ERROR":
        task_logger.error(message, extra=extra)
    elif level.upper() == "WARNING":
        task_logger.warning(message, extra=extra)
    else:
        task_logger.info(message, extra=extra)

    # --- Persistence & Broadcasting ---
    notifiable_types = {'completed', 'failed', 'new_device', 'status_changed', 'security_alert'}
    noisy_tasks = {'adguard_sync', 'openwrt_sync', 'mqtt_sync'}
    is_noisy_completion = event_type == 'completed' and task_type in noisy_tasks
    
    if (event_type in notifiable_types and not is_noisy_completion) or level.upper() in ["ERROR", "WARNING"]:
        notif_id = str(uuid.uuid4())
        created_at = utc_now()

        # 1. Queue for background persistence
        _worker.queue.put({
            "id": notif_id,
            "type": 'device' if event_type in ['new_device', 'status_changed'] else 'task',
            "task_type": task_type,
            "event_type": event_type,
            "message": message,
            "level": level.upper(),
            "target": target,
            "details": details,
            "created_at": created_at
        })

        # 2. WebSocket Broadcasting
        payload = {
            "type": "notification",
            "data": {
                "id": notif_id,
                "type": 'device' if event_type in ['new_device', 'status_changed'] else 'task',
                "task_type": task_type,
                "event_type": event_type,
                "message": message,
                "target": target,
                "details": details,
                "timestamp": created_at.isoformat(),
                "level": level
            }
        }
        
        # Broadcast using the thread-safe sync method
        manager.broadcast_sync(payload)
