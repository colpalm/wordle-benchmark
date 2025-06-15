import logging
import os
import sys
from pathlib import Path

def configure_logging(log_level=None, log_file=None):
    """
    Configure the logging system for the entire application.
    
    Args:
        log_level: The logging level to use (defaults to INFO, or DEBUG if env var is set)
        log_file: Optional path to a log file
    """
    # Determine log level from environment or parameter
    if log_level is None:
        log_level_name = os.environ.get("WORDLE_LOG_LEVEL", "INFO")
        log_level = getattr(logging, log_level_name, logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Clear existing handlers to avoid duplicates when reconfiguring
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # Silence noisy third-party loggers
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    
    return root_logger

def get_logger(name):
    """
    Get a logger for a specific module.
    
    Args:
        name: The name of the module (typically __name__)
        
    Returns:
        A configured logger instance
    """
    return logging.getLogger(name)