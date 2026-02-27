#!/usr/bin/env python3
"""
Test Slack notification with sample meeting insights
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from slack_service import send_slack_notification

# Sample meeting insights
sample_insights = {
    "summary": "Team discussed Q1 roadmap priorities. Decided to focus on authentication module first. Sarah will lead the design work. Main blocker is waiting for database schema approval from architecture team.",
    "decisions": [
        "Prioritize authentication module for Q1",
        "Use OAuth 2.0 for user authentication",
        "Deploy to staging environment by end of week"
    ],
    "blockers": [
        "Waiting on database schema approval from architecture team",
        "Need additional AWS credits for load testing"
    ],
    "action_items": [
        {
            "action": "Draft authentication module design document",
            "owner": "Sarah",
            "priority": "high"
        },
        {
            "action": "Follow up with architecture team on schema approval",
            "owner": "John",
            "priority": "high"
        },
        {
            "action": "Request additional AWS credits from finance",
            "owner": "Mike",
            "priority": "medium"
        },
        {
            "action": "Set up staging environment for testing",
            "owner": "DevOps Team",
            "priority": "medium"
        }
    ]
}

if __name__ == "__main__":
    print("🧪 Testing Slack Notification")
    print("=" * 50)
    print()
    
    try:
        send_slack_notification("test-meeting-789", sample_insights)
        print()
        print("✅ Test complete!")
        print()
        print("Check your Slack channel for the formatted message.")
        print("It should include:")
        print("  • Meeting summary")
        print("  • Decisions made")
        print("  • Blockers identified")
        print("  • Action items with owners and priorities")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
