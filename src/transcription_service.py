import boto3
import time
import json
import re
from datetime import datetime

transcribe_client = boto3.client('transcribe')
s3_client = boto3.client('s3')

def start_transcription(audio_s3_uri, meeting_id):
    """
    Start Amazon Transcribe job for meeting audio
    """
    # Sanitize meeting_id for Transcribe job name (only alphanumeric, dots, hyphens, underscores)
    sanitized_id = re.sub(r'[^0-9a-zA-Z._-]', '', meeting_id.replace(' ', '_').replace('+', '_'))
    job_name = f"meeting-{sanitized_id}-{int(time.time())}"
    
    try:
        response = transcribe_client.start_transcription_job(
            TranscriptionJobName=job_name,
            Media={'MediaFileUri': audio_s3_uri},
            MediaFormat='mp4',
            LanguageCode='en-US',
            Settings={
                'ShowSpeakerLabels': True,
                'MaxSpeakerLabels': 10
            },
            OutputBucketName=audio_s3_uri.split('/')[2]  # Use same bucket
        )
        
        print(f"Started transcription job: {job_name}")
        return job_name
    
    except Exception as e:
        print(f"Error starting transcription: {str(e)}")
        raise

def get_transcription_result(job_name):
    """
    Poll for transcription completion and return transcript
    """
    max_attempts = 120  # 20 minutes max
    attempt = 0
    
    while attempt < max_attempts:
        response = transcribe_client.get_transcription_job(
            TranscriptionJobName=job_name
        )
        
        status = response['TranscriptionJob']['TranscriptionJobStatus']
        
        if status == 'COMPLETED':
            transcript_uri = response['TranscriptionJob']['Transcript']['TranscriptFileUri']
            print(f"Transcription completed: {transcript_uri}")
            return fetch_transcript(transcript_uri)
        
        elif status == 'FAILED':
            reason = response['TranscriptionJob'].get('FailureReason', 'Unknown')
            raise Exception(f"Transcription failed: {reason}")
        
        print(f"Transcription status: {status}, attempt {attempt + 1}/{max_attempts}")
        time.sleep(10)
        attempt += 1
    
    raise Exception("Transcription timeout after 20 minutes")

def fetch_transcript(transcript_uri):
    """Fetch transcript from S3 URI or HTTPS URL"""
    import requests
    import re
    
    # Handle s3:// URIs
    match = re.match(r's3://([^/]+)/(.+)', transcript_uri)
    if match:
        bucket = match.group(1)
        key = match.group(2)
        response = s3_client.get_object(Bucket=bucket, Key=key)
        content = response['Body'].read().decode('utf-8')
        return json.loads(content)
    
    # Handle HTTPS URLs (like s3.us-east-1.amazonaws.com/...)
    if transcript_uri.startswith('https://'):
        # Extract bucket and key from the URL
        # Format: https://s3.region.amazonaws.com/bucket/key
        match = re.match(r'https://s3\.[^/]+\.amazonaws\.com/([^/]+)/(.+)', transcript_uri)
        if match:
            bucket = match.group(1)
            key = match.group(2)
            response = s3_client.get_object(Bucket=bucket, Key=key)
            content = response['Body'].read().decode('utf-8')
            return json.loads(content)
    
    # Fallback to requests for other URLs
    response = requests.get(transcript_uri)
    response.raise_for_status()
    return response.json()
