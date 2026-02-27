#!/bin/bash
# Configure S3 bucket to trigger Lambda on file uploads
# Run this after deploying the SAM stack

set -e

STACK_NAME="sam-app"
REGION="us-east-1"

echo "🔧 Configuring S3 trigger for Lambda..."
echo ""

# Get stack outputs
echo "📋 Fetching stack outputs..."
OUTPUTS=$(aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --region $REGION \
  --query 'Stacks[0].Outputs' \
  --output json)

BUCKET=$(echo $OUTPUTS | jq -r '.[] | select(.OutputKey=="AudioBucketName") | .OutputValue')
LAMBDA_ARN=$(echo $OUTPUTS | jq -r '.[] | select(.OutputKey=="IngestionFunctionArn") | .OutputValue')
LAMBDA_NAME=$(echo $LAMBDA_ARN | awk -F: '{print $NF}')

echo "✓ Bucket: $BUCKET"
echo "✓ Lambda: $LAMBDA_NAME"
echo ""

# Add Lambda permission for S3
echo "🔐 Adding S3 invoke permission to Lambda..."
aws lambda add-permission \
  --function-name $LAMBDA_NAME \
  --statement-id AllowS3Invoke \
  --action lambda:InvokeFunction \
  --principal s3.amazonaws.com \
  --source-arn "arn:aws:s3:::$BUCKET" \
  --region $REGION 2>/dev/null || echo "  (Permission may already exist)"

# Configure S3 bucket notification
echo "📤 Configuring S3 bucket notification..."
cat > /tmp/s3-notification.json <<EOF
{
  "LambdaFunctionConfigurations": [
    {
      "LambdaFunctionArn": "$LAMBDA_ARN",
      "Events": ["s3:ObjectCreated:*"],
      "Filter": {
        "Key": {
          "FilterRules": [
            {
              "Name": "prefix",
              "Value": "recordings/"
            }
          ]
        }
      }
    }
  ]
}
EOF

aws s3api put-bucket-notification-configuration \
  --bucket $BUCKET \
  --notification-configuration file:///tmp/s3-notification.json \
  --region $REGION

echo ""
echo "✅ S3 trigger configured successfully!"
echo ""
echo "📝 Next steps:"
echo "   1. Run: python auto_upload_recording.py"
echo "   2. Record a Zoom meeting in ~/Documents/Zoom/"
echo "   3. The recording will auto-upload and trigger Lambda processing"
echo "   4. Check Slack for notifications when processing completes"
