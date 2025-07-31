# Python Backend

Run Wordle Game:
```shell
uv run --directory src --env-file ../.env python -m wordle.game_runner
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

Set a specific logging level
```shell
uv run pytest --log-cli-level=DEBUG -m "not api_calls" tests/
```

Run a specific test
```shell
uv run pytest -m "not api_calls" tests/test_prompt_templates.py::TestSimplePromptTemplate::test_first_guess_prompt_structure
```

Run the specific full integration test (other integration tests in the file)
```shell
uv run pytest tests/integration/test_game_runner_integration.py::TestGameRunnerIntegration::test_complete_game_end_to_end -v -s --log-cli-level=DEBUG
```