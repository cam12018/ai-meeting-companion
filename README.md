# AI Meeting Companion

AI-powered meeting companion that transforms workplace conversations into actionable insights using AWS AI services.

## 🎯 Features

- 🎙️ Automatic ingestion from Zoom meeting recordings
- 📝 Speech-to-text transcription via Amazon Transcribe
- 🤖 AI-powered insight extraction via Amazon Bedrock (Claude 3 Haiku)
- 📊 Structured summaries with decisions, blockers, and action items
- 🔔 Real-time Slack notifications
- 📋 Automatic Jira ticket creation
- 🔒 Privacy-first: Audio deleted immediately after processing
- 💰 Cost-optimized for AWS Free Tier

## 🚀 Quick Start

### Local Testing (Free)
```bash
# 1. Deploy infrastructure
sam build && sam deploy --guided

# 2. Configure S3 trigger
bash configure_s3_trigger.sh

# 3. Start auto-uploader
python3 auto_upload_recording.py &

# 4. Record a Zoom meeting in ~/Documents/Zoom/
# 5. Watch it process automatically!
```

### Production (Zoom Cloud Recording)
See [Setup Guide](docs/SETUP.md) for full Zoom webhook configuration.

## 📚 Documentation

- [Setup Guide](docs/SETUP.md) - Complete setup instructions
- [Architecture](docs/ARCHITECTURE.md) - System design and data flow
- [Quick Start](docs/QUICK_START.md) - Get started quickly

## 🏗️ Architecture

```
Zoom Recording / S3 Upload
        ↓
Lambda (Ingestion Handler)
        ↓
Amazon Transcribe (Speech-to-Text)
        ↓
Amazon Bedrock (AI Insights)
        ↓
DynamoDB (Store Results)
        ↓
Slack Notification → Review UI
        ↓
Approval → Jira Tickets
```

**Key Components:**
- **Ingestion Handler**: Orchestrates the entire pipeline
- **Review UI**: Web interface to review and approve action items
- **Slack Integration**: Real-time notifications with review links
- **Jira Integration**: Automatic ticket creation from approved items

## 🚀 Setup

### Prerequisites

- AWS Account with credentials configured
- Zoom Developer Account (for production)
- Slack Workspace (for notifications)
- Python 3.12+
- AWS SAM CLI

### 1. Deploy Infrastructure

```bash
sam build
sam deploy --guided
```

### 2. Configure S3 Trigger

```bash
bash configure_s3_trigger.sh
```

This enables automatic Lambda invocation when recordings are uploaded to S3.

### 3. Configure Slack (Optional)

```bash
aws secretsmanager create-secret \
    --name meeting-companion/slack \
    --secret-string '{"webhook_url":"YOUR_SLACK_WEBHOOK_URL"}'
```

### 4. Test Locally

```bash
# Start auto-uploader
python3 auto_upload_recording.py &

# Record a Zoom meeting in ~/Documents/Zoom/
# The recording will auto-upload and process automatically
```

For production Zoom webhook setup, see [Setup Guide](docs/SETUP.md).

## 📊 What Gets Extracted

From each meeting, the AI extracts:

- **Summary**: Concise 2-3 sentence overview
- **Decisions**: Key decisions made during the meeting
- **Blockers**: Issues or obstacles mentioned
- **Action Items**: Tasks with owners and priority levels

## 💰 Cost Optimization

Configured to stay within AWS Free Tier:

- **Lambda**: 1M requests/month free
- **Amazon Transcribe**: 60 minutes/month free
- **Amazon Bedrock**: Pay-per-use (Claude 3 Haiku is cost-effective)
- **S3**: 5GB storage free (audio deleted immediately)
- **DynamoDB**: 25GB storage free
- **API Gateway**: 1M requests/month free

## 🔒 Privacy & Security

- Audio files deleted immediately after transcription
- Only AI-generated summaries stored
- Webhook signature verification
- Secrets stored in AWS Secrets Manager
- IAM least-privilege permissions

## 🧪 Testing

### Local Testing
```bash
# Generate test meetings with AI-extracted insights
python3 generate_test_meetings.py

# View dashboard
https://YOUR-API-ID.execute-api.us-east-1.amazonaws.com/Prod/dashboard
```

### Live Recording
1. Start auto-uploader: `python3 auto_upload_recording.py &`
2. Record a Zoom meeting in `~/Documents/Zoom/`
3. Recording auto-uploads and processes automatically
4. Check Slack for notification with review link
5. Review and approve action items in the UI
6. Approved items create Jira tickets automatically

Check CloudWatch logs for detailed execution:
```bash
aws logs tail /aws/lambda/meeting-ingestion-handler --follow
```

## 📁 Project Structure

```
.
├── src/
│   ├── ingestion_handler.py      # Main Lambda handler
│   ├── transcription_service.py  # Amazon Transcribe integration
│   ├── bedrock_service.py        # Amazon Bedrock AI
│   ├── slack_service.py          # Slack notifications
│   └── storage_service.py        # DynamoDB storage
├── template.yaml                 # SAM/CloudFormation template
├── requirements.txt              # Python dependencies
└── test_pipeline.py             # Test script

## 🔧 Troubleshooting

**Recordings not uploading:**
- Ensure `auto_upload_recording.py` is running
- Check `~/Documents/Zoom` folder exists
- Verify AWS credentials are configured

**Slack notifications not sending:**
- Verify webhook URL in Secrets Manager
- Check CloudWatch logs for errors

**Jira tickets not creating:**
- Verify Jira credentials in Secrets Manager
- Ensure project key is correct

See [Setup Guide](docs/SETUP.md) for detailed troubleshooting.

## 📝 Next Steps

- Review the [Architecture](docs/ARCHITECTURE.md) to understand the system
- Check [Setup Guide](docs/SETUP.md) for production deployment
- Customize the Bedrock prompt in `src/bedrock_service.py` for your use case
- Deploy to production when ready

## 📝 License

MIT
