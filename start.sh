#!/bin/bash
set -e

echo "Starting Gingerly..."

# Backend
cd backend
source venv/bin/activate
python seed.py
python run.py &
FLASK_PID=$!
cd ..

echo "✓ Flask API running on http://localhost:5001"

# Frontend
cd frontend
npm run dev &
NEXT_PID=$!
cd ..

echo "✓ Next.js running on http://localhost:3000"
echo ""
echo "  App:   http://localhost:3000"
echo "  API:   http://localhost:5001/api"
echo ""
echo "  Default admin: admin@gingerly.com / admin123"
echo ""
echo "Press Ctrl+C to stop both servers"

trap "kill $FLASK_PID $NEXT_PID 2>/dev/null" EXIT
wait
