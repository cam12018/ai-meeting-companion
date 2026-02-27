#!/usr/bin/env python3
"""
Test Jira integration by creating a test ticket
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from jira_service import create_jira_tickets

# Sample action items from a meeting
test_action_items = [
    {
        "action": "Follow up with security team on IAM roles",
        "owner": "John",
        "priority": "high"
    },
    {
        "action": "Review database migration scripts",
        "owner": "Sarah",
        "priority": "medium"
    }
]

if __name__ == "__main__":
    print("🧪 Testing Jira Integration")
    print("=" * 50)
    print()
    
    try:
        tickets = create_jira_tickets("test-meeting-jira-001", test_action_items)
        
        print()
        print("=" * 50)
        print("✅ Test complete!")
        print()
        
        if tickets:
            print(f"Created {len(tickets)} Jira ticket(s):")
            for ticket in tickets:
                print(f"  • {ticket['key']}: {ticket['action']}")
                print(f"    URL: {ticket['url']}")
            print()
            print("Check your Jira project to see the tickets!")
        else:
            print("⚠️  No tickets were created. Check the logs above for errors.")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
