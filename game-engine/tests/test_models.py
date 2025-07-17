import pytest
import json
from datetime import datetime
from pydantic import ValidationError
from wordle.enums import LetterStatus, GameStatus

from wordle.models import (
    LetterResult,
    GameState,
    GameMetadata,
    GameResult,
    UsageStats
)


class TestLetterResult:
    def test_valid_letter_result(self):
        result = LetterResult(
            position=0,
            letter="A",
            status=LetterStatus.CORRECT
        )
        assert result.position == 0
        assert result.letter == "A"
        assert result.status == LetterStatus.CORRECT

    def test_invalid_position_bounds(self):
        with pytest.raises(ValidationError):
            LetterResult(position=-1, letter="A", status=LetterStatus.CORRECT)
        
        with pytest.raises(ValidationError):
            LetterResult(position=5, letter="A", status=LetterStatus.CORRECT)

    def test_invalid_letter_length(self):
        with pytest.raises(ValidationError):
            LetterResult(position=0, letter="", status=LetterStatus.CORRECT)
        
        with pytest.raises(ValidationError):
            LetterResult(position=0, letter="AB", status=LetterStatus.CORRECT)

    def test_letter_status_enum(self):
        for status in [LetterStatus.CORRECT, LetterStatus.PRESENT, LetterStatus.ABSENT]:
            result = LetterResult(position=0, letter="A", status=status)
            assert result.status == status


class TestGameState:
    def test_valid_game_state(self):
        state = GameState(
            target_word="HELLO",
            guesses=["WORLD", "HELLO"],
            guess_reasoning=["First guess", "Got it!"],
            guess_results=[
                [
                    LetterResult(position=0, letter="W", status=LetterStatus.ABSENT),
                    LetterResult(position=1, letter="O", status=LetterStatus.PRESENT),
                    LetterResult(position=2, letter="R", status=LetterStatus.ABSENT),
                    LetterResult(position=3, letter="L", status=LetterStatus.CORRECT),
                    LetterResult(position=4, letter="D", status=LetterStatus.ABSENT)
                ],
                [
                    LetterResult(position=0, letter="H", status=LetterStatus.CORRECT),
                    LetterResult(position=1, letter="E", status=LetterStatus.CORRECT),
                    LetterResult(position=2, letter="L", status=LetterStatus.CORRECT),
                    LetterResult(position=3, letter="L", status=LetterStatus.CORRECT),
                    LetterResult(position=4, letter="O", status=LetterStatus.CORRECT)
                ]
            ],
            guesses_made=2,
            guesses_remaining=4,
            status=GameStatus.WON,
            won=True,
            game_over=True
        )
        assert state.target_word == "HELLO"
        assert len(state.guesses) == 2
        assert state.guesses_made == 2
        assert state.won is True

    def test_invalid_target_word_length(self):
        with pytest.raises(ValidationError):
            GameState(
                target_word="HELL",  # Too short
                guesses_made=0,
                guesses_remaining=6,
                status=GameStatus.IN_PROGRESS,
                won=False,
                game_over=False
            )

    def test_invalid_guesses_bounds(self):
        with pytest.raises(ValidationError):
            GameState(
                target_word="HELLO",
                guesses_made=-1,  # Invalid
                guesses_remaining=6,
                status=GameStatus.IN_PROGRESS,
                won=False,
                game_over=False
            )

    def test_default_values(self):
        state = GameState(
            target_word="HELLO",
            guesses_made=0,
            guesses_remaining=6,
            status=GameStatus.IN_PROGRESS,
            won=False,
            game_over=False
        )
        assert state.guesses == []
        assert state.guess_reasoning == []
        assert state.guess_results == []


class TestUsageStats:
    def test_default_usage_stats(self):
        stats = UsageStats()
        assert stats.total_requests == 0
        assert stats.total_tokens_input == 0
        assert stats.total_tokens_output == 0
        assert stats.total_cost_usd == pytest.approx(0.0)
        assert stats.response_time_avg_ms == pytest.approx(0.0)

    def test_custom_usage_stats(self):
        stats = UsageStats(
            total_requests=5,
            total_tokens_input=100,
            total_tokens_output=50,
            total_cost_usd=0.02,
            response_time_avg_ms=250.5
        )
        assert stats.total_requests == 5
        assert stats.total_tokens_input == 100
        assert stats.total_tokens_output == 50
        assert stats.total_cost_usd == pytest.approx(0.02)
        assert stats.response_time_avg_ms == pytest.approx(250.5)


class TestGameMetadata:
    def test_valid_game_metadata(self):
        start_time = datetime(2024, 1, 1, 10, 0, 0)
        end_time = datetime(2024, 1, 1, 10, 5, 0)
        
        metadata = GameMetadata(
            model="gpt-4o-mini",
            template="simple",
            parser="simple",
            duration_seconds=300.0,
            start_time=start_time,
            end_time=end_time,
            date="2024-01-01",
            invalid_word_attempts=["XXXXX"],
            total_invalid_attempts=1,
            usage_stats=UsageStats(total_requests=5)
        )
        
        assert metadata.model == "gpt-4o-mini"
        assert metadata.template == "simple"
        assert metadata.parser == "simple"
        assert metadata.duration_seconds == pytest.approx(300.0)
        assert metadata.start_time == start_time
        assert metadata.end_time == end_time
        assert metadata.date == "2024-01-01"
        assert metadata.invalid_word_attempts == ["XXXXX"]
        assert metadata.total_invalid_attempts == 1
        assert metadata.usage_stats.total_requests == 5

    def test_invalid_duration(self):
        with pytest.raises(ValidationError):
            GameMetadata(
                model="gpt-4o-mini",
                template="simple",
                parser="simple",
                duration_seconds=-1.0,  # Invalid
                start_time=datetime.now(),
                end_time=datetime.now(),
                date="2024-01-01"
            )

    def test_invalid_attempts_bounds(self):
        with pytest.raises(ValidationError):
            GameMetadata(
                model="gpt-4o-mini",
                template="simple",
                parser="simple",
                duration_seconds=300.0,
                start_time=datetime.now(),
                end_time=datetime.now(),
                date="2024-01-01",
                total_invalid_attempts=-1  # Invalid
            )

    def test_default_values(self):
        metadata = GameMetadata(
            model="gpt-4o-mini",
            template="simple",
            parser="simple",
            duration_seconds=300.0,
            start_time=datetime.now(),
            end_time=datetime.now(),
            date="2024-01-01"
        )
        assert metadata.invalid_word_attempts == []
        assert metadata.total_invalid_attempts == 0
        assert metadata.usage_stats is None


class TestGameResult:
    def test_valid_game_result(self):
        start_time = datetime(2024, 1, 1, 10, 0, 0)
        end_time = datetime(2024, 1, 1, 10, 5, 0)
        
        game_state = GameState(
            target_word="HELLO",
            guesses=["WORLD", "HELLO"],
            guesses_made=2,
            guesses_remaining=4,
            status=GameStatus.WON,
            won=True,
            game_over=True
        )
        
        metadata = GameMetadata(
            model="gpt-4o-mini",
            template="simple",
            parser="simple",
            duration_seconds=300.0,
            start_time=start_time,
            end_time=end_time,
            date="2024-01-01"
        )
        
        result = GameResult(
            success=True,
            game_state=game_state,
            metadata=metadata
        )
        
        assert result.success is True
        assert result.game_state == game_state
        assert result.metadata == metadata
        assert result.error is None

    def test_convenience_properties(self):
        game_state = GameState(
            target_word="HELLO",
            guesses=["WORLD", "HELLO"],
            guesses_made=2,
            guesses_remaining=4,
            status=GameStatus.WON,
            won=True,
            game_over=True
        )
        
        metadata = GameMetadata(
            model="gpt-4o-mini",
            template="simple",
            parser="simple",
            duration_seconds=300.0,
            start_time=datetime.now(),
            end_time=datetime.now(),
            date="2024-01-01"
        )
        
        result = GameResult(
            success=True,
            game_state=game_state,
            metadata=metadata
        )
        
        assert result.won is True
        assert result.target_word == "HELLO"
        assert result.guesses_made == 2

    def test_failed_game_result(self):
        game_state = GameState(
            target_word="HELLO",
            guesses_made=0,
            guesses_remaining=6,
            status=GameStatus.IN_PROGRESS,
            won=False,
            game_over=False
        )
        
        metadata = GameMetadata(
            model="gpt-4o-mini",
            template="simple",
            parser="simple",
            duration_seconds=300.0,
            start_time=datetime.now(),
            end_time=datetime.now(),
            date="2024-01-01"
        )
        
        result = GameResult(
            success=False,
            game_state=game_state,
            metadata=metadata,
            error="Connection timeout"
        )
        
        assert result.success is False
        assert result.error == "Connection timeout"


class TestModelSerialization:
    def test_letter_result_serialization(self):
        result = LetterResult(
            position=0,
            letter="A",
            status=LetterStatus.CORRECT
        )
        
        # Test JSON serialization
        json_data = result.model_dump()
        assert json_data == {
            "position": 0,
            "letter": "A",
            "status": "correct"
        }
        
        # Test JSON string serialization
        json_str = result.model_dump_json()
        assert json.loads(json_str) == json_data
        
        # Test deserialization
        reconstructed = LetterResult.model_validate(json_data)
        assert reconstructed == result

    def test_game_state_serialization(self):
        state = GameState(
            target_word="HELLO",
            guesses=["WORLD"],
            guess_reasoning=["First guess"],
            guess_results=[
                [
                    LetterResult(position=0, letter="W", status=LetterStatus.ABSENT),
                    LetterResult(position=1, letter="O", status=LetterStatus.PRESENT),
                    LetterResult(position=2, letter="R", status=LetterStatus.ABSENT),
                    LetterResult(position=3, letter="L", status=LetterStatus.CORRECT),
                    LetterResult(position=4, letter="D", status=LetterStatus.ABSENT)
                ]
            ],
            guesses_made=1,
            guesses_remaining=5,
            status=GameStatus.IN_PROGRESS,
            won=False,
            game_over=False
        )
        
        # Test serialization
        json_data = state.model_dump()
        assert json_data["target_word"] == "HELLO"
        assert json_data["guesses"] == ["WORLD"]
        assert json_data["guess_reasoning"] == ["First guess"]
        assert len(json_data["guess_results"]) == 1
        assert len(json_data["guess_results"][0]) == 5
        assert json_data["status"] == "in_progress"
        
        # Test deserialization
        reconstructed = GameState.model_validate(json_data)
        assert reconstructed == state

    def test_usage_stats_serialization(self):
        stats = UsageStats(
            total_requests=5,
            total_tokens_input=100,
            total_tokens_output=50,
            total_cost_usd=0.02,
            response_time_avg_ms=250.5
        )
        
        json_data = stats.model_dump()
        assert json_data == {
            "total_requests": 5,
            "total_tokens_input": 100,
            "total_tokens_output": 50,
            "total_tokens_reasoning": 0,
            "total_cost_usd": 0.02,
            "response_time_avg_ms": 250.5
        }
        
        reconstructed = UsageStats.model_validate(json_data)
        assert reconstructed == stats

    def test_game_metadata_serialization(self):
        start_time = datetime(2024, 1, 1, 10, 0, 0)
        end_time = datetime(2024, 1, 1, 10, 5, 0)
        
        metadata = GameMetadata(
            model="gpt-4o-mini",
            template="simple",
            parser="simple",
            duration_seconds=300.0,
            start_time=start_time,
            end_time=end_time,
            date="2024-01-01",
            invalid_word_attempts=["XXXXX"],
            total_invalid_attempts=1,
            usage_stats=UsageStats(total_requests=5)
        )
        
        json_data = metadata.model_dump()
        assert json_data["model"] == "gpt-4o-mini"
        assert json_data["template"] == "simple"
        assert json_data["parser"] == "simple"
        assert json_data["duration_seconds"] == pytest.approx(300.0)
        assert json_data["date"] == "2024-01-01"
        assert json_data["invalid_word_attempts"] == ["XXXXX"]
        assert json_data["total_invalid_attempts"] == 1
        assert json_data["usage_stats"]["total_requests"] == 5
        
        reconstructed = GameMetadata.model_validate(json_data)
        assert reconstructed == metadata

    def test_game_result_full_serialization(self):
        # Create a complete game result
        start_time = datetime(2024, 1, 1, 10, 0, 0)
        end_time = datetime(2024, 1, 1, 10, 5, 0)
        
        game_state = GameState(
            target_word="HELLO",
            guesses=["WORLD", "HELLO"],
            guess_reasoning=["First guess", "Got it!"],
            guess_results=[
                [
                    LetterResult(position=0, letter="W", status=LetterStatus.ABSENT),
                    LetterResult(position=1, letter="O", status=LetterStatus.PRESENT),
                    LetterResult(position=2, letter="R", status=LetterStatus.ABSENT),
                    LetterResult(position=3, letter="L", status=LetterStatus.CORRECT),
                    LetterResult(position=4, letter="D", status=LetterStatus.ABSENT)
                ],
                [
                    LetterResult(position=0, letter="H", status=LetterStatus.CORRECT),
                    LetterResult(position=1, letter="E", status=LetterStatus.CORRECT),
                    LetterResult(position=2, letter="L", status=LetterStatus.CORRECT),
                    LetterResult(position=3, letter="L", status=LetterStatus.CORRECT),
                    LetterResult(position=4, letter="O", status=LetterStatus.CORRECT)
                ]
            ],
            guesses_made=2,
            guesses_remaining=4,
            status=GameStatus.WON,
            won=True,
            game_over=True
        )
        
        metadata = GameMetadata(
            model="gpt-4o-mini",
            template="simple",
            parser="simple",
            duration_seconds=300.0,
            start_time=start_time,
            end_time=end_time,
            date="2024-01-01",
            usage_stats=UsageStats(
                total_requests=2,
                total_tokens_input=200,
                total_tokens_output=20,
                total_cost_usd=0.01,
                response_time_avg_ms=150.0
            )
        )
        
        result = GameResult(
            success=True,
            game_state=game_state,
            metadata=metadata
        )
        
        # Test full serialization
        json_data = result.model_dump()
        assert json_data["success"] is True
        assert json_data["error"] is None
        assert json_data["game_state"]["target_word"] == "HELLO"
        assert json_data["game_state"]["won"] is True
        assert json_data["metadata"]["model"] == "gpt-4o-mini"
        assert json_data["metadata"]["usage_stats"]["total_requests"] == 2
        
        # Test deserialization
        reconstructed = GameResult.model_validate(json_data)
        assert reconstructed == result
        
        # Test convenience properties work after deserialization
        assert reconstructed.won is True
        assert reconstructed.target_word == "HELLO"
        assert reconstructed.guesses_made == 2