dataFolderPath="data"

if [ ! -d "$dataFolderPath" ]; then
    echo "Creating data directory..."
    mkdir -p "$dataFolderPath"
fi

echo "Setting up database..."

alembic upgrade head

if [ $? -ne 0 ]; then
    echo "Database setup failed."
    exit 1
fi

echo "Database setup complete."
exit 0