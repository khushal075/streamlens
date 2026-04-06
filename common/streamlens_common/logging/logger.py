import logging
import sys
from typing import Any

def get_logger(name: str) -> logging.Logger:
    """
    Standardized JSON-ready logger for all StreamLens services.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        # In production, we'd use a JSON formatter here
        formatter = logging.Formatter(
            '[%(asctime)s] %(levelname)s in %(name)s: %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger