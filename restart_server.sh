#!/bin/bash
# Restart script for SHO_to_Z application

echo "🔄 Restarting SHO_to_Z application..."

# Find and kill any running server process
echo "🛑 Stopping any running server processes..."
pkill -f "uvicorn app.main:app" || echo "No running server process found"

# Wait a moment for the process to terminate
sleep 2

# Start the server in the background
echo "🚀 Starting the server..."
cd /Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &

echo "✅ Server started in the background"
echo "🌐 Application should be available at http://localhost:8000"
