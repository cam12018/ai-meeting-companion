#!/bin/bash

echo "🔍 Checking AI Meeting Companion Status"
echo "========================================"
echo ""

# Check AWS credentials
echo "1️⃣  AWS Credentials:"
if aws sts get-caller-identity &> /dev/null; then
    ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
    echo "   ✅ Connected to AWS Account: $ACCOUNT"
else
    echo "   ❌ AWS credentials not configured"
fi
echo ""

# Check Lambda function
echo "2️⃣  Lambda Function:"
if aws lambda get-function --function-name meeting-ingestion-handler --region us-east-1 &> /dev/null; then
    echo "   ✅ Lambda function deployed"
    LAST_MODIFIED=$(aws lambda get-function --function-name meeting-ingestion-handler --region us-east-1 --query 'Configuration.LastModified' --output text)
    echo "   📅 Last updated: $LAST_MODIFIED"
else
    echo "   ❌ Lambda function not found"
fi
echo ""

# Check S3 bucket
echo "3️⃣  S3 Bucket:"
BUCKET_NAME="meeting-audio-$ACCOUNT"
if aws s3 ls "s3://$BUCKET_NAME" --region us-east-1 &> /dev/null; then
    echo "   ✅ S3 bucket exists: $BUCKET_NAME"
    FILE_COUNT=$(aws s3 ls "s3://$BUCKET_NAME" --recursive --region us-east-1 | wc -l)
    echo "   📁 Files in bucket: $FILE_COUNT (should be 0 after processing)"
else
    echo "   ❌ S3 bucket not found"
fi
echo ""

# Check DynamoDB table
echo "4️⃣  DynamoDB Table:"
if aws dynamodb describe-table --table-name meeting-insights --region us-east-1 &> /dev/null; then
    echo "   ✅ DynamoDB table exists"
    ITEM_COUNT=$(aws dynamodb scan --table-name meeting-insights --select COUNT --region us-east-1 --query 'Count' --output text)
    echo "   📊 Meetings processed: $ITEM_COUNT"
else
    echo "   ❌ DynamoDB table not found"
fi
echo ""

# Check Zoom secret
echo "5️⃣  Zoom Configuration:"
if aws secretsmanager get-secret-value --secret-id meeting-companion/zoom --region us-east-1 &> /dev/null; then
    echo "   ✅ Zoom secret configured"
else
    echo "   ❌ Zoom secret not found"
fi
echo ""

# Check Slack secret
echo "6️⃣  Slack Configuration:"
if aws secretsmanager get-secret-value --secret-id meeting-companion/slack --region us-east-1 &> /dev/null; then
    echo "   ✅ Slack webhook configured"
else
    echo "   ⚠️  Slack webhook not configured yet"
    echo "   💡 Run: ./setup_slack.sh"
fi
echo ""

# Check Bedrock access
echo "7️⃣  Amazon Bedrock:"
if aws bedrock list-foundation-models --region us-east-1 &> /dev/null; then
    echo "   ✅ Bedrock API accessible"
    echo "   💡 Make sure Claude 3 Haiku model access is enabled"
else
    echo "   ❌ Bedrock not accessible"
fi
echo ""

# Show webhook URL
echo "8️⃣  Webhook URL:"
STACK_OUTPUT=$(aws cloudformation describe-stacks --stack-name sam-app --region us-east-1 --query 'Stacks[0].Outputs[?OutputKey==`WebhookUrl`].OutputValue' --output text 2>/dev/null)
if [ ! -z "$STACK_OUTPUT" ]; then
    echo "   🔗 $STACK_OUTPUT"
    echo "   💡 Use this URL in your Zoom app Event Subscriptions"
else
    echo "   ❌ Could not retrieve webhook URL"
fi
echo ""

echo "========================================"
echo "✨ Status check complete!"
echo ""
echo "Next steps:"
echo "1. Configure Slack webhook: ./setup_slack.sh"
echo "2. Enable Bedrock model access in AWS Console"
echo "3. Test with a Zoom meeting recording"
echo "4. Monitor logs: aws logs tail /aws/lambda/meeting-ingestion-handler --follow"
