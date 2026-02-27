#!/bin/bash

echo "📊 Viewing Processed Meetings"
echo "=============================="
echo ""

# Check if jq is installed
if ! command -v jq &> /dev/null; then
    echo "⚠️  jq not installed. Showing raw output..."
    aws dynamodb scan \
        --table-name meeting-insights \
        --region us-east-1 \
        --output json
    exit 0
fi

# Get meetings from DynamoDB
MEETINGS=$(aws dynamodb scan \
    --table-name meeting-insights \
    --region us-east-1 \
    --output json)

COUNT=$(echo "$MEETINGS" | jq '.Count')

if [ "$COUNT" -eq 0 ]; then
    echo "📭 No meetings processed yet"
    echo ""
    echo "To test:"
    echo "1. Record a Zoom meeting with recording enabled"
    echo "2. Wait 5-10 minutes after meeting ends"
    echo "3. Check logs: aws logs tail /aws/lambda/meeting-ingestion-handler --follow"
    exit 0
fi

echo "Found $COUNT meeting(s):"
echo ""

# Display each meeting
echo "$MEETINGS" | jq -r '.Items[] | 
    "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
    "Meeting ID: \(.meeting_id.S)",
    "Timestamp: \(.timestamp.S)",
    "Status: \(.status.S)",
    "",
    "📝 Summary:",
    "  \(.summary.S)",
    "",
    (if .decisions.L then 
        "✅ Decisions:",
        (.decisions.L[] | "  • \(.S)")
    else empty end),
    "",
    (if .blockers.L and (.blockers.L | length > 0) then
        "🚧 Blockers:",
        (.blockers.L[] | "  • \(.S)")
    else empty end),
    "",
    (if .action_items.L and (.action_items.L | length > 0) then
        "📋 Action Items:",
        (.action_items.L[] | "  • \(.M.action.S) - Owner: \(.M.owner.S) (\(.M.priority.S))")
    else empty end),
    ""
'

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "💡 To view raw data:"
echo "aws dynamodb scan --table-name meeting-insights --region us-east-1"
