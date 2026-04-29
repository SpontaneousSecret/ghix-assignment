#!/bin/bash

# Career Relocation Planner - Startup Script
# Starts both backend and frontend servers

echo "🚀 Starting Career Relocation Planner..."
echo ""

# Kill any existing instances
echo "🧹 Cleaning up existing processes..."
pkill -f "python3 run.py" 2>/dev/null
pkill -f "python3 -m http.server 8080" 2>/dev/null
sleep 1

# Start backend
echo "🔧 Starting Flask backend on port 5000..."
python3 run.py &
BACKEND_PID=$!
sleep 3

# Check if backend started
if ! curl -s http://localhost:5000 > /dev/null 2>&1; then
    echo "⚠️  Backend might not be ready yet, waiting..."
    sleep 2
fi

# Start frontend
echo "🌐 Starting frontend server on port 8080..."
python3 -m http.server 8080 > /dev/null 2>&1 &
FRONTEND_PID=$!
sleep 1

echo ""
echo "✅ Servers started successfully!"
echo ""
echo "📍 Access the application:"
echo "   Frontend: http://localhost:8080/index.html"
echo "   Backend:  http://localhost:5000"
echo ""
echo "📝 PIDs:"
echo "   Backend:  $BACKEND_PID"
echo "   Frontend: $FRONTEND_PID"
echo ""
echo "🛑 To stop servers:"
echo "   pkill -f \"python3 run.py\""
echo "   pkill -f \"python3 -m http.server\""
echo ""
echo "📖 For more info, see SETUP.md"
echo ""

# Keep script running
wait
