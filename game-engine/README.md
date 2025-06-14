# Python Backend

Run Wordle Logic:
```shell
uv run python -m wordle.wordle_game
```

Run Test Suite:

Run tests that do not make API calls - **START HERE** — api_calls cost money
```shell
uv run pytest -m "not api_calls" ./tests/
```

All Tests
```shell
uv run pytest ./tests/
```

Integration Tests
```shell
uv run pytest -m integration ./tests/
```

Only unit tests (no integration tests)
```shell
uv run pytest -m "not integration" ./tests/
```

Specific File
```shell
uv run pytest ./tests/test_wordle_logic.py
```

Not capturing standard out (`-s`)
```shell
uv run pytest ./tests/ -s
```