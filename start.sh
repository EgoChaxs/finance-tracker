#!/usr/bin/env bash

set -e

dataFolderPath="data"

if [ ! -d "$dataFolderPath" ]; then
    echo "Creating data directory..."
    mkdir -p "$dataFolderPath"
fi

echo "Setting up database..."

python -m alembic upgrade head

echo "Database setup complete."
echo "Starting Finance Tracker..."

python -m src.main

# If it does not work, make it executable first: chmod +x start.sh
# Then launch: ./start.sh