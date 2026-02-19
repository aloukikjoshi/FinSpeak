Write-Host "Setting up FinSpeak... (Windows)"

# Check for Python
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "Error: Python is not installed or not in your PATH." -ForegroundColor Red
    exit 1
}

# Create virtual environment if it doesn't exist
if (-not (Test-Path "venv")) {
    Write-Host "Creating virtual environment..."
    python -m venv venv
}

# Activate virtual environment
if (Test-Path "venv\Scripts\Activate.ps1") {
    Write-Host "Activating virtual environment..."
    . .\venv\Scripts\Activate.ps1
} else {
    Write-Host "Error: Virtual environment activation script not found." -ForegroundColor Red
    exit 1
}

# Install dependencies
Write-Host "Installing dependencies..."
pip install -r requirements.txt

# Create .env from example if it doesn't exist
if (-not (Test-Path ".env")) {
    if (Test-Path ".env.example") {
        Write-Host "Creating .env from template..."
        Copy-Item ".env.example" -Destination ".env"
    } else {
        Write-Host "Warning: .env.example not found. Skipping .env creation." -ForegroundColor Yellow
    }
}

# Run the application
Write-Host "Starting FinSpeak..."
streamlit run fin_speak/app.py
