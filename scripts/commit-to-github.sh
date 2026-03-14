#!/bin/bash
# Safe Commit Script for AI Influencer Platform
# This script verifies no secrets before committing

set -e

echo "🚀 AI Influencer Platform - GitHub Commit Script"
echo "================================================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

REMOTE_URL="https://github.com/rajkum2/Influencer-AI-Platform.git"

# Step 1: Check if we're in the right directory
if [ ! -f "docker-compose.yml" ]; then
    echo -e "${RED}❌ Error: docker-compose.yml not found!${NC}"
    echo "Please run this script from the project root directory."
    exit 1
fi

# Step 2: Run secret detection
echo -e "${BLUE}Step 1: Running secret detection...${NC}"
if bash scripts/check-secrets.sh; then
    echo -e "${GREEN}✓ Secret check passed${NC}"
else
    echo -e "${RED}❌ Secret check failed!${NC}"
    echo "Please fix the issues above before committing."
    exit 1
fi

echo ""
echo -e "${BLUE}Step 2: Verifying .gitignore...${NC}"

# Check if .gitignore exists
if [ ! -f ".gitignore" ]; then
    echo -e "${RED}❌ .gitignore not found!${NC}"
    exit 1
fi

# Check if .env is gitignored
if git check-ignore -q .env 2>/dev/null; then
    echo -e "${GREEN}✓ .env is properly gitignored${NC}"
else
    echo -e "${YELLOW}⚠️  Warning: .env might not be gitignored${NC}"
fi

echo ""
echo -e "${BLUE}Step 3: Initializing git (if needed)...${NC}"

if [ ! -d ".git" ]; then
    git init
    echo -e "${GREEN}✓ Git initialized${NC}"
else
    echo -e "${GREEN}✓ Git already initialized${NC}"
fi

# Step 4: Add remote
echo ""
echo -e "${BLUE}Step 4: Setting up remote repository...${NC}"

if git remote get-url origin 2>/dev/null; then
    CURRENT_URL=$(git remote get-url origin)
    if [ "$CURRENT_URL" != "$REMOTE_URL" ]; then
        echo "Remote URL differs. Updating..."
        git remote set-url origin "$REMOTE_URL"
    fi
else
    git remote add origin "$REMOTE_URL"
fi

echo -e "${GREEN}✓ Remote set to: $REMOTE_URL${NC}"

# Step 5: Check what will be committed
echo ""
echo -e "${BLUE}Step 5: Files to be committed:${NC}"
git add -A
git status

echo ""
echo -e "${YELLOW}⚠️  Review the files above before committing!${NC}"
echo "Make sure no sensitive files are listed."
echo ""

# Step 6: Confirm with user
read -p "Do you want to proceed with the commit? (y/N): " confirm
if [[ ! $confirm =~ ^[Yy]$ ]]; then
    echo "Commit cancelled."
    git reset HEAD
    exit 0
fi

# Step 7: Commit
echo ""
echo -e "${BLUE}Step 6: Creating commit...${NC}"

git commit -m "Initial commit: AI Influencer Discovery Platform

Features:
- FastAPI backend with 50+ REST API endpoints
- Next.js 14 frontend with dashboard and explorer
- PostgreSQL + pgvector for data and embeddings
- Redis for caching and task queue
- MeiliSearch for full-text search
- Qdrant for vector similarity search
- ClickHouse for analytics
- Celery workers for async processing

Platform Integrations:
- YouTube Data API with quota management
- GitHub API for repos and activity
- Bluesky AT Protocol integration
- RSS/Blog scraper for articles

AI Features:
- OpenAI-powered content classification
- Automatic technology tagging
- Content summarization
- Quality and spam scoring
- Embedding generation

Business Logic:
- Custom ranking engine (7 scoring factors)
- Technology taxonomy system
- CRM with pipeline management
- Watchlists and alerts
- User/Team management with RBAC

Infrastructure:
- Docker Compose for local development
- Kubernetes manifests for production
- Prometheus and Grafana monitoring
- Auto-scaling configuration

Sample Data:
- 15 technology categories
- 10 AI influencers (Karpathy, LeCun, Ng, etc.)
- Demo content and rankings

Documentation:
- Comprehensive README
- OpenAPI/Swagger docs
- Implementation plan
- Deployment guides"

echo -e "${GREEN}✓ Commit created${NC}"

# Step 8: Push
echo ""
echo -e "${BLUE}Step 7: Pushing to GitHub...${NC}"

# Set main branch
git branch -M main

# Check if we need to pull first
if git ls-remote --exit-code origin main 2>/dev/null; then
    echo "Remote repository exists. Checking for updates..."
    if git fetch origin main 2>/dev/null; then
        LOCAL=$(git rev-parse @)
        REMOTE=$(git rev-parse @{u} 2>/dev/null || echo "")
        BASE=$(git merge-base @ @{u} 2>/dev/null || echo "")
        
        if [ "$LOCAL" != "$REMOTE" ] && [ "$REMOTE" != "" ]; then
            echo -e "${YELLOW}⚠️  Remote has changes. You may need to pull first.${NC}"
            read -p "Force push anyway? This will overwrite remote changes! (y/N): " force_push
            if [[ $force_push =~ ^[Yy]$ ]]; then
                git push -u origin main --force
            else
                echo "Push cancelled. Please resolve conflicts manually."
                exit 0
            fi
        else
            git push -u origin main
        fi
    fi
else
    # First push
    git push -u origin main
fi

echo ""
echo -e "${GREEN}✅ SUCCESS! Code committed to GitHub!${NC}"
echo ""
echo "Repository: $REMOTE_URL"
echo ""
echo "Next steps:"
echo "1. Visit: https://github.com/rajkum2/Influencer-AI-Platform"
echo "2. Set up your secrets in the actual environment (not in code)"
echo "3. Deploy using: make up"
