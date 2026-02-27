#!/usr/bin/env python3
"""
Test Jira integration by creating sample tickets
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from jira_service import create_jira_tickets, get_jira_config

# Sample action items
sample_action_items = [
    {
        "action": "Review authentication module design",
        "owner": "Sarah",
        "priority": "high"
    },
    {
        "action": "Update deployment documentation",
        "owner": "John",
        "priority": "medium"
    },
    {
        "action": "Investigate CI/CD timeout issues",
        "owner": "Mike",
        "priority": "high"
    }
]

if __name__ == "__main__":
    print("🧪 Testing Jira Integration")
    print("=" * 50)
    print()
    
    # Check if Jira is configured
    config = get_jira_config()
    
    if not config:
        print("❌ Jira not configured")
        print()
        print("To configure Jira:")
        print("1. Create a free Jira site at https://www.atlassian.com/try/cloud/signup")
        print("2. Create a project and note the project key")
        print("3. Run: ./setup_jira.sh")
        print()
        print("Or skip Jira - the pipeline works without it!")
        sys.exit(1)
    
    print(f"✅ Jira configured:")
    print(f"   URL: {config['url']}")
    print(f"   Project: {config['project_key']}")
    print(f"   Email: {config['email']}")
    print()
    
    print("Creating test tickets...")
    print()
    
    try:
        tickets = create_jira_tickets("test-meeting-jira-123", sample_action_items)
        
        if tickets:
            print()
            print("=" * 50)
            print(f"✅ Successfully created {len(tickets)} tickets!")
            print("=" * 50)
            print()
            
            for ticket in tickets:
                print(f"🎫 {ticket['key']}: {ticket['action']}")
                print(f"   Owner: {ticket['owner']}")
                print(f"   URL: {ticket['url']}")
                print()
            
            print("Check your Jira board to see the tickets!")
        else:
            print("⚠️  No tickets were created. Check the logs above for errors.")
            sys.exit(1)
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
