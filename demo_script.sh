#!/bin/bash

# FinSpeak Demo Script
# This script demonstrates the FinSpeak application

echo "========================================"
echo "    FinSpeak Demo Script"
echo "========================================"
echo ""

# Check if Streamlit is running
echo "Starting FinSpeak Streamlit application..."
echo ""
echo "Please open your browser to: http://localhost:8501"
echo ""
echo "Try these example queries:"
echo ""
echo "1. What is the current NAV of Vanguard S&P 500 Fund?"
echo "2. Show me 6 month returns for Fidelity Growth Fund"
echo "3. How has Wellington Fund performed over 1 year?"
echo "4. Get me the latest price of PIMCO Total Return Fund"
echo ""
echo "========================================"
echo ""

# Run Streamlit
streamlit run fin_speak/app.py
