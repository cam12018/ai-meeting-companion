#!/usr/bin/env python3
"""
Generate test meetings by running transcripts through the AI pipeline
This mimics the normal ingestion pipeline but uses transcripts instead of audio
"""
import sys
sys.path.insert(0, 'src')

import boto3
from datetime import datetime, timedelta
from bedrock_service import extract_insights
from storage_service import store_meeting_insights

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('meeting-insights')

# Test meeting transcripts
test_transcripts = [
    {
        "meeting_id": "test-meeting-clean",
        "transcript": "Good morning everyone. Let's discuss Q1 planning. We've decided to move forward with the REST-to-GraphQL migration for our API redesign. This is a major decision that will improve our API performance. We also need to prioritize mobile app performance optimization. The main blocker is that we're waiting on the database schema finalization from the data team. We need that completed before we can proceed with the API work. Sarah, can you follow up with them? Also, we should implement enhanced error logging and alerting. Mike, can you start on the API design specification? Alex, we need you to work on the mobile performance spike next week."
    },
    {
        "meeting_id": "test-meeting-intermediate",
        "transcript": "Alright team, let's do our engineering standup. We're planning to deploy to staging this Friday. We've decided to use a new caching strategy for our database queries to improve performance. We also need to schedule a security audit for next month. The blockers we're facing are third-party API rate limiting issues and we're waiting on the design team for UI mockups. John, can you implement the caching layer for the database this week? We need someone to contact the third-party API support about the rate limiting. Sarah, can you review the security audit checklist for next week?"
    },
    {
        "meeting_id": "test-meeting-noisy",
        "transcript": "Welcome everyone to the all-hands meeting. We have some exciting updates. We've decided to expand our team by hiring 2 new engineers next quarter. We're also going to migrate to a new cloud provider to save costs. And we're implementing automated testing for all new features going forward. The main blocker is we're waiting on budget approval from finance. We also need to finish evaluating cloud provider options. Alex, can you prepare the hiring plan and job descriptions? Mike, we need you to get budget approval from finance this week. The team should evaluate the cloud provider options next week."
    }
]

# Process each transcript through the AI pipeline
for test in test_transcripts:
    meeting_id = test["meeting_id"]
    transcript = test["transcript"]
    
    try:
        print(f"Processing: {meeting_id}...")
        
        # Extract insights using Bedrock (same as real pipeline)
        insights = extract_insights(transcript)
        
        # Store in DynamoDB with pending_review status
        store_meeting_insights(
            meeting_id=meeting_id,
            insights=insights,
            metadata={"source": "test_generation", "transcript_length": len(transcript)}
        )
        
        print(f"✅ {meeting_id}")
        print(f"   Summary: {insights.get('summary', 'N/A')[:60]}...")
        print(f"   Decisions: {len(insights.get('decisions', []))} found")
        print(f"   Blockers: {len(insights.get('blockers', []))} found")
        print(f"   Action Items: {len(insights.get('action_items', []))} found")
        print()
        
    except Exception as e:
        print(f"❌ Error processing {meeting_id}: {e}")
        import traceback
        traceback.print_exc()

print("=" * 60)
print("Test meetings created successfully!")
print("=" * 60)
print("\nDashboard now has:")
print("  • 3 pending review meetings with AI-extracted insights")
print("  • Ready to review and approve")
print("\nYou can now:")
print("  1. View the dashboard to see all meetings")
print("  2. Click on any meeting to review AI-extracted insights")
print("  3. Record a live meeting to add to the dashboard")

