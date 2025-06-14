import tempfile
from pathlib import Path

import pytest

from wordle.word_list import WordList


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

        # Extract words from the base file for count comparison - ignore empty lines
        base_lines = [line for line in temp_base_words_file.read_text().splitlines() if line.strip()]

        assert len(words) == len(base_lines)
        # Check a few select words
        assert "CRANE" in words
        assert "STARE" in words
        assert "WORLD" in words
        assert "HELLO" in words
        assert "CLOUD" in words

    def test_load_with_existing_additions(self, temp_base_words_file, log_file_with_entries):
        """Test loading when the log file has previous additions"""
        word_list = WordList(temp_base_words_file, log_file_with_entries)
        words = word_list.words

        # Extract words from the base file for count comparison - ignore empty lines
        base_lines = [line for line in temp_base_words_file.read_text().splitlines() if line.strip()]
        log_lines = [line for line in log_file_with_entries.read_text().splitlines() if line.strip()]
        expected_total = len(base_lines) + len(log_lines)

        assert len(words) == expected_total

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

        # Extract words from the base file for count comparison - ignore empty lines
        base_lines = [line for line in temp_base_words_file.read_text().splitlines() if line.strip()]

        assert len(words) == len(base_lines)

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

    def test_add_new_valid_word_success(self, word_list, nonexistent_log_file):
        """Test adding a new valid word to the list"""

        # Verify word not initially present
        assert not word_list.is_valid("TESTS")
        # Verify the log file does not exist
        assert not nonexistent_log_file.exists()
        # Add the word
        word_list.add_word("TESTS")
        # Verify word is now valid
        assert word_list.is_valid("TESTS")

        # Verify the log file was created and contains the word
        log_content = nonexistent_log_file.read_text()
        assert "TESTS" in log_content

    def test_add_word_case_normalization(self, word_list):
        """Test that words are normalized to uppercase"""

        word_list.add_word("tests")
        assert word_list.is_valid("TESTS")
        assert word_list.is_valid("tests")

    def test_add_word_invalid_format(self, word_list):
        """Test error handling for invalid word formats"""

        with pytest.raises(ValueError, match="Invalid word format"):
            word_list.add_word("TOO")  # Too short

        with pytest.raises(ValueError, match="Invalid word format"):
            word_list.add_word("TOOLONG")  # Too long

        with pytest.raises(ValueError, match="Invalid word format"):
            word_list.add_word("TES1S")  # Contains number

    def test_add_duplicate_word_ignored(self, word_list):
        """Test that adding a word that already exists is handled gracefully - does not add to the valid list or log it"""

        original_size = len(word_list.words)

        # Adding existing word should not change anything
        word_list.add_word("CRANE")
        assert len(word_list.words) == original_size

        # Log file should not exist because CRANE was not added
        assert not word_list.added_valid_words_path.exists()