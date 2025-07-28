#!/bin/bash

# Root-MAS Upload Script
# This script uploads the project to a remote server and initiates deployment

set -e

# Configuration
PROJECT_NAME="root-mas"
REMOTE_PATH="/opt/${PROJECT_NAME}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Print usage
usage() {
    echo "Usage: $0 [OPTIONS] USER@HOST"
    echo ""
    echo "Options:"
    echo "  -p PORT     SSH port (default: 22)"
    echo "  -i KEY      SSH private key file"
    echo "  -d          Deploy after upload"
    echo "  -h          Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 root@192.168.1.100"
    echo "  $0 -p 2222 -i ~/.ssh/id_rsa ubuntu@myserver.com"
    echo "  $0 -d root@192.168.1.100  # Upload and deploy"
}

# Default values
SSH_PORT=22
SSH_KEY=""
DEPLOY_AFTER_UPLOAD=false
TARGET=""

# Parse command line arguments
while getopts "p:i:dh" opt; do
    case $opt in
        p)
            SSH_PORT="$OPTARG"
            ;;
        i)
            SSH_KEY="$OPTARG"
            ;;
        d)
            DEPLOY_AFTER_UPLOAD=true
            ;;
        h)
            usage
            exit 0
            ;;
        \?)
            echo "Invalid option: -$OPTARG" >&2
            usage
            exit 1
            ;;
    esac
done

shift $((OPTIND-1))
TARGET="$1"

if [ -z "$TARGET" ]; then
    echo -e "${RED}Error: Target server not specified${NC}"
    usage
    exit 1
fi

# Build SSH command options
SSH_OPTS="-p $SSH_PORT"
if [ -n "$SSH_KEY" ]; then
    SSH_OPTS="$SSH_OPTS -i $SSH_KEY"
fi

echo -e "${BLUE}Root-MAS Upload Script${NC}"
echo "=========================="
echo "Target: $TARGET"
echo "Port: $SSH_PORT"
echo "Project: $PROJECT_ROOT"
echo "Remote path: $REMOTE_PATH"
echo ""

# Check if .env file exists
if [ ! -f "$PROJECT_ROOT/.env" ]; then
    echo -e "${YELLOW}Warning: .env file not found in project root${NC}"
    echo "Make sure to create .env file on the server with your configuration"
    echo ""
fi

# Test SSH connection
echo -e "${BLUE}Testing SSH connection...${NC}"
if ! ssh $SSH_OPTS -o ConnectTimeout=10 "$TARGET" "echo 'SSH connection successful'"; then
    echo -e "${RED}Error: Cannot connect to $TARGET${NC}"
    exit 1
fi

# Create remote directory
echo -e "${BLUE}Creating remote directory...${NC}"
ssh $SSH_OPTS "$TARGET" "sudo mkdir -p $REMOTE_PATH && sudo chown \$(whoami):\$(whoami) $REMOTE_PATH"

# Create .rsyncignore for selective sync
cat > "$PROJECT_ROOT/.rsyncignore" << EOF
# Temporary files
*.tmp
*.log
.DS_Store
Thumbs.db

# Python cache
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
*.egg-info/
.pytest_cache/

# Virtual environments
venv/
env/
.venv/

# IDE files
.vscode/
.idea/
*.swp
*.swo

# OS files
.DS_Store
.Trashes
ehthumbs.db
Thumbs.db

# Git
.git/

# Large archives
*.zip
*.tar.gz
*.tar.bz2

# Local development files
.env.local
.env.development
docker-compose.override.yml
EOF

# Upload project files
echo -e "${BLUE}Uploading project files...${NC}"
rsync -avz --progress \
    --exclude-from="$PROJECT_ROOT/.rsyncignore" \
    -e "ssh $SSH_OPTS" \
    "$PROJECT_ROOT/" \
    "$TARGET:$REMOTE_PATH/"

# Clean up temporary files
rm -f "$PROJECT_ROOT/.rsyncignore"

# Make deployment script executable
echo -e "${BLUE}Setting up deployment script...${NC}"
ssh $SSH_OPTS "$TARGET" "chmod +x $REMOTE_PATH/deploy/deploy.sh"

echo -e "${GREEN}Upload completed successfully!${NC}"

# Check if .env file exists on remote server
echo -e "${BLUE}Checking remote configuration...${NC}"
if ssh $SSH_OPTS "$TARGET" "[ ! -f $REMOTE_PATH/.env ]"; then
    echo -e "${YELLOW}Warning: .env file not found on remote server${NC}"
    echo "You need to create .env file with your configuration:"
    echo "  ssh $SSH_OPTS $TARGET"
    echo "  cd $REMOTE_PATH"
    echo "  cp .env.example .env"
    echo "  nano .env  # Edit with your API keys and settings"
    echo ""
fi

# Deploy if requested
if [ "$DEPLOY_AFTER_UPLOAD" = true ]; then
    echo -e "${BLUE}Starting deployment...${NC}"
    
    # Check if .env exists before deploying
    if ssh $SSH_OPTS "$TARGET" "[ ! -f $REMOTE_PATH/.env ]"; then
        echo -e "${RED}Error: .env file is required for deployment${NC}"
        echo "Please create the .env file first, then run:"
        echo "  ssh $SSH_OPTS $TARGET 'sudo $REMOTE_PATH/deploy/deploy.sh deploy'"
        exit 1
    fi
    
    ssh $SSH_OPTS "$TARGET" "sudo $REMOTE_PATH/deploy/deploy.sh deploy"
    echo -e "${GREEN}Deployment completed!${NC}"
else
    echo ""
    echo -e "${BLUE}Next steps:${NC}"
    echo "1. Connect to your server:"
    echo "   ssh $SSH_OPTS $TARGET"
    echo ""
    echo "2. Configure environment (if not done already):"
    echo "   cd $REMOTE_PATH"
    echo "   cp .env.example .env"
    echo "   nano .env  # Add your API keys and configuration"
    echo ""
    echo "3. Deploy the application:"
    echo "   sudo ./deploy/deploy.sh deploy"
    echo ""
    echo "Or run with auto-deploy next time:"
    echo "   $0 -d $TARGET"
fi

echo ""
echo -e "${GREEN}Upload process completed!${NC}"