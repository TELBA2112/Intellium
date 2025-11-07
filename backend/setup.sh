#!/bin/bash

# Intellium Backend Setup Script
# This script sets up the development environment

set -e  # Exit on error

echo "========================================="
echo "Intellium Backend Setup"
echo "========================================="
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
required_version="3.11"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo -e "${RED}Error: Python 3.11 or higher is required${NC}"
    echo "Current version: $python_version"
    exit 1
fi
echo -e "${GREEN}✓ Python $python_version${NC}"
echo ""

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${YELLOW}Virtual environment already exists${NC}"
fi
echo ""

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
echo -e "${GREEN}✓ Virtual environment activated${NC}"
echo ""

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip > /dev/null 2>&1
echo -e "${GREEN}✓ pip upgraded${NC}"
echo ""

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt
echo -e "${GREEN}✓ Dependencies installed${NC}"
echo ""

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo -e "${YELLOW}⚠ Please update .env file with your configuration${NC}"
else
    echo -e "${YELLOW}.env file already exists${NC}"
fi
echo ""

# Create logs directory
if [ ! -d "logs" ]; then
    echo "Creating logs directory..."
    mkdir -p logs
    echo -e "${GREEN}✓ Logs directory created${NC}"
else
    echo -e "${YELLOW}Logs directory already exists${NC}"
fi
echo ""

# Check if Docker is installed
if command -v docker &> /dev/null; then
    echo -e "${GREEN}✓ Docker is installed${NC}"
    
    # Ask if user wants to start services
    read -p "Do you want to start Docker services (PostgreSQL, Redis, MinIO)? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Starting Docker services..."
        cd ..
        docker-compose up -d postgres redis minio
        cd backend
        echo -e "${GREEN}✓ Docker services started${NC}"
        echo ""
        echo "Waiting for services to be ready..."
        sleep 10
    fi
else
    echo -e "${YELLOW}⚠ Docker not found. Please install Docker to run services.${NC}"
fi
echo ""

# Check if database is accessible
echo "Checking database connection..."
python3 -c "
import os
from dotenv import load_dotenv
load_dotenv()
db_url = os.getenv('DATABASE_URL', '')
if db_url:
    print('Database URL configured')
else:
    print('Warning: DATABASE_URL not set in .env')
" 2>/dev/null || echo -e "${YELLOW}⚠ Could not check database${NC}"
echo ""

# Run database migrations (if alembic is set up)
if [ -d "alembic" ]; then
    echo "Running database migrations..."
    alembic upgrade head 2>/dev/null && echo -e "${GREEN}✓ Migrations completed${NC}" || echo -e "${YELLOW}⚠ Migrations skipped${NC}"
else
    echo -e "${YELLOW}⚠ Alembic not configured${NC}"
fi
echo ""

# Summary
echo "========================================="
echo "Setup Complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. Update .env file with your configuration"
echo "2. Run 'source venv/bin/activate' to activate the virtual environment"
echo "3. Run 'uvicorn app.main:app --reload' to start the development server"
echo "4. Run 'docker-compose up -d' to start all services (from project root)"
echo ""
echo "Useful commands:"
echo "  - Start dev server:      uvicorn app.main:app --reload"
echo "  - Run tests:             pytest"
echo "  - Run with coverage:     pytest --cov=app"
echo "  - Format code:           black app/ tests/"
echo "  - Lint code:             flake8 app/ tests/"
echo "  - Type check:            mypy app/"
echo ""
echo "URLs:"
echo "  - API:                   http://localhost:8000"
echo "  - API Docs:              http://localhost:8000/docs"
echo "  - Metrics:               http://localhost:8000/metrics"
echo "  - Prometheus:            http://localhost:9090"
echo "  - Grafana:               http://localhost:3000"
echo ""
echo -e "${GREEN}Happy coding! 🚀${NC}"
