# System Architecture - AI Meeting Companion

## Overview

The AI Meeting Companion is a serverless, event-driven system that transforms meeting recordings into actionable insights. It supports both cloud-based (Zoom webhook) and local testing (manual upload) workflows.

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     CLOUD SETUP (Production)                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Zoom Meeting → Zoom Webhook → API Gateway → Lambda (Ingestion) │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    LOCAL SETUP (Development)                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Zoom Recording → Auto-Uploader Script → S3 → Lambda (Ingestion)│
│                                                                   │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    PROCESSING PIPELINE (Same for Both)          │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Lambda Ingestion Handler                                        │
│  ├─ Download recording from S3                                  │
│  ├─ Transcribe with Amazon Transcribe                           │
│  ├─ Extract insights with Amazon Bedrock                        │
│  ├─ Store in DynamoDB                                           │
│  ├─ Send Slack notification with review link                   │
│  └─ Delete audio file (privacy)                                 │
│                                                                   │
│  ↓                                                                │
│                                                                   │
│  Review UI (Lambda + HTML)                                       │
│  ├─ Display meeting summary, decisions, blockers                │
│  ├─ Show action items with owner/priority/due date              │
│  ├─ Allow editing and selection                                 │
│  └─ Prevent re-approval (status check)                          │
│                                                                   │
│  ↓                                                                │
│                                                                   │
│  Approval Handler (Lambda)                                       │
│  ├─ Update meeting status to "approved"                         │
│  ├─ Create Jira tickets for selected items                      │
│  ├─ Send final Slack notification                               │
│  └─ Return success response                                      │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    DATA STORAGE & INTEGRATIONS                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  DynamoDB: Meeting insights, summaries, action items             │
│  S3: Temporary audio files (auto-deleted after 1 day)            │
│  Secrets Manager: Zoom, Slack, Jira credentials                 │
│  CloudWatch: Logs and monitoring                                 │
│                                                                   │
│  External APIs:                                                  │
│  ├─ Zoom: Recording download                                    │
│  ├─ Slack: Notifications and review links                       │
│  └─ Jira: Ticket creation                                       │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Ingestion Handler (`src/ingestion_handler.py`)

**Triggered by:**
- Cloud: Zoom webhook when recording is ready
- Local: S3 event when file is uploaded

**Responsibilities:**
- Verify webhook signature (Zoom only)
- Download recording from Zoom or S3
- Upload to S3 for processing
- Initiate transcription job
- Wait for transcription to complete
- Extract insights using Bedrock
- Store results in DynamoDB
- Send Slack notification with review link
- Delete audio file (privacy)

**Error Handling:**
- Retry on transient failures
- Log all errors to CloudWatch
- Notify on critical failures

### 2. Transcription Service (`src/transcription_service.py`)

**Uses:** Amazon Transcribe

**Process:**
- Start transcription job from S3 audio
- Poll for job completion
- Extract transcript text
- Return full transcript

**Timeout:** 15 minutes (configurable)

### 3. Bedrock Service (`src/bedrock_service.py`)

**Uses:** Amazon Bedrock (Claude 3 Haiku)

**Extracts:**
- **Summary**: 2-3 sentence overview of meeting
- **Decisions**: Key technical decisions made
- **Blockers**: Issues preventing progress
- **Action Items**: Specific, technical tasks with:
  - Clear description
  - Assigned owner (extracted from transcript)
  - Priority (high/medium/low)

**Prompt Engineering:**
- Emphasizes specific, technical language
- Includes examples of good vs bad action items
- Handles messy, ambiguous transcripts

### 4. Storage Service (`src/storage_service.py`)

**Uses:** DynamoDB

**Stores:**
```json
{
  "meeting_id": "unique-id",
  "timestamp": "2026-02-18T10:30:00Z",
  "status": "pending_review" | "approved",
  "summary": "Meeting summary text",
  "decisions": ["decision 1", "decision 2"],
  "blockers": ["blocker 1", "blocker 2"],
  "action_items": [
    {
      "action": "Specific task description",
      "owner": "Person Name",
      "priority": "high|medium|low",
      "due": "This week|Next week|End of month|No deadline"
    }
  ]
}
```

### 5. Review UI (`review-ui/index.html` + `review-ui/app.py`)

**Features:**
- Display meeting summary, decisions, blockers
- Show action items in 2-column grid
- Allow editing action item descriptions
- Select/deselect individual items
- Choose owner and due date for each item
- Prevent re-approval (status check)
- Show "already approved" message if applicable

**Routes:**
- `GET /` - Review UI (pending meetings list or specific meeting)
- `GET /dashboard` - Meeting history dashboard
- `GET /api/meetings` - List pending meetings
- `GET /api/meetings/{id}` - Get meeting details
- `POST /api/meetings/{id}/approve` - Approve and create tickets

### 6. Slack Service (`src/slack_service.py`)

**Two notification types:**

**1. Review Ready (before approval)**
```
🎙️ Meeting Summary Ready for Review
[Summary text]
✅ Decisions Made: [list]
🚧 Blockers: [list]
📋 Action Items: [list with owners]
[Review & Approve Button] → Links to review UI
```

**2. Approved (after approval)**
```
🎙️ Meeting Summary Approved
[Summary text]
✅ Decisions Made: [list]
🚧 Blockers: [list]
📋 Action Items: [list with owners]
✅ Approved! Action items have been published to Jira.
```

### 7. Jira Service (`src/jira_service.py`)

**Creates tickets for approved action items:**
- Title: Action item description
- Description: Full details with owner and priority
- Assignee: Person from action item
- Priority: Mapped from high/medium/low
- Due Date: Calculated from "This week", "Next week", etc.
- Project: Configured project key

## Data Flow

### Cloud Setup (Automatic)

```
1. Zoom Meeting Ends
   ↓
2. Zoom Webhook Notification
   ↓
3. API Gateway receives webhook
   ↓
4. Lambda Ingestion Handler triggered
   ↓
5. Download recording from Zoom
   ↓
6. Upload to S3
   ↓
7. Transcribe with Amazon Transcribe
   ↓
8. Extract insights with Bedrock
   ↓
9. Store in DynamoDB
   ↓
10. Send Slack notification with review link
   ↓
11. User clicks review link
   ↓
12. Review UI loads from Lambda
   ↓
13. User approves action items
   ↓
14. Lambda creates Jira tickets
   ↓
15. Send final Slack notification
```

### Local Setup (Semi-Automatic)

```
1. Zoom Meeting Ends
   ↓
2. Recording saved to ~/Documents/Zoom
   ↓
3. Auto-uploader script detects new recording
   ↓
4. Upload to S3
   ↓
5-15. [Same as cloud setup from step 7 onwards]
```

## Key Differences: Cloud vs Local

| Aspect | Cloud | Local |
|--------|-------|-------|
| **Trigger** | Zoom webhook | Manual upload script |
| **Automation** | Fully automatic | Semi-automatic (script must run) |
| **Setup** | Configure webhook in Zoom | Run `auto_upload_recording.py` |
| **Processing** | Same Lambda pipeline | Same Lambda pipeline |
| **Cost** | Free tier eligible | Free tier eligible |
| **Latency** | Immediate | Depends on script polling |

## Security & Privacy

- **Audio Deletion**: Recordings deleted from S3 after transcription (1-day lifecycle)
- **Credentials**: All secrets stored in AWS Secrets Manager
- **Encryption**: DynamoDB encryption at rest
- **Access Control**: Lambda execution roles with minimal permissions
- **Logs**: CloudWatch logs with sensitive data redaction

## Scalability

- **Serverless**: Auto-scales with demand
- **No servers to manage**: AWS handles infrastructure
- **Cost**: Pay only for what you use
- **Free tier**: Handles 1M+ requests/month

## Monitoring

**CloudWatch Logs:**
- `/aws/lambda/meeting-ingestion-handler` - Ingestion pipeline
- `/aws/lambda/meeting-review-ui` - Review UI and approvals

**Metrics to track:**
- Lambda invocations and duration
- DynamoDB read/write capacity
- S3 upload/download operations
- Transcription job duration
- Bedrock API calls

## Future Enhancements

- Microsoft Teams integration
- Slack Huddles integration
- Email notifications
- Custom Bedrock prompts per team
- Meeting analytics dashboard
- Recurring meeting templates
- Integration with other project management tools
