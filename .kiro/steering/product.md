# AI Meeting Companion - Product Overview

## What is it?

AI Meeting Companion is a serverless application that automatically transforms Zoom meeting recordings into actionable insights. It uses AWS AI services to transcribe meetings and extract structured summaries, decisions, blockers, and action items.

## Core Value Proposition

- **Automatic Processing**: Triggered by Zoom webhook when recording completes
- **AI-Powered Insights**: Uses Amazon Bedrock (Claude 3 Haiku) to extract meaningful information
- **Slack Integration**: Sends notifications with review links for team collaboration
- **Jira Integration**: Automatically creates tickets for approved action items
- **Privacy-First**: Audio files deleted immediately after transcription
- **Cost-Optimized**: Designed to stay within AWS Free Tier

## Key Features

1. **Meeting Ingestion**: Accepts recordings from Zoom cloud recording or local uploads
2. **Transcription**: Converts speech to text using Amazon Transcribe
3. **Insight Extraction**: AI identifies decisions, blockers, and action items
4. **Review UI**: Web interface for reviewing and editing extracted insights
5. **Approval Workflow**: Users approve action items before Jira ticket creation
6. **Notifications**: Slack messages at each stage (ready for review, approved)

## Deployment Models

- **Cloud**: Fully automatic via Zoom webhook (production)
- **Local**: Semi-automatic via upload script (development/testing)

## Data Extracted Per Meeting

- **Summary**: 2-3 sentence overview
- **Decisions**: Key technical decisions made
- **Blockers**: Issues preventing progress
- **Action Items**: Specific tasks with owner, priority, and due date

## Target Users

- Engineering teams using Zoom for meetings
- Teams that want to reduce manual note-taking
- Organizations using Slack and Jira for workflow management
