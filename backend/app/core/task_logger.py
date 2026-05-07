import logging
import json
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime
import traceback

# Ensure data directory exists
os.makedirs("data", exist_ok=True)

LOG_FILE = "data/tasks.jsonl"

class JsonFormatter(logging.Formatter):
    """
    Formatter that outputs JSON strings with structured event data
    """
    def format(self, record):
        # Base log entry
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
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
