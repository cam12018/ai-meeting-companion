#!/usr/bin/env python3
"""
Test script to verify the pipeline components
"""
import json
import sys

def test_bedrock():
    """Test Bedrock insight extraction"""
    print("🧪 Testing Amazon Bedrock...")
    
    sample_transcript = """
    John: Hey team, let's discuss the Q1 roadmap. We need to finalize the API design.
    Sarah: I agree. I think we should prioritize the authentication module first.
    John: Good point. Sarah, can you take the lead on that?
    Sarah: Sure, I'll have a draft by Friday.
    Mike: One blocker - we're still waiting on the database schema approval.
    John: Okay, I'll follow up with the architecture team today.
    """
    
    try:
        from src.bedrock_service import extract_insights
        insights = extract_insights(sample_transcript)
        
        print("✅ Bedrock test passed!")
        print(json.dumps(insights, indent=2))
        return True
    except Exception as e:
        print(f"❌ Bedrock test failed: {str(e)}")
        return False

def test_slack():
    """Test Slack notification"""
    print("\n🧪 Testing Slack integration...")
    
    sample_insights = {
        "summary": "Team discussed Q1 roadmap and prioritized authentication module",
        "decisions": ["Prioritize authentication module first"],
        "blockers": ["Waiting on database schema approval"],
        "action_items": [
            {"action": "Draft authentication module design", "owner": "Sarah", "priority": "high"},
            {"action": "Follow up with architecture team", "owner": "John", "priority": "high"}
        ]
    }
    
    try:
        from src.slack_service import send_slack_notification
        send_slack_notification("test-meeting-123", sample_insights)
        
        print("✅ Slack test passed!")
        return True
    except Exception as e:
        print(f"❌ Slack test failed: {str(e)}")
        return False

def test_storage():
    """Test DynamoDB storage"""
    print("\n🧪 Testing DynamoDB storage...")
    
    sample_insights = {
        "summary": "Test meeting summary",
        "decisions": ["Test decision"],
        "blockers": [],
        "action_items": []
    }
    
    try:
        from src.storage_service import store_meeting_insights
        result = store_meeting_insights("test-meeting-456", sample_insights, {"test": True})
        
        print("✅ Storage test passed!")
        print(f"Stored meeting: {result['meeting_id']}")
        return True
    except Exception as e:
        print(f"❌ Storage test failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Testing AI Meeting Companion Pipeline\n")
    
    results = []
    results.append(("Bedrock", test_bedrock()))
    results.append(("Slack", test_slack()))
    results.append(("Storage", test_storage()))
    
    print("\n" + "="*50)
    print("Test Results:")
    print("="*50)
    
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{name}: {status}")
    
    all_passed = all(result[1] for result in results)
    sys.exit(0 if all_passed else 1)
