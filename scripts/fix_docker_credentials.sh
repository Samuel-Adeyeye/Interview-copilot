#!/bin/bash

# Fix Docker Credential Helper Issue
# This script fixes the "docker-credential-desktop not found" error

set -e

echo "🔧 Fixing Docker Credential Helper..."
echo ""

# Check if Docker config exists
DOCKER_CONFIG="${HOME}/.docker/config.json"

if [ ! -f "$DOCKER_CONFIG" ]; then
    echo "Creating Docker config directory..."
    mkdir -p "${HOME}/.docker"
    echo '{}' > "$DOCKER_CONFIG"
fi

# Check current config
echo "Current Docker config:"
cat "$DOCKER_CONFIG" 2>/dev/null | python3 -m json.tool 2>/dev/null || cat "$DOCKER_CONFIG"
echo ""

# Remove credential helper if it exists and is causing issues
if grep -q "docker-credential-desktop" "$DOCKER_CONFIG" 2>/dev/null; then
    echo "⚠️  Found docker-credential-desktop in config"
    echo "Removing credential helper from config..."
    
    # Use Python to safely remove the credential helper
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
    if 'credHelpers' in config:
        del config['credHelpers']
    
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print("✅ Removed credential helper from config")
except Exception as e:
    print(f"Error: {e}")
EOF
    
    echo ""
    echo "Updated Docker config:"
    cat "$DOCKER_CONFIG" | python3 -m json.tool 2>/dev/null || cat "$DOCKER_CONFIG"
    echo ""
fi

# Alternative: Set credential helper to empty
echo "Setting credential helper to empty (no credentials needed for public images)..."
python3 << EOF
import json
import os

config_path = os.path.expanduser("${DOCKER_CONFIG}")
try:
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    # Set empty credential helper
    config['credsStore'] = ""
    
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print("✅ Set credential helper to empty")
except Exception as e:
    print(f"Error: {e}")
EOF

echo ""
echo "✅ Docker credential helper fixed!"
echo ""
echo "📝 Try running Docker commands again:"
echo "   docker compose up -d"
echo ""
echo "💡 Note: If you're using Docker Desktop, you may need to:"
echo "   1. Restart Docker Desktop"
echo "   2. Or reinstall Docker Desktop if the issue persists"

