#!/bin/bash

echo "🔍 Diagnosing Zoom Integration"
echo "========================================"
echo ""

# Check Lambda logs
echo "1️⃣  Checking Lambda logs (last 1 hour)..."
LOGS=$(aws logs tail /aws/lambda/meeting-ingestion-handler --since 1h --region us-east-1 2>&1)

if [ -z "$LOGS" ]; then
    echo "   ⚠️  No Lambda invocations in the last hour"
    echo "   This means Zoom hasn't sent any webhooks"
else
    echo "   ✅ Found Lambda logs:"
    echo "$LOGS" | head -20
fi
echo ""

# Check DynamoDB
echo "2️⃣  Checking DynamoDB for processed meetings..."
MEETING_COUNT=$(aws dynamodb scan --table-name meeting-insights --select COUNT --region us-east-1 --query 'Count' --output text 2>&1)

if [ "$MEETING_COUNT" = "0" ]; then
    echo "   📭 No meetings processed yet"
else
    echo "   ✅ Found $MEETING_COUNT meeting(s)"
fi
echo ""

# Check S3 bucket
echo "3️⃣  Checking S3 bucket for audio files..."
BUCKET_NAME="meeting-audio-069908900405"
FILE_COUNT=$(aws s3 ls "s3://$BUCKET_NAME" --recursive --region us-east-1 2>&1 | wc -l)

if [ "$FILE_COUNT" -eq 0 ]; then
    echo "   📭 No audio files (expected - they're deleted after processing)"
else
    echo "   📁 Found $FILE_COUNT file(s) in bucket"
    aws s3 ls "s3://$BUCKET_NAME" --recursive --region us-east-1
fi
echo ""

# Test webhook connectivity
echo "4️⃣  Testing webhook endpoint..."
WEBHOOK_URL="https://mmubd07gl3.execute-api.us-east-1.amazonaws.com/Prod/webhook/zoom"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$WEBHOOK_URL")

if [ "$HTTP_CODE" = "403" ] || [ "$HTTP_CODE" = "401" ]; then
    echo "   ✅ Webhook endpoint is responding (HTTP $HTTP_CODE)"
else
    echo "   ⚠️  Unexpected response: HTTP $HTTP_CODE"
fi
echo ""

echo "========================================"
echo "📋 Diagnosis Summary"
echo "========================================"
echo ""

if [ -z "$LOGS" ]; then
    echo "❌ ISSUE: Zoom is not sending webhooks to your endpoint"
    echo ""
    echo "Possible causes:"
    echo "1. Webhook URL not configured in Zoom app"
    echo "2. Event subscription not set up for 'recording.completed'"
    echo "3. Recording was local (not cloud)"
    echo "4. Zoom app not activated"
    echo ""
    echo "Next steps:"
    echo "1. Go to https://marketplace.zoom.us/"
    echo "2. Open your app → Feature → Event Subscriptions"
    echo "3. Verify URL: $WEBHOOK_URL"
    echo "4. Verify 'recording.completed' event is subscribed"
    echo "5. Check 'Event Subscription Log' for any errors"
    echo "6. Ensure cloud recording is enabled in Zoom settings"
else
    echo "✅ Webhook is receiving events!"
    echo ""
    echo "Check the logs above for processing details."
fi
echo ""
echo "📖 For detailed setup instructions, see: ZOOM_WEBHOOK_SETUP.md"
