import tempfile
from pathlib import Path

import pytest

from wordle.word_list import WordList


class TestWordListLoading:
    """Test suite for WordList file loading functionality"""

    @pytest.fixture
    def temp_base_words_file(self):
        """Create a temporary file with valid base words"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("CRANE\n")
            f.write("STARE\n")
            f.write("WORLD\n")
            f.write("HELLO\n")
            f.flush()
            yield Path(f.name)
            Path(f.name).unlink()  # Clean up

    @pytest.fixture
    def nonexistent_log_file(self):
        """Provide the path to the log file that doesn't exist (realistic scenario)"""
        temp_dir = Path(tempfile.mkdtemp())
        log_path = temp_dir / "added_words.log"  # Path exists, file doesn't

        yield log_path

        # Cleanup
        if log_path.exists():
            log_path.unlink()
        temp_dir.rmdir()

    @pytest.fixture
    def log_file_with_entries(self):
        """Create the log file with realistic entries"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
            f.write("2024-01-01T10:00:00: TESTS\n")
            f.write("2024-01-01T11:00:00: WORDS\n")
            f.flush()
            yield Path(f.name)
            Path(f.name).unlink()

    def test_load_base_words_first_time(self, temp_base_words_file, nonexistent_log_file):
        """Test loading when the log file doesn't exist yet (first run)"""
        word_list = WordList(temp_base_words_file, nonexistent_log_file)
        words = word_list.words
        assert len(words) == 4
        assert "CRANE" in words
        assert "STARE" in words
        assert "WORLD" in words
        assert "HELLO" in words

    def test_load_with_existing_additions(self, temp_base_words_file, log_file_with_entries):
        """Test loading when the log file has previous additions"""
        word_list = WordList(temp_base_words_file, log_file_with_entries)
        words = word_list.words
        assert len(words) == 6

    def test_load_words_nonexistent_base_file(self, nonexistent_log_file):
        """Test error when the base words file doesn't exist"""
        nonexistent_path = Path("/nonexistent/path/words.txt")
        word_list = WordList(nonexistent_path, nonexistent_log_file)

        with pytest.raises(FileNotFoundError, match="Word list file not found"):
            _ = word_list.words

    def test_lazy_loading(self, temp_base_words_file, nonexistent_log_file):
        """Test that words are only loaded when first accessed"""
        word_list = WordList(temp_base_words_file, nonexistent_log_file)

        # Should not have loaded yet
        assert word_list._words is None

        # First access should trigger loading
        words = word_list.words
        assert word_list._words is not None
        assert len(words) == 4

        # Later access should use the cached version
        words2 = word_list.words
        assert words2 is words  # Same object reference


class TestWordListValidation:
    """Test suite for word format validation"""


class TestWordListAddWord:
    """Test suite for adding words to WordList"""


class TestWordListIntegration:
    """Integration tests for WordList functionality"""