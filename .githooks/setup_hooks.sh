#!/bin/bash
#
# Setup script for Git Security Hooks
# Configures git to use the automated security logging hooks
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project root
PROJECT_ROOT="$(git rev-parse --show-toplevel)"

echo -e "${BLUE}🔧 Setting up Git Security Hooks...${NC}"

# Make hooks executable
chmod +x "$PROJECT_ROOT/.githooks/post-commit"

# Configure git to use the .githooks directory
git config core.hooksPath .githooks

# Create hooks log file
touch "$PROJECT_ROOT/.git/hooks.log"

# Test the setup
echo -e "${BLUE}🧪 Testing hook setup...${NC}"

# Check if Python is available
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo -e "${RED}❌ Python not found. Security hooks require Python.${NC}"
    exit 1
fi

# Test the security logger
SECURITY_LOGGER="$PROJECT_ROOT/scripts/security/auto_security_logger.py"
if [ -f "$SECURITY_LOGGER" ]; then
    echo -e "${GREEN}✅ Security logger found${NC}"
else
    echo -e "${RED}❌ Security logger not found: $SECURITY_LOGGER${NC}"
    exit 1
fi

# Test execution
if $PYTHON_CMD "$SECURITY_LOGGER" --help &> /dev/null; then
    echo -e "${GREEN}✅ Security logger is executable${NC}"
else
    echo -e "${YELLOW}⚠️  Security logger test failed, but continuing...${NC}"
fi

echo -e "${GREEN}✅ Git Security Hooks setup complete!${NC}"
echo ""
echo -e "${BLUE}Configuration:${NC}"
echo "  📁 Hooks directory: .githooks"
echo "  🔍 Security logger: scripts/security/auto_security_logger.py"
echo "  📝 Security log: SECURITY_AUDIT_LOG.md"
echo "  📋 Hook log: .git/hooks.log"
echo ""
echo -e "${BLUE}Usage:${NC}"
echo "  • Security analysis runs automatically after each commit"
echo "  • View hook logs: cat .git/hooks.log"
echo "  • Enable verbose output: export SECURITY_HOOK_VERBOSE=1"
echo "  • Manual analysis: $PYTHON_CMD scripts/security/auto_security_logger.py [commit-hash]"
echo ""
echo -e "${YELLOW}Note:${NC} The security log will be automatically updated when security-related commits are detected."