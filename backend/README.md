# Python Backend

Run Wordle Logic:
```shell
uv run python -m wordle.wordle_game
```

Run Test Suite:

All Tests
```shell
uv run pytest ./tests/wordle_tests.py
```

Integration Tests
```shell
uv run pytest -m integration ./tests/wordle_tests.py
```

Only unit tests (no integration tests)
```shell
uv run pytest -m "not integration" ./tests/wordle_tests.py
```