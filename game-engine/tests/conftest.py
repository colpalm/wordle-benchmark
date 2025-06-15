import tempfile
from pathlib import Path

import pytest

from utils.logging_config import configure_logging
from wordle.word_list import WordList


@pytest.fixture(scope="session", autouse=True)
def setup_logging():
    """Configure logging for all tests."""
    # Use a higher log level for tests to reduce noise
    configure_logging(log_level="WARNING")
    yield


@pytest.fixture
def temp_base_words_file():
    """Create a temporary file with valid base words"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("CRANE\n")
        f.write("STARE\n")
        f.write("WORLD\n")
        f.write("HELLO\n")
        f.write("CRANK\n")
        f.write("LIGHT\n")
        f.write("MOUND\n")
        f.write("FIFTY\n")
        f.write("BUMPS\n")
        f.write("GHOST\n")
        f.write("CLOUD\n")
        f.flush()
        yield Path(f.name)
        Path(f.name).unlink()  # Clean up

@pytest.fixture
def nonexistent_log_file():
    """Provide the path to the log file that doesn't exist (realistic scenario)"""
    temp_dir = Path(tempfile.mkdtemp())
    log_path = temp_dir / "added_words.log"  # Path exists, file doesn't

    yield log_path

    # Cleanup
    if log_path.exists():
        log_path.unlink()
    temp_dir.rmdir()

@pytest.fixture
def word_list(temp_base_words_file, nonexistent_log_file):
    """Create a basic WordList for testing validation"""
    word_list = WordList(temp_base_words_file, nonexistent_log_file)

    yield word_list
