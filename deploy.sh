#!/bin/bash

echo "🚀 EHR System Deployment Script"
echo "================================"

# Check if we're in the right directory
if [ ! -f "package.json" ]; then
    echo "❌ Error: Please run this script from the ehr-ui directory"
    exit 1
fi

# Step 1: Copy database file
echo "📁 Copying database file..."
if [ -f "../Downloads/condition_I82401_mimic_iv_data/ehr_data.sqlite3" ]; then
    cp ../Downloads/condition_I82401_mimic_iv_data/ehr_data.sqlite3 ./backend/
    echo "✅ Database file copied successfully"
else
    echo "⚠️  Warning: Database file not found. Please copy it manually to ./backend/"
fi

# Step 2: Build React app
echo "🔨 Building React app..."
npm run build
if [ $? -eq 0 ]; then
    echo "✅ React app built successfully"
else
    echo "❌ Error: Failed to build React app"
    exit 1
fi

# Step 3: Create deployment package
echo "📦 Creating deployment package..."
mkdir -p deployment
cp -r backend deployment/
cp -r build deployment/frontend
cp DEPLOYMENT.md deployment/

echo "✅ Deployment package created in ./deployment/"
echo ""
echo "🎯 Next Steps:"
echo "1. Upload the ./deployment/ folder to your hosting platform"
echo "2. Follow the instructions in DEPLOYMENT.md"
echo "3. Share the URL with your colleagues"
echo ""
echo "📋 Quick deployment options:"
echo "- Render: https://render.com"
echo "- Railway: https://railway.app"
echo "- Netlify: https://netlify.com"
echo "- Vercel: https://vercel.com"

