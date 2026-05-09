#!/bin/bash

# IPLoom SSH Deployment Script
# This script packages the application and transfers it to a remote server via SSH.

# --- Configuration ---
REMOTE_USER="oksbwn"                # Change to your server username
REMOTE_HOST="192.168.0.9"           # Change to your server IP or hostname
REMOTE_DIR="/home/$REMOTE_USER/iploom"
TAR_FILE="iploom_deploy.tar.gz"
# Use PARENT directory for the local archive to absolutely avoid "file changed as we read it" errors
LOCAL_ARCHIVE="../$TAR_FILE"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Starting IPLoom Build & Deployment...${NC}"

# 1. Build the UI locally (so the server doesn't need npm)
echo -e "${YELLOW}🏗️  Building UI locally...${NC}"
cd ui && npm run build && cd ..

if [ $? -ne 0 ]; then
    echo "❌ Error: UI build failed locally."
    exit 1
fi

# 2. Fix line endings in VERSION file (prevents syntax errors in publish.sh)
if [ -f "VERSION" ]; then
    sed -i 's/\r$//' VERSION
fi

# 3. Clean up old local archive
if [ -f "$LOCAL_ARCHIVE" ]; then
    rm "$LOCAL_ARCHIVE"
fi

# 4. Package the application
echo -e "${YELLOW}📦 Packaging files using tar (including built UI)...${NC}"
# Use tar as it is built-in to Windows and most Git Bash installs
tar -czf "$LOCAL_ARCHIVE" \
    --exclude="$TAR_FILE" \
    --exclude="iploom_deploy.tar.gz" \
    --exclude="ui/node_modules" \
    --exclude="backend/venv" \
    --exclude=".git" \
    --exclude="*/__pycache__" \
    --exclude="data/*.duckdb" \
    --exclude="data/*.log" \
    --exclude=".vscode" \
    --exclude=".idea" \
    --exclude="*.tar.gz" \
    --exclude="*.zip" \
    --exclude="*.log" \
    --exclude="temp" \
    .

if [ $? -ne 0 ]; then
    echo "❌ Error: Failed to create tar archive."
    exit 1
fi

# 3. Create remote directory if it doesn't exist
echo -e "${YELLOW}📁 Preparing remote directory at $REMOTE_HOST...${NC}"
ssh "$REMOTE_USER@$REMOTE_HOST" "mkdir -p $REMOTE_DIR"

if [ $? -ne 0 ]; then
    echo "❌ Error: Failed to connect to $REMOTE_HOST. Check SSH credentials."
    rm "$TAR_FILE"
    exit 1
fi

# 4. Transfer the file
echo -e "${YELLOW}📤 Transferring $TAR_FILE to server...${NC}"
scp "$LOCAL_ARCHIVE" "$REMOTE_USER@$REMOTE_HOST:$REMOTE_DIR/$TAR_FILE"

if [ $? -ne 0 ]; then
    echo "❌ Error: SCP transfer failed."
    rm "$LOCAL_ARCHIVE"
    exit 1
fi

# 5. Unpack on the remote server
echo -e "${YELLOW}🔓 Extracting files on server...${NC}"
ssh "$REMOTE_USER@$REMOTE_HOST" "cd $REMOTE_DIR && tar -xzf $TAR_FILE && rm $TAR_FILE && find . -maxdepth 2 -type f \( -name '*.sh' -o -name 'VERSION' -o -name '.env' \) -exec sed -i 's/\r$//' {} +"

if [ $? -ne 0 ]; then
    echo "❌ Warning: Extraction finished but line-ending fix (sed) might have failed."
    # We don't exit here because extraction was likely successful
fi

# 6. Success & Cleanup
rm "$LOCAL_ARCHIVE"
echo -e "${GREEN}✅ Deployment successful!${NC}"
echo -e "${BLUE}📍 Files are located at: $REMOTE_HOST:$REMOTE_DIR${NC}"
echo -e "${YELLOW}💡 Next steps: SSH into the server and run your start script (e.g., ./start.sh or docker-compose up)${NC}"
