import boto3
import json
from datetime import datetime

dynamodb = boto3.resource('dynamodb')
s3_client = boto3.client('s3')

# Table will be created via CloudFormation/Terraform
MEETINGS_TABLE = 'meeting-insights'

def store_meeting_insights(meeting_id, insights, metadata):
    """
    Store processed meeting insights in DynamoDB
    Prevents duplicate entries by checking if meeting_id already exists
    """
    table = dynamodb.Table(MEETINGS_TABLE)
    
    # Check if meeting already exists
    response = table.get_item(Key={'meeting_id': meeting_id})
    if 'Item' in response:
        print(f"⚠️  Meeting {meeting_id} already exists - skipping duplicate")
        return response['Item']
    
    item = {
        'meeting_id': meeting_id,
        'timestamp': datetime.utcnow().isoformat(),
        'summary': insights.get('summary'),
        'decisions': insights.get('decisions', []),
        'blockers': insights.get('blockers', []),
        'action_items': insights.get('action_items', []),
        'metadata': metadata,
        'status': 'pending_review'  # Default status
    }
    
    table.put_item(Item=item)
    print(f"✅ Stored new meeting: {meeting_id}")
    return item

def delete_audio_file(s3_bucket, s3_key):
    """
    Delete audio file from S3 after processing (privacy)
    """
    try:
        s3_client.delete_object(Bucket=s3_bucket, Key=s3_key)
        print(f"Deleted audio file: s3://{s3_bucket}/{s3_key}")
    except Exception as e:
        print(f"Error deleting audio: {str(e)}")

def get_meeting_insights(meeting_id):
    """
    Retrieve meeting insights from DynamoDB
    Returns None if meeting doesn't exist
    """
    table = dynamodb.Table(MEETINGS_TABLE)
    response = table.get_item(Key={'meeting_id': meeting_id})
    return response.get('Item')
