#!/bin/bash

# FinSpeak Local Setup and Run Script
# This script sets up a virtual environment, installs dependencies, and runs the app

set -e

echo "🚀 FinSpeak - Setting up local environment..."

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "✏️  Please edit .env file with your API keys if needed"
fi

# Create necessary directories
mkdir -p demo_assets
mkdir -p data

echo "✅ Setup complete!"
echo ""
echo "🎯 Starting FinSpeak Streamlit app..."
echo "   Access it at: http://localhost:8501"
echo ""

# Run the Streamlit app
streamlit run fin_speak/app.py
