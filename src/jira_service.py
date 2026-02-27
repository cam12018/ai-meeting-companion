import json
import boto3
import requests
from base64 import b64encode

secrets_client = boto3.client('secretsmanager')

def create_jira_tickets(meeting_id, action_items):
    """
    Create Jira tickets for approved action items
    """
    if not action_items:
        print("No action items to create tickets for")
        return []
    
    try:
        # Get Jira credentials
        jira_config = get_jira_config()
        
        if not jira_config:
            print("⚠️  No Jira configuration found - skipping ticket creation")
            return []
        
        created_tickets = []
        
        for item in action_items:
            ticket = create_single_ticket(jira_config, meeting_id, item)
            if ticket:
                created_tickets.append(ticket)
        
        print(f"✅ Created {len(created_tickets)} Jira tickets")
        return created_tickets
    
    except Exception as e:
        print(f"⚠️  Error creating Jira tickets: {str(e)}")
        # Don't raise - ticket creation failure shouldn't break the pipeline
        return []

def create_single_ticket(jira_config, meeting_id, action_item):
    """
    Create a single Jira ticket
    """
    try:
        url = f"{jira_config['url']}/rest/api/3/issue"
        
        # Create auth header
        auth_string = f"{jira_config['email']}:{jira_config['api_token']}"
        auth_header = b64encode(auth_string.encode()).decode()
        
        headers = {
            "Authorization": f"Basic {auth_header}",
            "Content-Type": "application/json"
        }
        
        # Map priority
        priority_map = {
            "high": "High",
            "medium": "Medium",
            "low": "Low"
        }
        
        priority = priority_map.get(action_item.get('priority', 'medium'), 'Medium')
        
        # Create ticket payload
        payload = {
            "fields": {
                "project": {
                    "key": jira_config['project_key']
                },
                "summary": action_item['action'],
                "description": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [
                                {
                                    "type": "text",
                                    "text": f"Action item from meeting: {meeting_id}"
                                }
                            ]
                        },
                        {
                            "type": "paragraph",
                            "content": [
                                {
                                    "type": "text",
                                    "text": f"Owner: {action_item.get('owner', 'Unassigned')}"
                                }
                            ]
                        },
                        {
                            "type": "paragraph",
                            "content": [
                                {
                                    "type": "text",
                                    "text": f"Priority: {priority}"
                                }
                            ]
                        }
                    ]
                },
                "issuetype": {
                    "name": "Task"
                },
                "priority": {
                    "name": priority
                }
            }
        }
        
        # Try to find and assign the owner
        owner = action_item.get('owner', '')
        if owner:
            assignee_id = get_assignee_id(owner)
            if assignee_id:
                payload['fields']['assignee'] = {
                    "accountId": assignee_id
                }
                print(f"   Assigned to: {owner} ({assignee_id})")
            else:
                print(f"   ⚠️  User '{owner}' not found in Jira - ticket created without assignee")
        
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        
        ticket_data = response.json()
        ticket_key = ticket_data['key']
        ticket_url = f"{jira_config['url']}/browse/{ticket_key}"
        
        print(f"✅ Created Jira ticket: {ticket_key} - {action_item['action']}")
        
        return {
            "key": ticket_key,
            "url": ticket_url,
            "action": action_item['action'],
            "owner": action_item.get('owner', 'Unassigned')
        }
    
    except requests.exceptions.HTTPError as e:
        print(f"❌ HTTP error creating ticket: {e.response.status_code} - {e.response.text}")
        return None
    except Exception as e:
        print(f"❌ Error creating ticket for '{action_item['action']}': {str(e)}")
        return None

def get_jira_config():
    """Get Jira configuration from Secrets Manager"""
    try:
        response = secrets_client.get_secret_value(
            SecretId='meeting-companion/jira'
        )
        config = json.loads(response['SecretString'])
        
        # Validate required fields
        required = ['url', 'email', 'api_token', 'project_key']
        if not all(field in config for field in required):
            print(f"⚠️  Jira config missing required fields: {required}")
            return None
        
        return config
    
    except secrets_client.exceptions.ResourceNotFoundException:
        print("ℹ️  Jira not configured (secret not found)")
        return None
    except Exception as e:
        print(f"⚠️  Error getting Jira config: {str(e)}")
        return None

def get_assignee_id(name):
    """Get Jira account ID for a person by searching for them"""
    try:
        config = get_jira_config()
        if not config:
            return None
        
        url = f"{config['url']}/rest/api/3/user/search"
        auth_string = f"{config['email']}:{config['api_token']}"
        auth_header = b64encode(auth_string.encode()).decode()
        
        headers = {
            "Authorization": f"Basic {auth_header}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(url, headers=headers, params={'query': name}, timeout=10)
        response.raise_for_status()
        
        users = response.json()
        if users:
            # Return the first matching user's account ID
            return users[0].get('accountId')
        
        return None
    
    except Exception as e:
        print(f"⚠️  Error finding user '{name}': {str(e)}")
        return None

def update_slack_with_tickets(webhook_url, meeting_id, tickets):
    """
    Send a follow-up Slack message with created Jira tickets
    """
    if not tickets:
        return
    
    try:
        ticket_links = "\n".join([
            f"• <{ticket['url']}|{ticket['key']}>: {ticket['action']} ({ticket['owner']})"
            for ticket in tickets
        ])
        
        message = {
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*📋 Jira Tickets Created for Meeting {meeting_id}*\n\n{ticket_links}"
                    }
                }
            ]
        }
        
        response = requests.post(webhook_url, json=message, timeout=10)
        response.raise_for_status()
        
        print(f"✅ Sent Jira ticket update to Slack")
    
    except Exception as e:
        print(f"⚠️  Error sending Jira update to Slack: {str(e)}")
