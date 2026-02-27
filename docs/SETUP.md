# Setup Guide - AI Meeting Companion

Complete setup instructions for the AI Meeting Companion system.

## Prerequisites

- AWS Account (free tier eligible)
- Zoom Account (Pro or higher for cloud recording)
- Slack Workspace (admin access)
- Jira Cloud Account (free tier available)
- macOS/Linux with Python 3.12+
- AWS CLI and SAM CLI installed

## Step 1: AWS Infrastructure Setup

### 1.1 Configure AWS Credentials

```bash
aws configure
```

Enter your AWS credentials when prompted:
- AWS Access Key ID
- AWS Secret Access Key
- Default region: `us-east-1`
- Default output format: `json`

### 1.2 Deploy Infrastructure

```bash
sam build
sam deploy --guided
```

During deployment, accept the defaults. This will create:
- Lambda functions (ingestion + review UI)
- API Gateway endpoints
- DynamoDB table for meeting storage
- S3 bucket for temporary audio files
- CloudWatch logs

**Save these outputs:**
- Webhook URL: `https://<api-id>.execute-api.us-east-1.amazonaws.com/Prod/webhook/zoom`
- Review UI URL: `https://<api-id>.execute-api.us-east-1.amazonaws.com/Prod/`
- S3 Bucket: `meeting-audio-<account-id>`

## Step 2: Zoom Integration

### 2.1 Get Zoom Credentials

1. Go to [Zoom App Marketplace](https://marketplace.zoom.us)
2. Click "Develop" → "Build App"
3. Choose "Server-to-Server OAuth"
4. Fill in app details and create

### 2.2 Store Zoom Secret in AWS Secrets Manager

```bash
aws secretsmanager create-secret \
  --name meeting-companion/zoom \
  --secret-string '{
    "secret_token": "YOUR_ZOOM_SECRET_TOKEN",
    "access_token": "YOUR_ZOOM_ACCESS_TOKEN"
  }'
```

### 2.3 Configure Zoom Webhook

1. In Zoom App settings, go to "Event Subscriptions"
2. Enable "Event Subscriptions"
3. Set Request URL to your webhook URL from Step 1.2
4. Subscribe to: `recording.completed`
5. Save and verify

## Step 3: Slack Integration

### 3.1 Create Slack App

1. Go to [Slack API](https://api.slack.com/apps)
2. Click "Create New App" → "From scratch"
3. Name: "Meeting Companion"
4. Choose your workspace

### 3.2 Configure Slack Permissions

1. Go to "OAuth & Permissions"
2. Add these scopes:
   - `chat:write`
   - `incoming-webhook`
3. Install app to workspace
4. Copy "Bot User OAuth Token"

### 3.3 Create Incoming Webhook

1. Go to "Incoming Webhooks"
2. Click "Add New Webhook to Workspace"
3. Select channel (e.g., #meetings)
4. Copy webhook URL

### 3.4 Store Slack Credentials

```bash
aws secretsmanager create-secret \
  --name meeting-companion/slack \
  --secret-string '{
    "webhook_url": "YOUR_SLACK_WEBHOOK_URL",
    "bot_token": "YOUR_BOT_TOKEN"
  }'
```

## Step 4: Jira Integration

### 4.1 Create Jira API Token

1. Go to [Atlassian Account Settings](https://id.atlassian.com/manage-profile/security/api-tokens)
2. Click "Create API token"
3. Copy the token

### 4.2 Get Jira Project Key

1. Go to your Jira project
2. Project key is in the URL: `https://your-domain.atlassian.net/browse/PROJECTKEY-1`
3. Note the project key (e.g., `SCRUM`)

### 4.3 Store Jira Credentials

```bash
aws secretsmanager create-secret \
  --name meeting-companion/jira \
  --secret-string '{
    "domain": "your-domain.atlassian.net",
    "email": "your-email@example.com",
    "api_token": "YOUR_API_TOKEN",
    "project_key": "SCRUM"
  }'
```

## Step 5: Local Testing Setup

### 5.1 Install Python Dependencies

```bash
pip install -r requirements.txt
pip install -r src/requirements.txt
pip install -r review-ui/requirements.txt
```

### 5.2 Run Auto-Uploader (Background)

For local testing, run the auto-uploader in the background:

```bash
python3 auto_upload_recording.py &
```

This monitors `~/Documents/Zoom` for new recordings and automatically uploads them to S3, triggering the full pipeline.

### 5.3 Test with Sample Transcripts

```bash
python3 tests/test_transcripts.py
```

This processes 3 test meetings with varying complexity:
- **Clean**: Structured meeting with clear assignments
- **Intermediate**: Some ambiguity and implied owners
- **Heavy**: Chaotic meeting with unclear responsibilities

## Step 6: Access the System

### Review UI
- **Pending Meetings**: `https://<api-id>.execute-api.us-east-1.amazonaws.com/Prod/`
- **Meeting History Dashboard**: `https://<api-id>.execute-api.us-east-1.amazonaws.com/Prod/dashboard`

### Workflow

1. **Record Meeting**: Use Zoom to record a meeting
2. **Auto-Upload**: Recording automatically uploads to S3 (if auto-uploader is running)
3. **Processing**: Lambda transcribes and extracts insights
4. **Slack Notification**: Team gets Slack message with review link
5. **Review**: Click link to review and approve action items
6. **Jira**: Approved items automatically create Jira tickets

## Troubleshooting

### Recordings Not Uploading
- Ensure `auto_upload_recording.py` is running: `ps aux | grep auto_upload`
- Check `~/Documents/Zoom` folder exists
- Verify AWS credentials are configured

### Slack Notifications Not Sending
- Check Slack webhook URL in Secrets Manager
- Verify Slack app has `chat:write` permission
- Check CloudWatch logs: `aws logs tail /aws/lambda/meeting-ingestion-handler --follow`

### Jira Tickets Not Creating
- Verify Jira credentials in Secrets Manager
- Check project key is correct
- Ensure Jira user has permission to create issues

### Lambda Timeouts
- Increase Lambda timeout in `template.yaml` (currently 900 seconds)
- Check CloudWatch logs for slow operations

## Known Issues & Gotchas

### S3 Event Trigger Configuration After Deployment
**Issue**: When deploying with SAM, the S3 bucket event notification configuration is NOT automatically created due to circular dependency constraints in CloudFormation. This means uploaded recordings won't trigger the Lambda function automatically.

**Solution**: After deploying the stack, run the configuration script:
```bash
bash configure_s3_trigger.sh
```

This script:
1. Fetches the Lambda function ARN from CloudFormation outputs
2. Adds the necessary S3 invoke permission to the Lambda function
3. Configures the S3 bucket to send `s3:ObjectCreated:*` events for the `recordings/` prefix

**Why this is necessary**: SAM's built-in S3 event source creates a circular dependency between the Lambda function, its IAM role, and the S3 bucket. By configuring notifications post-deployment via AWS CLI, we avoid this issue while maintaining the same functionality.

**Verification**: After running the script, test by uploading a file to S3:
```bash
aws s3 cp test.mp4 s3://meeting-audio-<account-id>/recordings/test-meeting/test.mp4
```
Check CloudWatch logs to verify the Lambda was triggered:
```bash
aws logs tail /aws/lambda/meeting-ingestion-handler --follow
```

### Zoom Meeting IDs with Special Characters
**Issue**: Zoom meeting folder names contain spaces and special characters (e.g., "2026-02-25 20.57.18 Alex Campbell's Zoom Meeting"). These characters get URL-encoded when passed through API Gateway, which can cause issues if not properly decoded.

**Solution**: The system automatically handles URL decoding in the review UI API endpoints. However, be aware that:
- Meeting IDs are used as DynamoDB primary keys - they preserve the original folder name
- API paths must URL-decode the meeting ID before querying DynamoDB
- The dashboard link properly encodes meeting IDs in URLs

**Example**: A meeting with ID `2026-02-25 20.57.18 Alex Campbell's Zoom Meeting` becomes `2026-02-25%2020.57.18%20Alex%20Campbell%27s%20Zoom%20Meeting` in URLs, which is automatically decoded by the API handler.

## Cost Estimate

All services used are within AWS Free Tier:
- Lambda: 1M free requests/month
- DynamoDB: 25GB free storage
- S3: 5GB free storage
- API Gateway: 1M free requests/month
- CloudWatch: 5GB free logs

**Estimated monthly cost: $0** (within free tier)

## Next Steps

1. Test with a real Zoom meeting
2. Review the meeting history dashboard
3. Approve action items and verify Jira tickets are created
4. Customize Bedrock prompt in `src/bedrock_service.py` for your use case
5. Deploy to production when ready

## Support

For issues or questions:
1. Check CloudWatch logs: `aws logs tail /aws/lambda/meeting-ingestion-handler --follow`
2. Review troubleshooting section above
3. Check individual service documentation (Zoom, Slack, Jira)
