#!/bin/bash

set -e

echo "🚀 Deploying AI Meeting Companion..."

# Check if SAM CLI is installed
if ! command -v sam &> /dev/null; then
    echo "❌ AWS SAM CLI not found. Installing..."
    brew tap aws/tap
    brew install aws-sam-cli
fi

# Build the application
echo "📦 Building application..."
sam build

# Deploy the application
echo "🌐 Deploying to AWS..."
sam deploy --guided --capabilities CAPABILITY_IAM

echo "✅ Deployment complete!"
echo ""
echo "📋 Next steps:"
echo "1. Copy the WebhookUrl from the outputs above"
echo "2. Go to Zoom Developer Portal"
echo "3. Paste the URL in Event Notification Endpoint URL"
echo "4. Subscribe to 'Recording Completed' events"
