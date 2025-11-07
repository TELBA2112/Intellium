"""
Core logging configuration using loguru.

This module sets up structured logging for the entire application with:
- JSON formatting for production
- Console formatting for development
- Request ID tracking
- Performance metrics
- Error tracking with stack traces
"""

import sys
from pathlib import Path
from typing import Any, Dict

from loguru import logger

# Remove default logger
logger.remove()


def serialize_record(record: Dict[str, Any]) -> str:
    """
    Serialize log record to JSON format.
    
    Args:
        record: Log record dictionary from loguru
        
    Returns:
        JSON-formatted log string
    """
    subset = {
        "timestamp": record["time"].isoformat(),
        "level": record["level"].name,
        "message": record["message"],
        "module": record["module"],
        "function": record["function"],
        "line": record["line"],
    }
    
    if record.get("extra"):
        subset["extra"] = record["extra"]
    
    if record.get("exception"):
        subset["exception"] = {
            "type": record["exception"].type.__name__,
            "value": str(record["exception"].value),
            "traceback": record["exception"].traceback,
        }
    
    import json
    return json.dumps(subset)


def setup_logging(
    log_level: str = "INFO",
    json_logs: bool = False,
    log_file: str = "logs/app.log"
) -> None:
    """
    Configure application logging.
    
    Args:
        log_level: Minimum log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_logs: If True, output logs in JSON format
        log_file: Path to log file
        
    Examples:
        >>> setup_logging(log_level="DEBUG", json_logs=True)
        >>> logger.info("Application started")
    """
    # Ensure log directory exists
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Console logging
    if json_logs:
        logger.add(
            sys.stdout,
            level=log_level,
            serialize=True,
            format=serialize_record,
        )
    else:
        logger.add(
            sys.stdout,
            level=log_level,
            format=(
                "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
                "<level>{level: <8}</level> | "
                "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
                "<level>{message}</level>"
            ),
            colorize=True,
        )
    
    # File logging (always JSON)
    logger.add(
        log_file,
        level=log_level,
        rotation="500 MB",
        retention="10 days",
        compression="zip",
        serialize=True,
        format=serialize_record,
    )
    
    # Error file logging
    logger.add(
        log_path.parent / "error.log",
        level="ERROR",
        rotation="100 MB",
        retention="30 days",
        compression="zip",
        serialize=True,
        format=serialize_record,
    )
    
    logger.info(
        "Logging configured",
        log_level=log_level,
        json_logs=json_logs,
        log_file=log_file
    )


# Initialize logging
setup_logging()
