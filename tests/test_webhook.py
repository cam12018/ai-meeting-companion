#!/usr/bin/env python3
"""
Test the webhook endpoint with a simulated Zoom payload
"""
import json
import requests
import hmac
import hashlib
import time

# Your webhook URL
WEBHOOK_URL = "https://mmubd07gl3.execute-api.us-east-1.amazonaws.com/Prod/webhook/zoom"

# Zoom secret token
ZOOM_SECRET = "VZFzm5jnSRSwClN3l5UZsw"

def create_zoom_signature(payload, timestamp, secret):
    """Create Zoom webhook signature"""
    message = f"v0:{timestamp}:{payload}"
    hash_for_verify = hmac.new(
        secret.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return f"v0={hash_for_verify}"

def test_webhook_validation():
    """Test 1: Webhook validation (Zoom sends this first)"""
    print("🧪 Test 1: Webhook Validation")
    print("-" * 50)
    
    # Zoom sends a validation request when you first configure the webhook
    payload = json.dumps({
        "event": "endpoint.url_validation",
        "payload": {
            "plainToken": "test_token_123"
        }
    })
    
    timestamp = str(int(time.time()))
    signature = create_zoom_signature(payload, timestamp, ZOOM_SECRET)
    
    headers = {
        "Content-Type": "application/json",
        "x-zm-signature": signature,
        "x-zm-request-timestamp": timestamp
    }
    
    try:
        response = requests.post(WEBHOOK_URL, data=payload, headers=headers, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Webhook validation test passed!")
        else:
            print("⚠️  Unexpected status code")
        
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False

def test_webhook_without_signature():
    """Test 2: Webhook without signature (should fail)"""
    print("\n🧪 Test 2: Webhook Without Signature (Should Fail)")
    print("-" * 50)
    
    payload = json.dumps({
        "event": "recording.completed",
        "payload": {
            "object": {
                "id": "test-meeting-123"
            }
        }
    })
    
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(WEBHOOK_URL, data=payload, headers=headers, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 401:
            print("✅ Correctly rejected unsigned request!")
            return True
        else:
            print("⚠️  Should have returned 401 Unauthorized")
            return False
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False

def test_recording_completed():
    """Test 3: Simulated recording completed event"""
    print("\n🧪 Test 3: Recording Completed Event")
    print("-" * 50)
    
    # Simulate a real Zoom recording completed webhook
    payload = json.dumps({
        "event": "recording.completed",
        "payload": {
            "account_id": "test_account",
            "object": {
                "uuid": "test-uuid-123",
                "id": "test-meeting-456",
                "host_id": "test-host",
                "topic": "Test Meeting",
                "start_time": "2026-02-13T22:00:00Z",
                "duration": 5,
                "recording_files": [
                    {
                        "id": "test-file-1",
                        "recording_start": "2026-02-13T22:00:00Z",
                        "recording_end": "2026-02-13T22:05:00Z",
                        "file_type": "MP4",
                        "file_size": 1024000,
                        "recording_type": "shared_screen_with_speaker_view",
                        "download_url": "https://example.zoom.us/rec/download/test-file"
                    }
                ]
            }
        }
    })
    
    timestamp = str(int(time.time()))
    signature = create_zoom_signature(payload, timestamp, ZOOM_SECRET)
    
    headers = {
        "Content-Type": "application/json",
        "x-zm-signature": signature,
        "x-zm-request-timestamp": timestamp
    }
    
    try:
        response = requests.post(WEBHOOK_URL, data=payload, headers=headers, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Webhook accepted the recording event!")
            print("💡 Note: Actual processing will fail because the download URL is fake")
            print("   Check CloudWatch logs for details")
        else:
            print("⚠️  Unexpected status code")
        
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False

def test_basic_connectivity():
    """Test 0: Basic connectivity"""
    print("🧪 Test 0: Basic Connectivity")
    print("-" * 50)
    
    try:
        # Try a simple GET request (should return 403 or 404, but proves endpoint exists)
        response = requests.get(WEBHOOK_URL, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Endpoint is reachable!")
        print("✅ Basic connectivity test passed!")
        return True
    except requests.exceptions.Timeout:
        print("❌ Request timed out - endpoint may not be responding")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ Connection error - check the webhook URL")
        return False
    except Exception as e:
        print(f"⚠️  Error: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Testing Zoom Webhook Endpoint")
    print("=" * 50)
    print(f"URL: {WEBHOOK_URL}")
    print("=" * 50)
    print()
    
    results = []
    
    # Run tests
    results.append(("Basic Connectivity", test_basic_connectivity()))
    results.append(("Webhook Validation", test_webhook_validation()))
    results.append(("Unsigned Request", test_webhook_without_signature()))
    results.append(("Recording Event", test_recording_completed()))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Summary")
    print("=" * 50)
    
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{name}: {status}")
    
    print("\n💡 Next Steps:")
    print("1. Check CloudWatch logs:")
    print("   aws logs tail /aws/lambda/meeting-ingestion-handler --follow")
    print("2. If tests pass, try a real Zoom recording")
    print("3. View processed meetings: ./view_meetings.sh")
