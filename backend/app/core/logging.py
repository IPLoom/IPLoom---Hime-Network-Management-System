import logging
import json
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime, timezone

class JsonFormatter(logging.Formatter):
    """
    Formatter that outputs JSON strings after some basic cleanup.
    """
    def format(self, record):
        log_record = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "funcName": record.funcName,
            "line": record.lineno,
            "path": record.pathname 
        }
        
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
            
        return json.dumps(log_record)

def setup_logging():
    """
    Configures the root logger to write JSON logs to a rotating file using a safe 5MB limit.
    """
    from app.core.config import get_settings
    settings = get_settings()
    from pathlib import Path
    log_dir = str(Path(settings.db_path).parent)
    
    if not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
        
    log_file = os.path.join(log_dir, "system.jsonl")
    
    # Create handler with rotation: Max 5MB, 1 backup file
    handler = RotatingFileHandler(
        log_file, 
        maxBytes=5 * 1024 * 1024, # 5MB
        backupCount=1,
        encoding='utf-8'
    )
    handler.setFormatter(JsonFormatter())
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Remove existing handlers to avoid duplicates/conflicts if re-initialized
    if root_logger.handlers:
        for h in root_logger.handlers:
            root_logger.removeHandler(h)
            
    root_logger.addHandler(handler)
    
    # Also log to console for development visibility (optional, but good for debugging)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    root_logger.addHandler(console_handler)

    logging.info("Logging initialized with rotation (Max 5MB).")
