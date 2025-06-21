#!/bin/bash
set -e

# Run database migrations if needed
# python -m alembic upgrade head

# Start the application
exec "$@"
