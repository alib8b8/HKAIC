#!/bin/bash
# HKAIC Backend Startup Script

echo "=========================================="
echo "  HKAIC - AI Drone Flight Intelligence"
echo "  Backend Server"
echo "=========================================="
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Check if requirements are installed
if [ ! -f "venv/installed.txt" ] || [ requirements.txt -nt venv/installed.txt ]; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
    touch venv/installed.txt
fi

# Create uploads directory if it doesn't exist
mkdir -p uploads

echo ""
echo "Starting FastAPI server..."
echo "API documentation will be available at:"
echo "  http://localhost:8000/docs (Swagger UI)"
echo "  http://localhost:8000/redoc (ReDoc)"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
