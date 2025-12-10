#!/bin/bash

# F1 Analysis Agent - Frontend Setup Script

echo "🏎️  F1 Analysis Agent - Frontend Setup"
echo "========================================"
echo ""

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed."
    echo "Please install Node.js from https://nodejs.org/"
    exit 1
fi

echo "✅ Node.js version: $(node --version)"
echo "✅ npm version: $(npm --version)"
echo ""

# Navigate to frontend directory
cd frontend || { echo "❌ Frontend directory not found"; exit 1; }

echo "📦 Installing frontend dependencies..."
npm install

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Frontend setup complete!"
    echo ""
    echo "To start the frontend development server, run:"
    echo "  cd frontend && npm start"
    echo ""
    echo "The frontend will be available at http://localhost:3000"
else
    echo "❌ Frontend setup failed"
    exit 1
fi
