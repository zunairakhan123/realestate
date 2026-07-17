import logging
import json
from contextvars import ContextVar
from datetime import datetime, timezone

# 1. Thread-safe, async-safe context variable
request_id_var: ContextVar[str] = ContextVar("request_id", default="system")

class JSONLogFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        # Base log payload
        log_record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "request_id": request_id_var.get() # Propagated ID injected here!
        }
        
        # Extract standard custom fields if provided
        for attr in ["method", "path", "status", "duration_ms"]:
            if hasattr(record, attr):
                log_record[attr] = getattr(record, attr)

        return json.dumps(log_record)

# Initialize Logger
logger = logging.getLogger("realty_app")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(JSONLogFormatter())
logger.handlers = [handler]
logger.propagate = False # Prevent double logging