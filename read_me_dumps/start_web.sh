#!/bin/bash

# F1 Analysis Agent - Web Application Startup Script

echo "🏎️  Starting F1 Analysis Agent Web Application"
echo "==============================================="
echo ""

# Check if virtual environment exists
if [ ! -d "f1env_new" ]; then
    echo "❌ Virtual environment not found. Please run setup first."
    exit 1
fi

# Activate virtual environment
source f1env_new/bin/activate

# Check if backend dependencies are installed
if ! python -c "import flask" 2>/dev/null; then
    echo "📦 Installing backend dependencies..."
    pip install -r requirements-web.txt
fi

# Check if frontend is built
if [ ! -d "frontend/build" ]; then
    echo "📦 Building frontend..."
    cd frontend
    npm run build
    cd ..
fi

echo ""
echo "🚀 Starting backend server..."
echo ""
echo "Backend API: http://localhost:5000"
echo "Frontend:    http://localhost:5000"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the backend server
python backend/app.py
