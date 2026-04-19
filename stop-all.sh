#!/bin/bash

# SupplyChainGPT - Stop All Services Script (Linux/Mac)

set -e

echo "🛑 Stopping SupplyChainGPT System..."
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Stop backend
if [ -f backend.pid ]; then
    BACKEND_PID=$(cat backend.pid)
    echo -e "${BLUE}Stopping backend (PID: $BACKEND_PID)...${NC}"
    kill $BACKEND_PID 2>/dev/null || echo -e "${YELLOW}Backend already stopped${NC}"
    rm backend.pid
    echo -e "${GREEN}✅ Backend stopped${NC}"
else
    echo -e "${YELLOW}⚠️  Backend PID file not found${NC}"
fi

# Stop frontend
if [ -f frontend.pid ]; then
    FRONTEND_PID=$(cat frontend.pid)
    echo -e "${BLUE}Stopping frontend (PID: $FRONTEND_PID)...${NC}"
    kill $FRONTEND_PID 2>/dev/null || echo -e "${YELLOW}Frontend already stopped${NC}"
    rm frontend.pid
    echo -e "${GREEN}✅ Frontend stopped${NC}"
else
    echo -e "${YELLOW}⚠️  Frontend PID file not found${NC}"
fi

# Stop Docker services
echo -e "${BLUE}Stopping Docker services...${NC}"
docker-compose down

echo -e "${GREEN}✅ Docker services stopped${NC}"
echo ""
echo -e "${GREEN}🎉 All services stopped successfully!${NC}"
echo ""
echo -e "${BLUE}To start again: ${YELLOW}./start-all.sh${NC}"
