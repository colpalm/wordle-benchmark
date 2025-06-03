import tempfile
from pathlib import Path

import pytest

from wordle.word_list import WordList

@pytest.fixture
def temp_base_words_file():
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

class TestWordListLoading:
    """Test suite for WordList file loading functionality"""

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

    def test_load_words_invalid_entries_filtered(self, nonexistent_log_file):
        """Test that invalid entries are filtered out during loading"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("CRANE\n")  # Valid
            f.write("CAR\n")  # Too short
            f.write("HOUSES\n")  # Too long
            f.write("CR4NE\n")  # Contains number
            f.write("WORLD\n")  # Valid
            f.write("\n")  # Empty line
            f.write("  STARE  \n")  # Valid with whitespace
            f.flush()

            temp_path = Path(f.name)

        try:
            word_list = WordList(temp_path, nonexistent_log_file)
            words = word_list.words

            assert len(words) == 3
            assert "CRANE" in words
            assert "WORLD" in words
            assert "STARE" in words

            # Invalid words should be filtered out
            assert "CAR" not in words
            assert "HOUSES" not in words
            assert "CR4NE" not in words

        finally:
            temp_path.unlink()

    def test_load_words_empty_file_error(self, nonexistent_log_file):
        """Test error when the base words file is empty"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.flush()  # Empty file
            temp_path = Path(f.name)

        try:
            word_list = WordList(temp_path, nonexistent_log_file)

            with pytest.raises(ValueError, match="No valid words found"):
                _ = word_list.words

        finally:
            temp_path.unlink()

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

    def test_is_valid_existing_word(self, word_list):
        """Test validation of a word that exists in the list"""
        assert word_list.is_valid("CRANE") is True
        assert word_list.is_valid("crane") is True

    def test_is_valid_nonexistent_word(self, word_list):
        """Test validation of words that don't exist in the list"""
        assert word_list.is_valid("TESTS") is False
        assert word_list.is_valid("INVALID") is False


class TestWordListAddWord:
    """Test suite for adding words to WordList"""


class TestWordListIntegration:
    """Integration tests for WordList functionality"""