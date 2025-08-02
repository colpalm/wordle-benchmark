#!/bin/sh
set -e

echo "Running database migrations..."
uv run alembic upgrade head

# Execute the command passed to the container (from CMD or docker run)
exec "$@"