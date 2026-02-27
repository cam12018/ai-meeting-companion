import json
import boto3

bedrock_runtime = boto3.client('bedrock-runtime', region_name='us-east-1')

def extract_insights(transcript_text):
    """
    Use Amazon Bedrock to extract meeting insights
    Returns: dict with summary, blockers, action_items
    """
    
    # Check if transcript is meaningful (not empty or just silence)
    if len(transcript_text.strip()) < 100:
        print("⚠️  Transcript is too short or empty - using demo insights")
        return get_demo_insights()
    
    prompt = f"""You are an expert meeting analyst for a tech team. Analyze this meeting transcript and extract SPECIFIC, ACTIONABLE insights.

CRITICAL: Action items MUST be specific and technical. Examples:
- GOOD: "Follow up with the security team about the IAM rules for the new S3 bucket"
- GOOD: "Update the deployment runbook with the new PostgreSQL configuration details"
- GOOD: "Review the database migration scripts for performance issues"
- BAD: "Follow up with security team"
- BAD: "Update documentation"

1. **Summary** (2-3 sentences): What was the meeting about? Key technical outcomes?
2. **Decisions Made**: Specific technical decisions reached
3. **Blockers/Issues**: Technical problems that need resolution
4. **Action Items**: MUST include:
   - Clear, specific technical task description
   - Assigned person (extract names from transcript: John, Sarah, Mike, Alex, etc.)
   - Priority (high/medium/low based on urgency and impact)
   - If no names mentioned, use "Unassigned"

Transcript:
{transcript_text}

Provide the response in JSON format:
{{
  "summary": "...",
  "decisions": ["decision 1", "decision 2"],
  "blockers": ["blocker 1", "blocker 2"],
  "action_items": [
    {{"action": "Specific, technical task description with details", "owner": "Person's name or Unassigned", "priority": "high|medium|low"}}
  ]
}}

IMPORTANT: 
- Be specific about technologies mentioned (AWS services, databases, frameworks, etc.)
- Include concrete details in action items
- Focus on technical implementation tasks
- If the transcript is about infrastructure, include specific AWS services
- If about security, include specific security controls or compliance requirements
"""
    
    try:
        # Using Claude 3 Haiku (cost-effective for Free Tier)
        response = bedrock_runtime.invoke_model(
            modelId='anthropic.claude-3-haiku-20240307-v1:0',
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 2000,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            })
        )
        
        response_body = json.loads(response['body'].read())
        content = response_body['content'][0]['text']
        
        # Parse JSON from response
        insights = json.loads(content)
        return insights
    
    except Exception as e:
        print(f"Error extracting insights: {str(e)}")
        # Return demo insights if Bedrock fails
        print("Using demo insights (Bedrock not available)")
        return get_demo_insights()

def get_demo_insights():
    """Return realistic, specific demo insights for testing"""
    return {
        "summary": "Team discussed infrastructure updates and security compliance. Decided to implement new IAM rules for S3 buckets and update PostgreSQL configuration. Need security team approval for the new IAM policies.",
        "decisions": [
            "Implement new IAM rules for S3 bucket access by Friday",
            "Update PostgreSQL configuration from 13 to 14 with new performance settings",
            "Schedule security review for the new authentication system"
        ],
        "blockers": [
            "Security team needs to review new IAM policies before implementation",
            "Database migration from PostgreSQL 13 to 14 requires downtime planning",
            "AWS budget constraints for new infrastructure"
        ],
        "action_items": [
            {"action": "Follow up with the security team about the IAM rules for the new S3 bucket", "owner": "Alex", "priority": "high"},
            {"action": "Update the deployment runbook with the new PostgreSQL 14 configuration details", "owner": "Sarah", "priority": "high"},
            {"action": "Review the database migration scripts for performance issues before production deployment", "owner": "John", "priority": "high"},
            {"action": "Configure CloudWatch alarms for the new authentication service API endpoints", "owner": "Mike", "priority": "medium"},
            {"action": "Update the API documentation with the new GraphQL schema changes", "owner": "Sarah", "priority": "medium"},
            {"action": "Test the new IAM policies in the staging environment before production rollout", "owner": "Alex", "priority": "high"}
        ]
    }
