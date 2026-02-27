import json
import boto3
import requests

secrets_client = boto3.client('secretsmanager')

def send_slack_notification(meeting_id, insights, review_ready=False):
    """
    Send meeting insights to Slack
    """
    try:
        # Get Slack webhook URL from Secrets Manager
        webhook_url = get_slack_webhook_url()
        
        if not webhook_url:
            print("⚠️  No Slack webhook URL configured - skipping notification")
            print("💡 Insights are still saved to DynamoDB")
            print(f"📊 Meeting ID: {meeting_id}")
            print(f"📝 Summary: {insights.get('summary', 'N/A')}")
            return
        
        # Format the message
        message = format_slack_message(meeting_id, insights, review_ready)
        
        # Send to Slack
        response = requests.post(
            webhook_url,
            json=message,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        response.raise_for_status()
        print(f"✅ Slack notification sent successfully for meeting {meeting_id}")
        
    except Exception as e:
        print(f"⚠️  Error sending Slack notification: {str(e)}")
        print("💡 This is non-critical - insights are still saved to DynamoDB")
        # Don't raise - notification failure shouldn't break the pipeline

def format_slack_message(meeting_id, insights, review_ready=False):
    """
    Format insights into a Slack message
    """
    summary = insights.get('summary', 'No summary available')
    decisions = insights.get('decisions', [])
    blockers = insights.get('blockers', [])
    action_items = insights.get('action_items', [])
    
    if review_ready:
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "🎙️ Meeting Summary Ready for Review"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Summary:*\n{summary}"
                }
            }
        ]
    else:
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "🎙️ Meeting Summary Approved"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Summary:*\n{summary}"
                }
            }
        ]
    
    # Add decisions
    if decisions:
        decisions_text = "\n".join([f"• {d}" for d in decisions])
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*✅ Decisions Made:*\n{decisions_text}"
            }
        })
    
    # Add blockers
    if blockers:
        blockers_text = "\n".join([f"• {b}" for b in blockers])
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*🚧 Blockers:*\n{blockers_text}"
            }
        })
    
    # Add action items
    if action_items:
        action_text = "\n".join([
            f"• {item['action']} - *Owner:* {item.get('owner', 'Unassigned')} ({item.get('priority', 'medium')} priority)"
            for item in action_items
        ])
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*📋 Action Items:*\n{action_text}"
            }
        })
    
    # Add review UI link if review is ready
    if review_ready:
        review_url = f"https://7f2john8q9.execute-api.us-east-1.amazonaws.com/Prod/?id={meeting_id}"
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*📝 Review Required:*\n<{review_url}|Click here to review and approve the action items before they're created as Jira tickets.>"
            }
        })
    else:
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "✅ *Approved!* Action items have been published to Jira."
            }
        })
    
    # Add dashboard link
    dashboard_url = "https://7f2john8q9.execute-api.us-east-1.amazonaws.com/Prod/dashboard"
    blocks.append({
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": f"<{dashboard_url}|📊 View Meeting History Dashboard>"
        }
    })
    
    blocks.append({
        "type": "context",
        "elements": [
            {
                "type": "mrkdwn",
                "text": f"Meeting ID: `{meeting_id}`"
            }
        ]
    })
    
    return {"blocks": blocks}

def get_slack_webhook_url():
    """Get Slack webhook URL from Secrets Manager"""
    try:
        response = secrets_client.get_secret_value(
            SecretId='meeting-companion/slack'
        )
        secret_data = json.loads(response['SecretString'])
        return secret_data.get('webhook_url')
    except secrets_client.exceptions.ResourceNotFoundException:
        print("Slack webhook secret not found")
        return None
    except Exception as e:
        print(f"Error getting Slack webhook: {str(e)}")
        return None
