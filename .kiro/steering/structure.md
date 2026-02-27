# Project Structure & Organization

## Directory Layout

```
ai-meeting-companion/
├── .aws-sam/                     # SAM build artifacts (generated)
│   ├── build/                    # Compiled Lambda functions
│   └── build.toml                # Build configuration
├── .kiro/                        # Kiro IDE configuration
│   └── steering/                 # Steering documents (this folder)
├── .vscode/                      # VS Code settings
├── docs/                         # Documentation
│   ├── ARCHITECTURE.md           # System design and data flow
│   ├── QUICK_START.md            # Getting started guide
│   ├── SETUP.md                  # Detailed setup instructions
│   ├── ARTICLE_TEMPLATE.md       # Template for documentation
│   └── ingest-video-epics-README.md
├── src/                          # Main Lambda function code
│   ├── __init__.py
│   ├── ingestion_handler.py      # Webhook handler (entry point)
│   ├── transcription_service.py  # Amazon Transcribe integration
│   ├── bedrock_service.py        # AI insight extraction
│   ├── slack_service.py          # Slack notification service
│   ├── jira_service.py           # Jira ticket creation
│   ├── storage_service.py        # DynamoDB operations
│   └── requirements.txt          # Lambda dependencies
├── review-ui/                    # Review UI Lambda function
│   ├── app.py                    # Flask/Lambda handler for review UI
│   ├── index.html                # Review interface (pending meetings)
│   ├── dashboard.html            # Meeting history dashboard
│   ├── jira_service.py           # Jira integration for UI
│   ├── slack_service.py          # Slack integration for UI
│   └── requirements.txt          # UI dependencies
├── tests/                        # Test suite
│   ├── test_pipeline.py          # End-to-end pipeline tests
│   ├── test_jira.py              # Jira integration tests
│   ├── test_jira_integration.py  # Jira API tests
│   ├── test_slack_notification.py # Slack notification tests
│   ├── test_transcripts.py       # Transcription tests
│   ├── test_upload.py            # S3 upload tests
│   ├── test_webhook.py           # Webhook verification tests
│   ├── check_jira_projects.py    # Jira project checker
│   ├── check_status.sh           # Status check script
│   ├── diagnose_zoom.sh          # Zoom diagnostic script
│   ├── upload_recording.py       # Manual recording upload
│   └── view_meetings.sh          # View stored meetings
├── template.yaml                 # SAM CloudFormation template
├── samconfig.toml                # SAM deployment configuration
├── deploy.sh                     # Deployment automation script
├── auto_upload_recording.py      # Local recording auto-uploader
├── requirements.txt              # Root Python dependencies
├── .env.example                  # Environment variable template
├── .gitignore                    # Git ignore rules
├── .kiroignore                   # Kiro ignore rules
└── README.md                     # Project overview
```

## Module Organization

### Core Processing Pipeline (`src/`)

**ingestion_handler.py** (Entry Point)
- Handles Zoom webhooks and S3 events
- Orchestrates the processing pipeline
- Verifies webhook signatures
- Coordinates between services

**transcription_service.py**
- Manages Amazon Transcribe jobs
- Polls for transcription completion
- Fetches and returns transcript text

**bedrock_service.py**
- Calls Amazon Bedrock API
- Extracts insights from transcripts
- Formats AI responses into structured data

**slack_service.py**
- Sends Slack notifications
- Formats messages with meeting summaries
- Handles review ready and approval notifications

**jira_service.py**
- Creates Jira tickets from action items
- Maps priorities and due dates
- Assigns tickets to team members

**storage_service.py**
- Stores meeting insights in DynamoDB
- Manages S3 audio file lifecycle
- Retrieves stored meeting data

### Review UI (`review-ui/`)

**app.py**
- Lambda handler for review UI endpoints
- Serves HTML interface
- Handles approval requests
- Manages meeting status updates

**index.html**
- Review interface for pending meetings
- Displays summaries, decisions, blockers
- Action item editing and selection
- Approval submission

**dashboard.html**
- Meeting history view
- Status tracking (pending/approved)
- Search and filtering

### Testing (`tests/`)

- **Unit Tests**: Individual service tests
- **Integration Tests**: End-to-end pipeline tests
- **Diagnostic Scripts**: Troubleshooting and validation

## Data Flow Architecture

```
Webhook/Upload
    ↓
ingestion_handler.py (orchestrator)
    ├→ transcription_service.py
    ├→ bedrock_service.py
    ├→ storage_service.py
    ├→ slack_service.py
    └→ jira_service.py
```

## Configuration Files

- **template.yaml**: SAM infrastructure definition
- **samconfig.toml**: Deployment parameters and stack settings
- **.env.example**: Local development environment variables
- **requirements.txt**: Python dependencies (root level)
- **src/requirements.txt**: Lambda function dependencies
- **review-ui/requirements.txt**: Review UI dependencies

## Key Conventions

### File Naming
- Python modules: `snake_case.py`
- Services: `{service_name}_service.py`
- Tests: `test_{module_name}.py`
- HTML files: `lowercase.html`

### Function Organization
- Service functions: Grouped by responsibility
- Error handling: Consistent logging to CloudWatch
- AWS SDK: Use boto3 clients
- Secrets: Retrieved from Secrets Manager

### Data Storage
- **DynamoDB**: Meeting insights with meeting_id as primary key
- **S3**: Temporary audio files (auto-deleted after 1 day)
- **Secrets Manager**: Zoom, Slack, Jira credentials

## Development Workflow

1. **Local Development**: Use `.env` file and local testing scripts
2. **Testing**: Run tests in `tests/` directory
3. **Build**: `sam build` to compile Lambda functions
4. **Deploy**: `sam deploy` to AWS
5. **Monitoring**: Check CloudWatch logs for execution details

## Important Notes

- All AWS credentials should be stored in Secrets Manager, never in code
- Lambda functions have 15-minute timeout for transcription
- Audio files are automatically deleted after 1 day (S3 lifecycle)
- DynamoDB uses on-demand billing (no capacity planning needed)
- All services use IAM roles with least-privilege permissions
