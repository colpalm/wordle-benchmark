import logging
import os
import sys
from pathlib import Path


def configure_logging(log_level: int | str | None = None, log_file: Path | str | None = None) -> logging.Logger:
    """
    Configure the logging system for the entire application.

    This function is pytest-aware and won't interfere with pytest's
    own logging configuration when running tests.

    Args:
        log_level: The logging level to use (defaults to INFO, or DEBUG if env var is set)
                   Can be an integer (e.g., logging.DEBUG) or a string (e.g., "DEBUG").
        log_file: Optional path to a log file
    """
    effective_log_level = _determine_log_level(log_level)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(effective_log_level)

    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Clear existing handlers only when not running under pytest
    if not os.environ.get("PYTEST_CURRENT_TEST"):
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

    # Add a console handler only if no stream handlers exist
    if not root_logger.handlers or not any(isinstance(h, logging.StreamHandler) for h in root_logger.handlers):
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    # File handler (if specified)
    if log_file:
        # Set up file logging
        _setup_file_handler(log_file, formatter, root_logger)

    # Silence noisy third-party loggers
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    return root_logger

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger for a specific module.

    Args:
        name: The name of the module (typically __name__)

    Returns:
        A configured logger instance
    """
    return logging.getLogger(name)

def _determine_log_level(log_level: str | int | None) -> int:
    """
    Determine the effective log level from parameter or environment.

    Args:
        log_level: The log level parameter (string, int, or None)

    Returns:
        int: The effective logging level
    """
    if log_level is not None:
        if isinstance(log_level, str):
            return getattr(logging, log_level.upper(), logging.INFO)
        elif isinstance(log_level, int):
            return log_level
        else:
            print(f"Warning: Invalid log_level type '{type(log_level)}'. Defaulting to INFO.", file=sys.stderr)
            return logging.INFO
    else:
        log_level_name = os.environ.get("WORDLE_LOG_LEVEL", "INFO")
        return getattr(logging, log_level_name.upper(), logging.INFO)


def _setup_file_handler(log_file: Path | str, formatter: logging.Formatter, root_logger: logging.Logger) -> None:
    """
    Set up the file logging handler if one does not already exist.

    Args:
        log_file: Path to the log file
        formatter: Logging formatter to use
        root_logger: The root logger instance
    """
    # Check if a similar file handler already exists to avoid duplication
    resolved_path = str(Path(log_file).resolve())
    file_handler_exists = any(
        isinstance(h, logging.FileHandler) and h.baseFilename == resolved_path
        for h in root_logger.handlers
    )

    if file_handler_exists:
        return
    try:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    except Exception as e:
        print(f"Error setting up file logger for {log_file}: {e}. Logging to console.", file=sys.stderr)