#!/bin/bash
# Secret Detection Script
# Run this before committing to ensure no secrets are exposed

echo "🔍 Checking for potential secrets in codebase..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

FOUND_SECRETS=0

# Check for .env files (should be gitignored)
echo ""
echo "Checking for .env files..."
ENV_FILES=$(find . -name ".env*" -type f ! -name ".env.example" ! -path "./.git/*" 2>/dev/null)
if [ ! -z "$ENV_FILES" ]; then
    echo -e "${RED}❌ WARNING: Found .env files that might not be gitignored:${NC}"
    echo "$ENV_FILES"
    FOUND_SECRETS=1
else
    echo -e "${GREEN}✓ No .env files found (good!)${NC}"
fi

# Check for OpenAI API keys
echo ""
echo "Checking for OpenAI API keys..."
if grep -r "sk-[a-zA-Z0-9]\{20,\}" --include="*.py" --include="*.ts" --include="*.tsx" --include="*.js" --include="*.json" --include="*.yml" --include="*.yaml" --include="*.toml" --include="*.txt" . 2>/dev/null | grep -v ".gitignore" | grep -v "__pycache__" | grep -v ".pyc" | grep -v "Binary"; then
    echo -e "${RED}❌ Found potential OpenAI API keys!${NC}"
    FOUND_SECRETS=1
else
    echo -e "${GREEN}✓ No OpenAI API keys found${NC}"
fi

# Check for GitHub tokens
echo ""
echo "Checking for GitHub tokens..."
if grep -r "ghp_[a-zA-Z0-9]\{30,\}" --include="*.py" --include="*.ts" --include="*.tsx" --include="*.js" --include="*.json" --include="*.yml" --include="*.yaml" . 2>/dev/null | grep -v ".gitignore" | grep -v "__pycache__"; then
    echo -e "${RED}❌ Found potential GitHub tokens!${NC}"
    FOUND_SECRETS=1
else
    echo -e "${GREEN}✓ No GitHub tokens found${NC}"
fi

# Check for AWS keys
echo ""
echo "Checking for AWS access keys..."
if grep -rE "(AKIA[0-9A-Z]{16}|ASIA[0-9A-Z]{16})" --include="*.py" --include="*.ts" --include="*.tsx" --include="*.js" --include="*.json" --include="*.yml" --include="*.yaml" . 2>/dev/null | grep -v ".gitignore" | grep -v "__pycache__"; then
    echo -e "${RED}❌ Found potential AWS access keys!${NC}"
    FOUND_SECRETS=1
else
    echo -e "${GREEN}✓ No AWS access keys found${NC}"
fi

# Check for private keys
echo ""
echo "Checking for private keys..."
if find . -name "*.pem" -o -name "*.key" -o -name "id_rsa" -o -name "id_dsa" -o -name "id_ecdsa" -o -name "id_ed25519" 2>/dev/null | grep -v ".git" | grep -v "node_modules"; then
    echo -e "${YELLOW}⚠️  Found key files. Make sure they are gitignored!${NC}"
fi

# Check for hardcoded passwords (excluding test/example patterns)
echo ""
echo "Checking for hardcoded passwords..."
POTENTIAL_PASSWORDS=$(grep -ri "password.*=.*['\"][^'\"]\{8,\}['\"]" --include="*.py" --include="*.ts" --include="*.tsx" --include="*.js" --include="*.json" . 2>/dev/null | grep -v "__pycache__" | grep -v ".pyc" | grep -v "get_password_hash" | grep -v "password_hash" | grep -v "PASSWORD" | grep -v "example" | grep -v "test" | grep -v "dummy" | grep -v "admin123")
if [ ! -z "$POTENTIAL_PASSWORDS" ]; then
    echo -e "${YELLOW}⚠️  Found potential hardcoded passwords:${NC}"
    echo "$POTENTIAL_PASSWORDS"
    echo -e "${YELLOW}   (Note: admin123 in seed_data.py is OK for demo purposes)${NC}"
else
    echo -e "${GREEN}✓ No suspicious hardcoded passwords found${NC}"
fi

# Summary
echo ""
echo "=================================="
if [ $FOUND_SECRETS -eq 1 ]; then
    echo -e "${RED}❌ SECRETS DETECTED! DO NOT COMMIT!${NC}"
    echo "Please remove secrets before committing."
    exit 1
else
    echo -e "${GREEN}✅ No obvious secrets detected!${NC}"
    echo "Safe to commit (but always double-check!)"
    exit 0
fi
