import json
import os
import boto3
import requests
import hmac
import hashlib
from datetime import datetime

s3_client = boto3.client('s3')
transcribe_client = boto3.client('transcribe')
bedrock_runtime = boto3.client('bedrock-runtime')
secrets_client = boto3.client('secretsmanager')

# Cache the secret
_zoom_secret = None

def get_zoom_secret():
    """Get Zoom secret token from Secrets Manager"""
    global _zoom_secret
    if _zoom_secret is None:
        response = secrets_client.get_secret_value(SecretId='meeting-companion/zoom')
        secret_data = json.loads(response['SecretString'])
        _zoom_secret = secret_data['secret_token']
    return _zoom_secret

def lambda_handler(event, context):
    """
    Main Lambda handler for Zoom webhook ingestion
    Triggered when Zoom recording is ready or S3 upload occurs
    """
    # Handle S3 event (manual uploads)
    if 'Records' in event and event['Records'][0].get('eventSource') == 'aws:s3':
        return handle_s3_event(event)
    
    # Handle Zoom webhook
    return handle_zoom_webhook(event)

def handle_s3_event(event):
    """Handle S3 upload event"""
    try:
        from urllib.parse import unquote_plus
        
        record = event['Records'][0]
        bucket = record['s3']['bucket']['name']
        key = unquote_plus(record['s3']['object']['key'])  # Decode URL-encoded key
        
        print(f"S3 event: {bucket}/{key}")
        
        # Extract meeting ID from key (format: recordings/{meeting_id}/filename.mp4)
        parts = key.split('/')
        if len(parts) >= 2:
            meeting_id = parts[1]
            print(f"Processing meeting: {meeting_id}")
            
            # Process the recording from S3
            s3_uri = f"s3://{bucket}/{key}"
            process_s3_recording(meeting_id, s3_uri)
            
            return {
                'statusCode': 200,
                'body': json.dumps({'message': f'Processing {meeting_id} from S3'})
            }
        
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Invalid S3 key format'})
        }
    
    except Exception as e:
        print(f"Error handling S3 event: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

def handle_zoom_webhook(event):
    """Handle Zoom webhook event"""
    try:
        # Parse Zoom webhook payload
        body = json.loads(event.get('body', '{}'))
        
        # Verify webhook authenticity
        if not verify_zoom_webhook(event):
            return {
                'statusCode': 401,
                'body': json.dumps({'error': 'Unauthorized'})
            }
        
        # Extract recording details
        recording_data = body.get('payload', {}).get('object', {})
        meeting_id = recording_data.get('id')
        recording_files = recording_data.get('recording_files', [])
        
        # Process audio recordings
        for recording in recording_files:
            if recording.get('file_type') == 'MP4' or recording.get('recording_type') == 'audio_only':
                download_url = recording.get('download_url')
                process_recording(meeting_id, download_url)
        
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Recording processing initiated'})
        }
    
    except Exception as e:
        print(f"Error processing webhook: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

def verify_zoom_webhook(event):
    """Verify Zoom webhook signature"""
    try:
        headers = event.get('headers', {})
        body = event.get('body', '')
        
        # Zoom sends signature in x-zm-signature header
        signature = headers.get('x-zm-signature', '')
        timestamp = headers.get('x-zm-request-timestamp', '')
        
        if not signature or not timestamp:
            print("Missing signature or timestamp")
            return False
        
        # Construct the message to verify
        message = f"v0:{timestamp}:{body}"
        
        # Get secret token
        secret_token = get_zoom_secret()
        
        # Calculate expected signature
        hash_for_verify = hmac.new(
            secret_token.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        expected_signature = f"v0={hash_for_verify}"
        
        # Compare signatures
        return hmac.compare_digest(signature, expected_signature)
    
    except Exception as e:
        print(f"Error verifying webhook: {str(e)}")
        return False

def process_s3_recording(meeting_id, s3_uri):
    """Process a recording that was uploaded directly to S3"""
    from transcription_service import start_transcription, get_transcription_result
    from bedrock_service import extract_insights
    from storage_service import store_meeting_insights, delete_audio_file, get_meeting_insights
    from slack_service import send_slack_notification
    
    try:
        # Check if meeting already exists (deduplication)
        existing = get_meeting_insights(meeting_id)
        if existing:
            print(f"Meeting {meeting_id} already processed - skipping duplicate")
            return
        
        # Start transcription
        print(f"Starting transcription for: {s3_uri}")
        job_name = start_transcription(s3_uri, meeting_id)
        
        # Wait for transcription to complete
        print(f"Waiting for transcription job: {job_name}")
        transcript_data = get_transcription_result(job_name)
        transcript_text = transcript_data['results']['transcripts'][0]['transcript']
        
        print(f"Transcript length: {len(transcript_text)} characters")
        
        # Extract insights using Bedrock
        print("Extracting insights with Amazon Bedrock...")
        insights = extract_insights(transcript_text)
        
        # Store in DynamoDB with pending_review status
        # Slack and Jira will be triggered by the review UI approval
        print("Storing insights in DynamoDB...")
        metadata = {
            'meeting_id': meeting_id,
            'transcript_length': len(transcript_text)
        }
        stored_item = store_meeting_insights(meeting_id, insights, metadata)
        
        # Delete audio file (privacy)
        print("Deleting audio file from S3...")
        bucket = s3_uri.split('/')[2]
        key = '/'.join(s3_uri.split('/')[3:])
        delete_audio_file(bucket, key)
        
        # Only send Slack notification if this is a new meeting (not a duplicate)
        if stored_item.get('status') == 'pending_review' and 'timestamp' in stored_item:
            # Check if this is a fresh insert by comparing timestamps
            from datetime import datetime, timedelta
            stored_time = datetime.fromisoformat(stored_item['timestamp'])
            now = datetime.utcnow()
            if (now - stored_time).total_seconds() < 5:  # Within 5 seconds = fresh insert
                print("Sending Slack notification that review is ready...")
                send_slack_notification(meeting_id, insights, review_ready=True)
                print(f"Meeting ready for review: {meeting_id}")
            else:
                print(f"Duplicate meeting detected - skipping Slack notification")
        else:
            print(f"Duplicate meeting detected - skipping Slack notification")
        
    except Exception as e:
        print(f"Error processing S3 recording: {str(e)}")
        raise

def process_recording(meeting_id, download_url):
    """Download and process meeting recording"""
    import uuid
    from transcription_service import start_transcription, get_transcription_result
    from bedrock_service import extract_insights
    from storage_service import store_meeting_insights, delete_audio_file
    from slack_service import send_slack_notification
    
    try:
        # Generate unique filename
        file_key = f"recordings/{meeting_id}/{uuid.uuid4()}.mp4"
        bucket_name = os.environ.get('AUDIO_BUCKET')
        
        # Download recording from Zoom
        print(f"Downloading recording from: {download_url}")
        zoom_token = get_zoom_access_token()
        headers = {'Authorization': f'Bearer {zoom_token}'}
        response = requests.get(download_url, headers=headers, stream=True)
        response.raise_for_status()
        
        # Upload to S3 temporarily
        print(f"Uploading to S3: {bucket_name}/{file_key}")
        s3_client.upload_fileobj(response.raw, bucket_name, file_key)
        
        # Start transcription
        s3_uri = f"s3://{bucket_name}/{file_key}"
        print(f"Starting transcription for: {s3_uri}")
        job_name = start_transcription(s3_uri, meeting_id)
        
        # Wait for transcription to complete
        print(f"Waiting for transcription job: {job_name}")
        transcript_data = get_transcription_result(job_name)
        transcript_text = transcript_data['results']['transcripts'][0]['transcript']
        
        print(f"Transcript length: {len(transcript_text)} characters")
        
        # Extract insights using Bedrock
        print("Extracting insights with Amazon Bedrock...")
        insights = extract_insights(transcript_text)
        
        # Store in DynamoDB with pending_review status
        # Slack and Jira will be triggered by the review UI approval
        print("Storing insights in DynamoDB...")
        metadata = {
            'meeting_id': meeting_id,
            'transcript_length': len(transcript_text)
        }
        stored_item = store_meeting_insights(meeting_id, insights, metadata)
        
        # Delete audio file (privacy)
        print("Deleting audio file from S3...")
        delete_audio_file(bucket_name, file_key)
        
        # Only send Slack notification if this is a new meeting (not a duplicate)
        if stored_item.get('status') == 'pending_review' and 'timestamp' in stored_item:
            # Check if this is a fresh insert by comparing timestamps
            from datetime import datetime, timedelta
            stored_time = datetime.fromisoformat(stored_item['timestamp'])
            now = datetime.utcnow()
            if (now - stored_time).total_seconds() < 5:  # Within 5 seconds = fresh insert
                print("Sending Slack notification that review is ready...")
                send_slack_notification(meeting_id, insights, review_ready=True)
                print(f"Meeting ready for review: {meeting_id}")
            else:
                print(f"Duplicate meeting detected - skipping Slack notification")
        else:
            print(f"Duplicate meeting detected - skipping Slack notification")
        
    except Exception as e:
        print(f"Error processing recording: {str(e)}")
        raise

def get_zoom_access_token():
    """Get Zoom OAuth access token"""
    # For now, return the download token from the webhook
    # In production, implement proper OAuth flow
    secret_data = json.loads(secrets_client.get_secret_value(
        SecretId='meeting-companion/zoom'
    )['SecretString'])
    
    # If you have OAuth credentials, use them
    if 'access_token' in secret_data:
        return secret_data['access_token']
    
    # Otherwise, Zoom download URLs include auth token
    return None
# Updated
