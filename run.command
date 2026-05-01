#!/bin/bash

# Climate Risk Premium - Full Stack Runner
# Runs both the Python backend (Streamlit) and Next.js frontend

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}======================================================================${NC}"
echo -e "${BLUE}Climate Risk Premium - Full Stack Startup${NC}"
echo -e "${BLUE}======================================================================${NC}"

# Check if conda environment exists
if [ ! -d ".venv_SH" ]; then
    echo -e "${RED}Error: .venv_SH environment not found!${NC}"
    echo "Please create it first with: conda create -p ./.venv_SH python=3.11"
    exit 1
fi

echo -e "${GREEN}✓ Environment found: .venv_SH${NC}"

# Check if Node modules are installed
if [ ! -d "crp-dashboard/node_modules" ]; then
    echo -e "${YELLOW}Installing Node dependencies for frontend...${NC}"
    cd crp-dashboard
    npm install
    cd ..
    echo -e "${GREEN}✓ Node dependencies installed${NC}"
fi

echo ""
echo -e "${YELLOW}Starting services...${NC}"
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo -e "${YELLOW}Shutting down services...${NC}"
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true
    echo -e "${RED}Services stopped.${NC}"
}

trap cleanup EXIT

# Start Streamlit backend in background
echo -e "${BLUE}[1/2] Starting Python Backend (Streamlit)...${NC}"
/opt/miniconda3/bin/conda run -p ./.venv_SH python run_dashboard.py &
BACKEND_PID=$!
echo -e "${GREEN}✓ Backend started (PID: $BACKEND_PID)${NC}"

# Wait a moment for backend to initialize
sleep 3

# Start Next.js frontend in background
echo -e "${BLUE}[2/2] Starting Next.js Frontend...${NC}"
cd crp-dashboard
npm run dev &
FRONTEND_PID=$!
cd ..
echo -e "${GREEN}✓ Frontend started (PID: $FRONTEND_PID)${NC}"

echo ""
echo -e "${GREEN}======================================================================${NC}"
echo -e "${GREEN}Both services are running!${NC}"
echo -e "${GREEN}======================================================================${NC}"
echo ""
echo -e "${YELLOW}Access the services:${NC}"
echo -e "  • Frontend (Next.js):    ${BLUE}http://localhost:3000${NC}"
echo -e "  • Backend (Streamlit):   ${BLUE}http://localhost:8501${NC}"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop both services${NC}"
echo ""

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID
