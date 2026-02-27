# Technology Stack & Build System

## Language & Runtime

- **Primary Language**: Python 3.12
- **Runtime Environment**: AWS Lambda
- **Infrastructure as Code**: AWS SAM (Serverless Application Model)

## Core Dependencies

```
boto3==1.34.34          # AWS SDK for Python
requests==2.31.0        # HTTP library for API calls
python-dotenv==1.0.0    # Environment variable management
```

## AWS Services Used

- **Lambda**: Serverless compute for ingestion and review handlers
- **API Gateway**: HTTP endpoint for webhooks and review UI
- **S3**: Temporary audio file storage (auto-deleted after 1 day)
- **DynamoDB**: Meeting insights and metadata storage
- **Amazon Transcribe**: Speech-to-text transcription
- **Amazon Bedrock**: AI model invocation (Claude 3 Haiku)
- **Secrets Manager**: Secure credential storage (Zoom, Slack, Jira)
- **CloudWatch**: Logging and monitoring

## Frontend

- **Review UI**: HTML/JavaScript (served by Lambda)
- **Dashboard**: HTML interface for meeting history

## Build & Deployment

### Prerequisites

- AWS Account with credentials configured
- AWS SAM CLI
- Python 3.12+
- Zoom Developer Account
- Slack Workspace

### Build Commands

```bash
# Build the SAM application
sam build

# Deploy with guided setup (interactive)
sam deploy --guided

# Deploy with existing configuration
sam deploy

# View logs
aws logs tail /aws/lambda/meeting-ingestion-handler --follow
```

### Project Structure

```
.
├── src/                          # Lambda function code
│   ├── ingestion_handler.py      # Main webhook handler
│   ├── transcription_service.py  # Amazon Transcribe integration
│   ├── bedrock_service.py        # AI insight extraction
│   ├── slack_service.py          # Slack notifications
│   ├── jira_service.py           # Jira ticket creation
│   ├── storage_service.py        # DynamoDB operations
│   └── requirements.txt          # Lambda dependencies
├── review-ui/                    # Review UI Lambda function
│   ├── app.py                    # Flask/Lambda handler
│   ├── index.html                # Review interface
│   ├── dashboard.html            # Meeting history
│   ├── jira_service.py           # Jira integration
│   ├── slack_service.py          # Slack integration
│   └── requirements.txt          # UI dependencies
├── template.yaml                 # SAM CloudFormation template
├── requirements.txt              # Root dependencies
├── deploy.sh                     # Deployment script
└── tests/                        # Test files
```

## Testing

```bash
# Run test suite
python -m pytest tests/

# Run specific test
python -m pytest tests/test_pipeline.py

# Test individual components
python tests/test_jira.py
python tests/test_slack_notification.py
python tests/test_transcripts.py
```

## Environment Configuration

- **Local Development**: Use `.env` file (see `.env.example`)
- **AWS Deployment**: Use AWS Secrets Manager for credentials
- **Configuration**: `samconfig.toml` stores deployment settings

## Code Style & Conventions

- **Python Version**: 3.12
- **Naming**: snake_case for functions and variables
- **Error Handling**: Try-catch with CloudWatch logging
- **AWS SDK**: Use boto3 client pattern
- **Secrets**: Always retrieve from Secrets Manager, never hardcode

## Monitoring & Logging

- **CloudWatch Logs**: All Lambda functions log to CloudWatch
- **Log Groups**:
  - `/aws/lambda/meeting-ingestion-handler`
  - `/aws/lambda/meeting-review-ui`
- **Metrics**: Lambda duration, DynamoDB capacity, S3 operations

## Cost Optimization

- Designed to stay within AWS Free Tier
- Lambda: 1M requests/month free
- Transcribe: 60 minutes/month free
- Bedrock: Pay-per-use (Claude 3 Haiku is cost-effective)
- S3: 5GB storage free (audio auto-deleted)
- DynamoDB: 25GB storage free
