# Quick Start Guide

## ✅ What's Already Done

1. ✅ AWS infrastructure deployed
2. ✅ Zoom webhook configured with secret token
3. ✅ Lambda function with full processing pipeline
4. ✅ Webhook URL: `https://mmubd07gl3.execute-api.us-east-1.amazonaws.com/Prod/webhook/zoom`

## 🎯 Next Steps to Complete

### 1. Set Up Slack (5 minutes)

```bash
./setup_slack.sh
```

Or manually:
1. Go to https://api.slack.com/apps
2. Click "Create New App" → "From scratch"
3. Name it "Meeting Companion" and select your workspace
4. Go to "Incoming Webhooks" → Toggle "Activate Incoming Webhooks"
5. Click "Add New Webhook to Workspace"
6. Select a channel (e.g., #meetings or #general)
7. Copy the webhook URL (looks like: `https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXX`)
8. Store it in AWS:
   ```bash
   aws secretsmanager create-secret \
       --name meeting-companion/slack \
       --secret-string '{"webhook_url":"YOUR_WEBHOOK_URL"}' \
       --region us-east-1
   ```

### 2. Enable Amazon Bedrock (2 minutes)

1. Go to AWS Console → Amazon Bedrock
2. Click "Model access" in the left sidebar
3. Click "Manage model access"
4. Check "Claude 3 Haiku" by Anthropic
5. Click "Request model access"
6. Wait for approval (usually instant)

### 3. Test with a Real Meeting

1. Schedule a Zoom meeting
2. **Important**: Enable "Record the meeting automatically" in settings
3. Start the meeting and talk for 1-2 minutes
4. End the meeting
5. Wait 5-10 minutes for Zoom to process the recording
6. Check your Slack channel for the summary!

### 4. Monitor Execution

Watch the logs in real-time:
```bash
aws logs tail /aws/lambda/meeting-ingestion-handler --follow
```

Or check CloudWatch Logs in AWS Console.

## 🧪 Test Without a Meeting

Run the test script to verify components:
```bash
pip install -r requirements.txt
python test_pipeline.py
```

This will test:
- ✅ Bedrock AI extraction
- ✅ Slack notification
- ✅ DynamoDB storage

## 🔍 Troubleshooting

### Webhook not triggering
- Check Zoom app "Event Subscriptions" page
- Verify the webhook URL is correct
- Look for validation errors in Zoom dashboard

### Transcription errors
- Ensure recording is in MP4 format
- Check Lambda timeout (currently 15 minutes)
- Verify S3 bucket permissions

### Bedrock access denied
- Go to Bedrock console and request model access
- Wait for approval (usually instant)
- Verify IAM permissions include `bedrock:InvokeModel`

### Slack not working
- Test webhook manually:
  ```bash
  curl -X POST YOUR_WEBHOOK_URL \
    -H 'Content-Type: application/json' \
    -d '{"text":"Test message"}'
  ```
- Verify secret is stored correctly:
  ```bash
  aws secretsmanager get-secret-value \
    --secret-id meeting-companion/slack \
    --region us-east-1
  ```

## 📊 Expected Flow

1. **Meeting ends** → Zoom processes recording (5-10 min)
2. **Webhook fires** → Lambda receives notification
3. **Download** → Audio downloaded to S3 (~30 sec)
4. **Transcribe** → Speech-to-text (~1-2 min per 10 min audio)
5. **AI Analysis** → Bedrock extracts insights (~10-30 sec)
6. **Store** → Results saved to DynamoDB
7. **Notify** → Slack message sent with summary
8. **Cleanup** → Audio file deleted from S3

Total time: ~7-15 minutes after meeting ends

## 🎉 Success Indicators

You'll know it's working when:
- ✅ Slack receives a formatted message with meeting summary
- ✅ DynamoDB table has a new entry
- ✅ CloudWatch logs show successful execution
- ✅ No audio files remain in S3 bucket

## 💡 Tips

- Start with short test meetings (2-3 minutes)
- Use clear speech for better transcription
- Mention action items explicitly ("John will do X by Friday")
- Check CloudWatch Logs for detailed debugging
- Audio is deleted immediately - only summaries are kept

## 🚀 What's Next?

Once the basic pipeline works, you can add:
- Review UI for approving action items before posting
- Jira integration for automatic ticket creation
- Support for Microsoft Teams and Slack Huddles
- Custom prompt engineering for better insights
- Email digests
