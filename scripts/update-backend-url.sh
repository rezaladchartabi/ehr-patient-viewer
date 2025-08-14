#!/bin/bash

# Script to update backend URL across the project
# Usage: ./scripts/update-backend-url.sh <new-backend-url>

if [ $# -eq 0 ]; then
    echo "Usage: $0 <new-backend-url>"
    echo "Example: $0 https://my-new-backend.onrender.com"
    exit 1
fi

NEW_URL="$1"
OLD_URL="http://localhost:8005"

echo "Updating backend URL from $OLD_URL to $NEW_URL"

# Update config file
sed -i.bak "s|$OLD_URL|$NEW_URL|g" src/config.ts

# Update render.yaml
sed -i.bak "s|https://your-new-backend-url.onrender.com|$NEW_URL|g" render.yaml

# Update test file
sed -i.bak "s|$OLD_URL|$NEW_URL|g" test_backend.py

# Create .env.local if it doesn't exist
if [ ! -f .env.local ]; then
    echo "Creating .env.local file..."
    cat > .env.local << EOF
# Backend API Configuration
REACT_APP_API_URL=$NEW_URL

# Development Configuration
REACT_APP_ENV=development

# Feature Flags
REACT_APP_ENABLE_CACHE=true
REACT_APP_ENABLE_RATE_LIMITING=true
EOF
else
    echo "Updating .env.local file..."
    sed -i.bak "s|REACT_APP_API_URL=.*|REACT_APP_API_URL=$NEW_URL|g" .env.local
fi

# Clean up backup files
rm -f src/config.ts.bak render.yaml.bak test_backend.py.bak .env.local.bak

echo "✅ Backend URL updated successfully!"
echo ""
echo "Files updated:"
echo "- src/config.ts"
echo "- render.yaml"
echo "- test_backend.py"
echo "- .env.local"
echo ""
echo "To use the new URL:"
echo "1. Restart your development server: npm start"
echo "2. Update your deployment configuration if needed"

