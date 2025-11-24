#!/bin/bash

# Fix Docker Credential Helper Issue - Better Solution
# Adds Docker Desktop bin to PATH or removes credential helper

set -e

echo "🔧 Fixing Docker Credential Helper (Better Solution)..."
echo ""

DOCKER_CONFIG="${HOME}/.docker/config.json"
DOCKER_DESKTOP_BIN="/Applications/Docker.app/Contents/Resources/bin"

# Option 1: Add Docker Desktop bin to PATH (if it exists)
if [ -d "$DOCKER_DESKTOP_BIN" ] && [ -f "$DOCKER_DESKTOP_BIN/docker-credential-desktop" ]; then
    echo "✅ Found docker-credential-desktop at: $DOCKER_DESKTOP_BIN"
    echo ""
    echo "Option 1: Add to PATH (Recommended)"
    echo "Add this to your ~/.zshrc:"
    echo ""
    echo "export PATH=\"/Applications/Docker.app/Contents/Resources/bin:\$PATH\""
    echo ""
    
    # Check if already in PATH
    if echo "$PATH" | grep -q "$DOCKER_DESKTOP_BIN"; then
        echo "✅ Docker Desktop bin is already in PATH"
    else
        echo "⚠️  Docker Desktop bin is NOT in PATH"
        echo "   Adding temporarily for this session..."
        export PATH="$DOCKER_DESKTOP_BIN:$PATH"
        echo "✅ Added to PATH (temporary for this session)"
    fi
fi

# Option 2: Remove credential helper (works for public images)
echo ""
echo "Option 2: Remove credential helper (works for public Docker Hub images)"
echo "This is safe if you're only pulling public images..."
echo ""

read -p "Do you want to remove the credential helper? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    python3 << EOF
import json
import os

config_path = os.path.expanduser("${DOCKER_CONFIG}")
try:
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    # Remove credential helper
    if 'credsStore' in config:
        del config['credsStore']
    
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print("✅ Removed credential helper from config")
except Exception as e:
    print(f"Error: {e}")
EOF
else
    echo "Keeping credential helper. Make sure Docker Desktop bin is in PATH."
fi

echo ""
echo "✅ Fix complete!"
echo ""
echo "📝 Next steps:"
echo "   1. If you chose Option 1, add the export to ~/.zshrc and restart terminal"
echo "   2. If you chose Option 2, try: docker compose up -d"
echo "   3. Or restart Docker Desktop if issues persist"

