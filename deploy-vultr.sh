#!/bin/bash

# OmniVibe Pro - Vultr Deployment Script
# Usage: ./deploy-vultr.sh [environment]
# Example: ./deploy-vultr.sh production

set -e

ENVIRONMENT=${1:-production}

echo "🚀 OmniVibe Pro Deployment to Vultr"
echo "Environment: $ENVIRONMENT"
echo "=================================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if .env.production exists
if [ ! -f ".env.production" ]; then
    echo -e "${RED}❌ Error: .env.production not found${NC}"
    echo "Please copy .env.production.template to .env.production and fill in your values"
    exit 1
fi

echo -e "${GREEN}✓${NC} Found .env.production"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Error: Docker is not running${NC}"
    exit 1
fi

echo -e "${GREEN}✓${NC} Docker is running"

# Pull latest changes (if in Git)
if [ -d ".git" ]; then
    echo -e "${YELLOW}📥 Pulling latest changes...${NC}"
    git pull origin main
    echo -e "${GREEN}✓${NC} Git pull completed"
fi

# Stop existing containers
echo -e "${YELLOW}🛑 Stopping existing containers...${NC}"
docker-compose -f docker-compose.production.yml --env-file .env.production down

# Build images
echo -e "${YELLOW}🔨 Building Docker images...${NC}"
docker-compose -f docker-compose.production.yml --env-file .env.production build --no-cache

# Start services
echo -e "${YELLOW}🚀 Starting services...${NC}"
docker-compose -f docker-compose.production.yml --env-file .env.production up -d

# Wait for services to be healthy
echo -e "${YELLOW}⏳ Waiting for services to be healthy...${NC}"
sleep 10

# Check service status
echo -e "${YELLOW}📊 Service Status:${NC}"
docker-compose -f docker-compose.production.yml ps

# Initialize Neo4j schema
echo -e "${YELLOW}📊 Initializing Neo4j schema...${NC}"
docker exec omnivibe-neo4j cypher-shell -u neo4j -p "${NEO4J_PASSWORD:-omnivibe2026}" < backend/scripts/init_neo4j_schema.cypher || echo "Schema already initialized"

# Show logs
echo -e "${GREEN}✓${NC} Deployment completed!"
echo ""
echo "=================================="
echo "📋 Useful Commands:"
echo "=================================="
echo "View logs:          docker-compose -f docker-compose.production.yml logs -f"
echo "View backend logs:  docker logs -f omnivibe-backend"
echo "View worker logs:   docker logs -f omnivibe-celery-worker"
echo "Restart services:   docker-compose -f docker-compose.production.yml restart"
echo "Stop services:      docker-compose -f docker-compose.production.yml down"
echo ""
echo "=================================="
echo "🌐 Service URLs:"
echo "=================================="
echo "Frontend:   http://localhost:3020"
echo "Backend:    http://localhost:8000"
echo "Neo4j:      http://localhost:7474"
echo "Redis:      redis://localhost:6379"
echo ""
echo "=================================="
echo "📊 Next Steps:"
echo "=================================="
echo "1. Configure domain DNS (point to Vultr IP)"
echo "2. Setup SSL certificates:"
echo "   docker run -it --rm -v \$(pwd)/nginx/ssl:/etc/letsencrypt certbot/certbot certonly --standalone -d omnivibepro.com -d api.omnivibepro.com"
echo "3. Reload Nginx:"
echo "   docker exec omnivibe-nginx nginx -s reload"
echo ""
echo -e "${GREEN}✅ Deployment successful!${NC}"
