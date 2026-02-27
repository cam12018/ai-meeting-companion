import json
import boto3
import os
import urllib.parse

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ.get('MEETINGS_TABLE', 'meeting-insights'))

def lambda_handler(event, context):
    """Handle review UI requests"""
    path = event.get('path', '')
    http_method = event.get('httpMethod', '')
    
    # Handle CORS preflight requests
    if http_method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Max-Age': '86400'
            },
            'body': ''
        }
    
    elif path == '/api/meetings' and http_method == 'GET':
        return list_meetings(event)
    
    elif path == '/api/meetings/history' and http_method == 'GET':
        return get_meeting_history(event)
    
    elif path.startswith('/api/meetings/') and http_method == 'GET':
        # Extract meeting_id from path, handling URL encoding
        meeting_id = urllib.parse.unquote(path.split('/api/meetings/')[-1])
        return get_meeting(meeting_id)
    
    elif path.startswith('/api/meetings/') and http_method == 'POST':
        # Extract meeting_id from path, handling URL encoding
        parts = path.split('/')
        meeting_id = urllib.parse.unquote(parts[-2])
        return approve_meeting(meeting_id, event)
    
    elif path == '/dashboard':
        html_path = os.path.join(os.path.dirname(__file__), 'dashboard.html')
        with open(html_path, 'r') as f:
            html_content = f.read()
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'text/html'},
            'body': html_content
        }
    
    elif path == '/':
        html_path = os.path.join(os.path.dirname(__file__), 'index.html')
        with open(html_path, 'r') as f:
            html_content = f.read()
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'text/html'},
            'body': html_content
        }
    
    return {
        'statusCode': 404,
        'headers': {
            'Access-Control-Allow-Origin': '*',
            'Content-Type': 'application/json'
        },
        'body': json.dumps({'error': 'Not found'})
    }

def list_meetings(event):
    """List pending meetings"""
    try:
        response = table.scan(
            FilterExpression='#status = :status',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={':status': 'pending_review'}
        )
        
        meetings = []
        for item in response.get('Items', []):
            meetings.append({
                'meeting_id': item['meeting_id'],
                'timestamp': item['timestamp'],
                'summary': item.get('summary', '')[:100] + '...' if len(item.get('summary', '')) > 100 else item.get('summary', '')
            })
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Cache-Control': 'no-store, no-cache, must-revalidate, max-age=0',
                'Pragma': 'no-cache',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Max-Age': '86400'
            },
            'body': json.dumps({'meetings': meetings})
        }
    
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

def get_meeting_history(event):
    """Get all meetings (approved and pending) for history dashboard"""
    try:
        response = table.scan()
        
        meetings = []
        for item in response.get('Items', []):
            meetings.append({
                'meeting_id': item['meeting_id'],
                'timestamp': item['timestamp'],
                'summary': item.get('summary', '')[:100] + '...' if len(item.get('summary', '')) > 100 else item.get('summary', ''),
                'status': item.get('status', 'pending_review'),
                'action_items_count': len(item.get('action_items', [])),
                'decisions_count': len(item.get('decisions', [])),
                'blockers_count': len(item.get('blockers', []))
            })
        
        # Sort by timestamp descending (newest first)
        meetings.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Cache-Control': 'no-store, no-cache, must-revalidate, max-age=0',
                'Pragma': 'no-cache',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'meetings': meetings})
        }
    
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

def get_meeting(meeting_id):
    """Get meeting details"""
    try:
        response = table.get_item(Key={'meeting_id': meeting_id})
        item = response.get('Item')
        
        if not item:
            return {
                'statusCode': 404,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'Meeting not found'})
            }
        
        # Return meeting details for the UI
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Cache-Control': 'no-store, no-cache, must-revalidate, max-age=0'
            },
            'body': json.dumps({
                'meeting_id': item['meeting_id'],
                'summary': item.get('summary'),
                'decisions': item.get('decisions', []),
                'blockers': item.get('blockers', []),
                'action_items': item.get('action_items', []),
                'status': item.get('status', 'pending_review')
            })
        }
    
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': str(e)})
        }

def approve_meeting(meeting_id, event):
    """Approve meeting and trigger Slack/Jira"""
    try:
        # First check if meeting is already approved
        response = table.get_item(Key={'meeting_id': meeting_id})
        item = response.get('Item')
        
        if not item:
            return {
                'statusCode': 404,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'Meeting not found'})
            }
        
        if item.get('status') == 'approved':
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'Meeting already approved'})
            }
        
        body = json.loads(event.get('body', '{}'))
        action_items = body.get('action_items', [])
        
        # Update meeting status (use #status because status is a reserved keyword)
        table.update_item(
            Key={'meeting_id': meeting_id},
            UpdateExpression='SET #status = :status, action_items = :action_items',
            ExpressionAttributeNames={
                '#status': 'status'
            },
            ExpressionAttributeValues={
                ':status': 'approved',
                ':action_items': action_items
            }
        )
        
        # Get meeting details for Slack/Jira
        response = table.get_item(Key={'meeting_id': meeting_id})
        item = response.get('Item')
        
        # Send to Slack (approved notification)
        from slack_service import send_slack_notification
        send_slack_notification(meeting_id, {
            'summary': item.get('summary'),
            'decisions': item.get('decisions', []),
            'blockers': item.get('blockers', []),
            'action_items': action_items
        }, review_ready=False)
        
        # Create Jira tickets
        from jira_service import create_jira_tickets
        create_jira_tickets(meeting_id, action_items)
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'message': 'Meeting approved and published'})
        }
    
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': str(e)})
        }
