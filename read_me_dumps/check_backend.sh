#!/bin/bash

echo "🏎️  F1 Analysis Agent - Backend Health Check"
echo "==========================================="
echo ""

# Check if backend is running
echo "Checking backend at http://localhost:5000/api/health..."
response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/api/health 2>/dev/null)

if [ "$response" = "200" ]; then
    echo "✅ Backend is running and healthy!"
    echo ""
    curl -s http://localhost:5000/api/health | python3 -m json.tool
else
    echo "❌ Backend is NOT running (HTTP $response)"
    echo ""
    echo "To start the backend:"
    echo "  1. Terminal 1: source f1env_new/bin/activate && python backend/app.py"
    echo "  2. Terminal 2: cd frontend && npm start"
    echo ""
    echo "Or use the production script:"
    echo "  ./start_web.sh"
fi
