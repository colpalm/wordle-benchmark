import tempfile
from pathlib import Path

import pytest

from wordle.enums import LetterStatus, GameStatus
from wordle.word_list import WordList
from wordle.wordle_game import WordleGame

@pytest.fixture
def sample_game(word_list: WordList) -> WordleGame:
    """Fixture providing a basic game instance"""
    return WordleGame(word_list=word_list, target_word="CRANE")

class TestEvaluateGuess:
    """Test suite for _evaluate_guess method"""

    def test_all_correct_letters(self, sample_game: WordleGame):
        """Test when all letters are in correct positions"""
        result = sample_game._evaluate_guess("CRANE")

        expected = [
            {"position": 0, "letter": "C", "status": LetterStatus.CORRECT.value},
            {"position": 1, "letter": "R", "status": LetterStatus.CORRECT.value},
            {"position": 2, "letter": "A", "status": LetterStatus.CORRECT.value},
            {"position": 3, "letter": "N", "status": LetterStatus.CORRECT.value},
            {"position": 4, "letter": "E", "status": LetterStatus.CORRECT.value},
        ]
        assert result == expected

    def test_no_correct_letters(self, sample_game: WordleGame):
        """Test when no letters match"""
        result = sample_game._evaluate_guess("FOIST")

        for letter_result in result:
            assert letter_result["status"] == LetterStatus.ABSENT.value

    def test_present_letters(self, sample_game: WordleGame):
        """Test letters in wrong positions (yellow)"""
        result = sample_game._evaluate_guess("EARNS")

        # E is in position 0 but should be in position 4 (present)
        assert result[0]["letter"] == "E"
        assert result[0]["status"] == LetterStatus.PRESENT.value

        # A is in position 1 but should be in position 2 (present)
        assert result[1]["letter"] == "A"
        assert result[1]["status"] == LetterStatus.PRESENT.value

        # R is in position 2 but should be in position 1 (present)
        assert result[2]["letter"] == "R"
        assert result[2]["status"] == LetterStatus.PRESENT.value

        # N is in correct position 3 (correct)
        assert result[3]["letter"] == "N"
        assert result[3]["status"] == LetterStatus.CORRECT.value

        # S is not in the target word (absent)
        assert result[4]["letter"] == "S"
        assert result[4]["status"] == LetterStatus.ABSENT.value

    def test_duplicate_letters_in_guess(self, sample_game: WordleGame):
        """Test handling of duplicate letters in guess"""
        result = sample_game._evaluate_guess("ERASE")

        # First E (position 0) should be absent (Correct E in position 4 is handled first, then there should be no more E's)
        assert result[0]["letter"] == "E"
        assert result[0]["status"] == LetterStatus.ABSENT.value

        # R (position 1) should be correct
        assert result[1]["letter"] == "R"
        assert result[1]["status"] == LetterStatus.CORRECT.value

        # A (position 2) should be correct
        assert result[2]["letter"] == "A"
        assert result[2]["status"] == LetterStatus.CORRECT.value

        # S (position 3) should be absent
        assert result[3]["letter"] == "S"
        assert result[3]["status"] == LetterStatus.ABSENT.value

        # Second E (position 4) should be correct
        assert result[4]["letter"] == "E"
        assert result[4]["status"] == LetterStatus.CORRECT.value

    def test_duplicate_letters_in_target(self, word_list):
        """Test handling when the target word has duplicate letters"""
        game = WordleGame(word_list=word_list, target_word="SPEED")
        result = game._evaluate_guess("SUEDE")

        # S in position 0 should be correct
        assert result[0]["letter"] == "S"
        assert result[0]["status"] == LetterStatus.CORRECT.value

        # U in position 1 should be absent
        assert result[1]["letter"] == "U"
        assert result[1]["status"] == LetterStatus.ABSENT.value

        # First E in position 2 should be correct
        assert result[2]["letter"] == "E"
        assert result[2]["status"] == LetterStatus.CORRECT.value

        # D in position 3 should be present (wrong position)
        assert result[3]["letter"] == "D"
        assert result[3]["status"] == LetterStatus.PRESENT.value

        # E in position 4 should be present (wrong position)
        assert result[4]["letter"] == "E"
        assert result[4]["status"] == LetterStatus.PRESENT.value


class TestMakeGuess:
    """Test suite for make_guess method"""

    def test_valid_guess(self, sample_game: WordleGame):
        """Test making a valid guess"""
        result = sample_game.make_guess("STARE")

        assert result["guess"] == "STARE"
        assert len(result["result"]) == 5
        assert result["status"] == GameStatus.IN_PROGRESS.value
        assert result["guesses_remaining"] == 5
        assert result["target_word"] is None  # Hidden during the game

    def test_winning_guess(self, sample_game: WordleGame):
        """Test making the correct guess"""
        result = sample_game.make_guess("CRANE")

        assert result["guess"] == "CRANE"
        assert result["status"] == GameStatus.WON.value
        assert result["target_word"] == "CRANE"  # Revealed after winning

    def test_losing_game(self, sample_game: WordleGame):
        """Test losing the game after 6 incorrect guesses"""

        # Make 5 incorrect guesses
        for _ in range(5):
            result = sample_game.make_guess("STARE")
            assert result["status"] == GameStatus.IN_PROGRESS.value
            assert result["target_word"] is None

        # Make the 6th incorrect guess
        result = sample_game.make_guess("STARE")
        assert result["status"] == GameStatus.LOST.value
        assert result["target_word"] == "CRANE"  # Revealed after losing
        assert sample_game.status == GameStatus.LOST

    def test_guess_too_short(self, sample_game: WordleGame):
        """Test error handling for short guess"""

        with pytest.raises(ValueError, match=f"Guess must be a {WordleGame.WORD_LENGTH}-letter word"):
            sample_game.make_guess("CAR")

    def test_guess_too_long(self, sample_game: WordleGame):
        """Test error handling for long guess"""

        with pytest.raises(ValueError, match=f"Guess must be a {WordleGame.WORD_LENGTH}-letter word"):
            sample_game.make_guess("CRANES")

    def test_non_alphabetic_guess(self, sample_game: WordleGame):
        """Test error handling for non-alphabetic guess"""

        with pytest.raises(ValueError, match="Guess must only contain alphabetical characters"):
            sample_game.make_guess("CR4NE")

    def test_guess_after_game_over(self, sample_game: WordleGame):
        """Test error when trying to guess after the game is over"""
        sample_game.make_guess("CRANE")  # Win the game

        with pytest.raises(ValueError, match="Game is not in progress"):
            sample_game.make_guess("STARE")

    def test_guess_whitespace_handling(self, sample_game: WordleGame):
        """Test that whitespace is stripped from guesses"""
        result = sample_game.make_guess(" STARE ")

        assert result["guess"] == "STARE"

    def test_case_insensitive_guess_input(self, sample_game: WordleGame):
        """Test that lowercase guesses are accepted"""
        result = sample_game.make_guess("stare")

        assert result["guess"] == "STARE"

class TestValidateGuess:
    """Test suite for validate_guess_format method"""
    # Note: Incorrect Length and invalid characters tested above in TestMakeGuess

    def test_valid_five_letter_word(self):
        """Test validation of a valid 5-letter word"""
        is_valid, error_msg = WordleGame.validate_guess_format("CRANE")
        assert is_valid is True
        assert error_msg == ""

        is_valid, error_msg = WordleGame.validate_guess_format("world")
        assert is_valid is True
        assert error_msg == ""

    def test_empty_string(self):
        """Test validation fails for an empty string"""
        is_valid, error_msg = WordleGame.validate_guess_format("")
        assert is_valid is False
        assert "5-letter word" in error_msg

class TestGameState:
    """Test suite for the get_game_state method"""

    def test_initial_game_state(self, sample_game: WordleGame):
        """Test game state at initialization"""
        state = sample_game.get_game_state()

        assert state["status"] == GameStatus.IN_PROGRESS.value
        assert state["guesses"] == []
        assert state["guess_results"] == []
        assert state["guesses_made"] == 0
        assert state["guesses_remaining"] == 6
        assert state["target_word"] is None  # Hidden during the game
        assert state["won"] is False
        assert state["game_over"] is False

    def test_game_state_after_guess(self, sample_game: WordleGame):
        """Test game state after making a guess"""
        sample_game.make_guess("STARE")
        state = sample_game.get_game_state()

        assert state["status"] == GameStatus.IN_PROGRESS.value
        assert state["guesses"] == ["STARE"]
        assert len(state["guess_results"]) == 1
        assert state["guesses_made"] == 1
        assert state["guesses_remaining"] == 5
        assert state["won"] is False
        assert state["game_over"] is False

    def test_game_state_when_won(self, sample_game: WordleGame):
        """Test game state when the game is won"""
        sample_game.make_guess("CRANE")
        state = sample_game.get_game_state()

        assert state["status"] == GameStatus.WON.value
        assert state["target_word"] == "CRANE"  # Revealed when won
        assert state["won"] is True
        assert state["game_over"] is True

    def test_game_state_when_lost(self, sample_game: WordleGame):
        """Test game state when the game is lost"""

        # Make 6 incorrect guesses
        for _ in range(6):
            sample_game.make_guess("STARE")

        state = sample_game.get_game_state()
        assert state["status"] == GameStatus.LOST.value
        assert state["guesses"] == ["STARE"] * 6
        assert state["guesses_made"] == 6
        assert state["guesses_remaining"] == 0
        assert state["target_word"] == "CRANE"  # Revealed when lost
        assert state["won"] is False
        assert state["game_over"] is True

class TestAPIFetch:
    """Test suite for the _fetch_wordle_data method"""

    # TODO: add test for word of the day retrieval
    def test_word_of_the_day_retrieved(self):
        pass


class TestEnsureTargetIsValid:
    """Test suite for ensuring a target is valid and adding it to the word list if necessary"""

    def test_target_word_already_valid(self, word_list: WordList):
        """Test when the target word is already in valid list - should do nothing"""
        # Create game with target word that's already in the word list
        original_size = len(word_list.words)
        game = WordleGame(word_list=word_list, target_word="CRANE")  # CRANE is in fixture

        # Should not change the word list
        assert len(game.word_list.words) == original_size
        assert game.word_list.is_valid("CRANE")

    def test_game_initialization_adds_invalid_target_word(self, word_list: WordList):
        """Test that creating a game with an invalid target word adds it to the word list"""
        # Check that the target word is not in the word list
        assert "ZZZZZ" not in word_list.words
        original_size = len(word_list.words)

        # Create game with target word NOT in the word list
        game = WordleGame(word_list, target_word="ZZZZZ")  # Not in the fixture

        # Should add the word
        assert len(game.word_list.words) == original_size + 1
        assert game.word_list.is_valid("ZZZZZ")


class TestWordleGameIntegration:
    """Integration test suite for full WordleGame scenarios"""

    @pytest.mark.integration
    def test_complete_winning_game(self, sample_game: WordleGame):
        """Test a complete winning game"""
        # First guess - some letters present
        result1 = sample_game.make_guess("STARE")
        assert result1["status"] == GameStatus.IN_PROGRESS.value
        assert len(sample_game.guesses) == 1
        assert result1["guesses_remaining"] == 5

        # Second guess - closer
        result2 = sample_game.make_guess("CRANK")
        assert result2["status"] == GameStatus.IN_PROGRESS.value
        assert len(sample_game.guesses) == 2
        assert result1["guesses_remaining"] == 5

        # Third guess - correct!
        result3 = sample_game.make_guess("CRANE")
        assert result3["status"] == GameStatus.WON.value
        assert len(sample_game.guesses) == 3

        # Verify the final game state
        final_state = sample_game.get_game_state()
        assert final_state["won"] is True
        assert final_state["game_over"] is True
        assert final_state["guesses_made"] == 3
        assert final_state["guesses"] == ["STARE", "CRANK", "CRANE"]

    @pytest.mark.integration
    def test_complete_losing_game(self, sample_game: WordleGame):
        """Test a complete game that ends in a loss"""
        # Make 6 incorrect guesses
        wrong_guesses = ["STARE", "LIGHT", "MOUND", "FIFTY", "BUMPS", "GHOST"]

        for i, guess in enumerate(wrong_guesses):
            result = sample_game.make_guess(guess)

            if i < 5:  # First 5 guesses
                assert result["status"] == GameStatus.IN_PROGRESS.value
                assert result["guesses_remaining"] == 5 - i
            else:  # Last guess
                assert result["status"] == GameStatus.LOST.value
                assert result["guesses_remaining"] == 0

        # Verify the final game state
        final_state = sample_game.get_game_state()
        assert final_state["won"] is False
        assert final_state["game_over"] is True
        assert final_state["guesses_made"] == 6
        assert final_state["guesses_remaining"] == 0
        assert final_state["guesses"] == wrong_guesses

    @pytest.mark.integration
    def test_game_progression_tracking(self, word_list: WordList):
        """Test that game properly tracks progression through multiple guesses"""
        game = WordleGame(word_list=word_list, target_word="WORLD")

        guesses = ["STARE", "CLOUD", "WORLD"]

        for i, guess in enumerate(guesses):
            result = game.make_guess(guess)

            # Check that all previous guesses are stored
            assert len(game.guesses) == i + 1
            assert len(game.guess_results) == i + 1
            assert game.guesses[i] == guess

            # Check remaining guesses
            expected_remaining = 6 - (i + 1)
            if result["status"] == GameStatus.IN_PROGRESS.value:
                assert result["guesses_remaining"] == expected_remaining

        # Should have won on the third guess
        assert game.status == GameStatus.WON

    @pytest.mark.integration
    def test_game_invalid_guess(self, word_list: WordList):
        """Test that the game handles invalid guesses"""
        game = WordleGame(word_list=word_list, target_word="WORLD")

        with pytest.raises(ValueError, match="Guess must be a valid English word"):
            game.make_guess("AAAAA")
