# Use the official Python 3.12 slim image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/src

# Set the working directory
WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

# Copy dependency definition files
COPY ./game-engine/pyproject.toml ./game-engine/uv.lock* /app/

# Install project dependencies using uv
RUN uv sync --frozen

# Copy the application source code
COPY ./game-engine /app

# Copy and set up the entrypoint script
COPY ./docker/game-engine/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

# Set the entrypoint
ENTRYPOINT ["entrypoint.sh"]

# Set the default command to run the game runner
CMD ["uv", "run", "python", "-m", "wordle.game_runner"]