#!/bin/bash

# HTS Oracle Backend Deployment Script for Heroku

set -e  # Exit on any error

echo "🚀 Starting HTS Oracle Backend Deployment..."

# Check if Heroku CLI is installed
if ! command -v heroku &> /dev/null; then
    echo "❌ Heroku CLI is not installed. Please install it first:"
    echo "   https://devcenter.heroku.com/articles/heroku-cli"
    exit 1
fi

# Check if logged into Heroku
if ! heroku auth:whoami &> /dev/null; then
    echo "❌ Not logged into Heroku. Please run: heroku login"
    exit 1
fi

# App name (change this to your app name)
APP_NAME="hts-oracle-backend"

echo "📱 Deploying to Heroku app: $APP_NAME"

# Check if app exists, create if not
if ! heroku apps:info $APP_NAME &> /dev/null; then
    echo "🔧 Creating Heroku app: $APP_NAME"
    heroku create $APP_NAME
    heroku buildpacks:set heroku/python -a $APP_NAME
else
    echo "✅ Heroku app $APP_NAME already exists"
fi

# Set required environment variables (if not already set)
echo "🔧 Configuring environment variables..."

# Check if required vars are set
if ! heroku config:get ANTHROPIC_API_KEY -a $APP_NAME &> /dev/null || [ -z "$(heroku config:get ANTHROPIC_API_KEY -a $APP_NAME)" ]; then
    echo "⚠️  ANTHROPIC_API_KEY not set. Please set it manually:"
    echo "   heroku config:set ANTHROPIC_API_KEY=\"your_key_here\" -a $APP_NAME"
fi

if ! heroku config:get PINECONE_API_KEY -a $APP_NAME &> /dev/null || [ -z "$(heroku config:get PINECONE_API_KEY -a $APP_NAME)" ]; then
    echo "⚠️  PINECONE_API_KEY not set. Please set it manually:"
    echo "   heroku config:set PINECONE_API_KEY=\"your_key_here\" -a $APP_NAME"
fi

# Set production environment
heroku config:set FLASK_ENV="production" -a $APP_NAME --quiet
heroku config:set NETLIFY_URL="https://hts-oracle.netlify.app" -a $APP_NAME --quiet
heroku config:set FRONTEND_URL="https://hts-oracle.netlify.app" -a $APP_NAME --quiet
heroku config:set PINECONE_INDEX_NAME="commodity-hts-codes-new" -a $APP_NAME --quiet
heroku config:set PINECONE_DIMENSION="1024" -a $APP_NAME --quiet

echo "✅ Environment variables configured"

# Add Heroku remote if not exists
if ! git remote get-url heroku &> /dev/null; then
    echo "🔗 Adding Heroku remote..."
    heroku git:remote -a $APP_NAME
else
    echo "✅ Heroku remote already exists"
fi

# Deploy to Heroku
echo "📤 Deploying to Heroku..."
git push heroku main

# Check deployment status
echo "🔍 Checking deployment status..."
sleep 5

if heroku ps -a $APP_NAME | grep -q "web.*up"; then
    echo "✅ Deployment successful!"
    echo "🌐 Your API is available at: https://$APP_NAME.herokuapp.com"
    echo "🔍 Test health endpoint: https://$APP_NAME.herokuapp.com/api/health"
    
    # Test health endpoint
    echo "🧪 Testing health endpoint..."
    if curl -s "https://$APP_NAME.herokuapp.com/api/health" | grep -q "healthy"; then
        echo "✅ Health check passed!"
    else
        echo "⚠️  Health check failed. Check logs: heroku logs --tail -a $APP_NAME"
    fi
else
    echo "❌ Deployment may have failed. Check logs:"
    echo "   heroku logs --tail -a $APP_NAME"
    exit 1
fi

echo ""
echo "🎉 Deployment complete!"
echo "📊 Monitor your app:"
echo "   heroku logs --tail -a $APP_NAME"
echo "   heroku ps -a $APP_NAME"
echo ""
echo "🔧 Next steps:"
echo "1. Set your API keys if not already done:"
echo "   heroku config:set ANTHROPIC_API_KEY=\"your_key\" -a $APP_NAME"
echo "   heroku config:set PINECONE_API_KEY=\"your_key\" -a $APP_NAME"
echo "2. Deploy your frontend to Netlify"
echo "3. Test the complete application"