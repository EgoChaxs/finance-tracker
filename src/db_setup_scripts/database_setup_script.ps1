$dataFolderPath = "data"

if (-not (Test-Path $dataFolderPath)) {
    Write-Host "Creating data directory..."
    New-Item -ItemType Directory -Path $dataFolderPath | Out-Null
}

Write-Host "Setting up database..."

python -m alembic upgrade head

if ($LASTEXITCODE -ne 0) {
    Write-Host "Database setup failed."
    exit 1
}

Write-Host "Database setup complete."
exit 0