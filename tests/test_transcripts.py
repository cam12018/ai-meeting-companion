#!/usr/bin/env python3
"""
Test the pipeline with different meeting transcript complexities
Realistic meeting lengths: 15-30 minutes of actual dialogue
"""
import json
import boto3
import uuid
from datetime import datetime

dynamodb = boto3.client('dynamodb')
transcribe = boto3.client('transcribe')
bedrock = boto3.client('bedrock-runtime')

MEETINGS_TABLE = 'meeting-insights'

# Test transcripts with varying complexity - realistic lengths

CLEAN_TRANSCRIPT = """
Engineering Team Standup - February 18, 2026

John: Alright team, let's get started. We've got a lot on our plate this week. Sarah, can you kick us off with the database migration status?

Sarah: Yeah, absolutely. So we're on track for the PostgreSQL 14 upgrade. I've been working with the infrastructure team and we've finalized the migration scripts. I've tested them in our staging environment and everything looks solid. The performance benchmarks show about a 15% improvement in query times, which is great. We're seeing faster index scans and better query optimization.

John: That's excellent news. What about the blockers you mentioned last week?

Sarah: Right, so the main blocker is we need security team approval for the new IAM policies before we can proceed to production. The policies are more restrictive than our current setup, which is good for security but we need their sign-off. I'm planning to send them the IAM policy document by end of this week, and hopefully we can get approval by next Wednesday. I've already drafted the policies and they look good from a functionality perspective.

John: Okay, so you're taking point on that? Who should we loop in from security?

Sarah: Yes, I'll handle the security coordination. I'll reach out to the security team lead directly. I'll also need to update the deployment runbook with the new PostgreSQL 14 configuration details. I'm thinking I'll add step-by-step instructions for the migration, rollback procedures, and the new connection pooling settings. I want to test that in staging first to make sure the runbook is accurate and that someone else could follow it.

John: Perfect. How long do you think that'll take?

Sarah: The runbook update? Maybe a day or two. I want to be thorough since this is a critical system. I'll also document the new monitoring requirements and any performance tuning we need to do.

John: Sounds good. Mike, let's talk about the API documentation. Where are we on that?

Mike: Good progress overall. I've completed the GraphQL schema documentation - that's all the types, queries, and mutations. I've also documented the authentication flow and error handling. But I still need to review and document all the REST endpoints. We have quite a few of those and some of them are legacy endpoints that we should probably deprecate anyway. I'm thinking we should mark them as deprecated in the docs.

John: How much of the REST stuff is left?

Mike: I'd say about 40% of the total documentation work. The GraphQL stuff is pretty clean and modern, but the REST API has grown organically over the years. I'm thinking we should probably do a pass to clean it up while we're documenting it. Maybe we could deprecate some of the older endpoints and encourage clients to migrate to GraphQL.

John: That makes sense. Can you get that done by next Friday?

Mike: Yeah, I think so. I'm also helping with some other projects but I can prioritize this. I'll probably spend a couple days on it this week and finish it up early next week. I'll make sure to include examples and error codes for each endpoint.

John: Great. Alex, how are the monitoring and alerting improvements going?

Alex: Good. So we need to set up CloudWatch alarms for the authentication service. Right now we don't have good visibility into what's happening with auth failures. I want to create alarms for failed login attempts, token expiration issues, and API latency. I'm planning to set those up in staging first, test them with some synthetic traffic, and then roll them out to production. I'll also set up dashboards so we can see the metrics in real time.

John: That's smart. When do you think you can have that ready?

Alex: I can get the staging setup done this week. I'll run some tests to make sure the alarms are firing correctly and not too noisy. Then we can review them together and push to production next week. I'm thinking we should also set up some automated responses for common issues.

John: Perfect. One thing I want to make sure we're tracking - we need to document all these changes. Sarah, can you make sure the runbook gets updated? And Mike, can you make sure the API docs are comprehensive?

Mike: Absolutely. I'll make sure everything is documented. I'll also add a section about deprecation timelines for the old REST endpoints.

Sarah: Yeah, I'll handle the runbook. I'll also document the IAM policy changes so future team members understand the security model. I'll include the rationale behind each policy decision.

John: Excellent. Let's plan to sync again next Wednesday to check on progress. Sarah, hopefully you'll have security approval by then. Everyone good?

All: Sounds good.

John: Great. Thanks everyone. One last thing - let's make sure we're communicating these changes to the rest of the team. Mike, can you send out a summary of the API changes? Sarah, can you do the same for the database migration?

Sarah: Will do. I'll send out a detailed email with the timeline and any action items for other teams.

Mike: I'll create a summary document and share it in Slack.

John: Perfect. Let's wrap up.
"""

INTERMEDIATE_TRANSCRIPT = """
Product & Engineering Sync - February 18, 2026

John: Alright team, let's catch up. We've got a bunch of stuff going on and I want to make sure we're aligned. So we've been working on the database upgrade, the API stuff, and some infrastructure improvements. Sarah, Mike, you guys were looking at the database thing, right?

Sarah: Yeah, so the database thing... we're trying to upgrade to PostgreSQL 14. It's kind of a big deal because we need to make sure nothing breaks. The scripts look okay but honestly we're not 100% sure about the IAM stuff. Like, we need someone from security to look at it. I think it's important but I'm not sure who to contact or how urgent it is. We might also need to coordinate with the ops team about the migration window.

Mike: Yeah, and also the API docs are kind of a mess right now. We have the GraphQL stuff but the REST endpoints... I don't know, maybe we should just focus on one? Or maybe we should refactor the REST API first? I'm not sure what the priority is. Some of the endpoints are really old and probably don't even work anymore.

John: Hmm, okay. So Sarah, you're handling the database thing? And Mike, you're on the API docs?

Sarah: I guess? I mean, I can talk to security but I'm not sure when they'll get back to us. And the deployment runbook probably needs updating too but I haven't looked at it yet. Also, I think we might need to coordinate with the ops team about the migration window. Do we need downtime? How long will it take? And should we notify customers about the maintenance window?

Mike: The API docs will take a while. Maybe a week or two? I'm also helping with some other stuff so it's hard to say. And like, should we be documenting the old REST endpoints or just the new ones? Or both? And should we include migration guides for clients moving from REST to GraphQL?

Alex: What about the CloudWatch alarms? We talked about that last time. I think we need monitoring for the auth service but I'm not sure what metrics we should be tracking. Should we monitor database performance too?

John: Right, right. Someone should probably set those up. Alex, can you do that?

Alex: I mean, I could but I'm not sure if we should do it in staging first or just go straight to production. And should we set up alerts? Like, who gets notified if something goes wrong? Should we page someone or just send a Slack message?

Sarah: Also, we might need to involve the frontend team because they might be affected by the database changes. Or maybe not? I'm not sure. And the mobile team might need to know about the API changes too.

Mike: And we should probably document this somewhere but I'm not sure where. Like, should it be in the wiki? Or in the runbook? Or in Confluence? Or somewhere else? And should we document the old stuff or just the new stuff? Maybe we should create a migration guide?

John: Let's do staging for the alarms. Okay, I think that covers it. We'll figure out the details later. Let's sync again soon. Sarah, can you reach out to security this week?

Sarah: Should I reach out to security this week?

John: Yeah, that would be good. And maybe coordinate with ops about the migration window. And see if we need to notify customers.

Mike: I'll start working on the API docs. I'll focus on the GraphQL stuff first since that's cleaner. But I might need help figuring out what to deprecate.

Alex: I'll get the CloudWatch alarms set up in staging and we can review them next week. I'll also look into what metrics we should be tracking.

John: Sounds good. Let's wrap up. Oh, and everyone - let's try to document our decisions so we don't have to re-discuss this next week.
"""

HEAVY_NOISE_TRANSCRIPT = """
All-Hands Engineering Meeting - February 18, 2026

John: Okay everyone, let's get started. Sorry I'm late, had another meeting run over. So we need to talk about like three different things today. The database stuff, the API, and I think there's something about monitoring? Let me check my notes... yeah, monitoring. And also maybe something about documentation? I'm not sure.

Sarah: So the database upgrade is happening but there's like three different things we need to do and I'm not sure what the priority is. We need to upgrade PostgreSQL, we need to handle the IAM stuff, and we need to make sure the deployment process is documented. But also, I'm not sure if we should do all of that at once or in phases. And like, what if something goes wrong? Do we have a rollback plan? And should we test it?

Mike: Yeah and also we need to think about the API. Like, should we even be doing GraphQL? REST is simpler. But then we have all these clients that expect GraphQL so... I don't know. And also, some of the REST endpoints are really old and probably should be cleaned up. But that's a separate project maybe? Or should we do it at the same time? I'm confused about what the priority is.

John: Wait, what about the security stuff? I thought we were doing IAM policies?

Sarah: Yeah that too. And the deployment runbook. And we need to test things. But like, do we test in staging or production? And who's responsible for what? Also, I think we might need to coordinate with the ops team but I haven't talked to them yet. And should we notify customers? And what about the frontend team? Will they be affected?

Alex: I think we also need to look at the authentication service. Or was that something else? Like, we need monitoring but I'm not sure what we're monitoring for. Should we monitor database performance? API latency? Both? And who should get alerted if something goes wrong?

Mike: No wait, that's the CloudWatch alarms thing. Or is it? I'm confused. Are we doing alarms for auth or for the database or for the API? Or all of them? And should we set up dashboards too?

John: Okay so let me try to summarize. We have database stuff, API stuff, security stuff, and testing stuff. Sarah, you're on database?

Sarah: I guess? But I also need to coordinate with security and I'm not sure who that is. And someone needs to update the runbook but I don't know if that's me or someone else. Also, the migration might need downtime and I'm not sure how to communicate that to users. And what if the migration takes longer than expected? Do we have a backup plan?

Mike: I can help with the API but I'm also working on other projects so I can't commit to a timeline. Maybe next week? Or the week after? And like, should we be refactoring the REST API or just documenting it? And should we create migration guides for clients? And what about backwards compatibility?

Alex: Should I start the CloudWatch alarms now or wait? And what metrics should we track? Failed logins? API latency? Database performance? All of them? And what should the thresholds be? And who should get notified?

John: Um, let's do it in staging. Or maybe production? I don't know. Let's just figure it out as we go. But also, we should probably have some kind of alert when things go wrong. Like, who gets notified? Should we page someone? Send a Slack message? Both?

Sarah: Also, we might need to involve the frontend team but I haven't talked to them yet. And the mobile team might be affected too. Or maybe not. And what about the data team? Do they need to know about the database changes?

Mike: And we should probably document this somewhere but I'm not sure where. Like, should it be in the wiki? Or in the runbook? Or in Confluence? Or somewhere else? And should we document the old stuff or just the new stuff? And should we create migration guides? And what about API versioning?

Alex: What about the database connection pooling? Do we need to update the application code? And should we update the client libraries too?

Sarah: Oh yeah, that's a good point. I think we might need to update the connection strings. Or maybe not? I'm not sure. And what about the environment variables? Do we need to change those?

John: Okay, so there's a lot here. Let me try to organize this. Sarah, can you figure out what needs to happen with the database and coordinate with security and ops? And maybe the frontend team?

Sarah: I'll try. But I'm not sure when I can get to it. Maybe this week? Or next week? And I'm not sure who to talk to in security. Should I email them? Call them? Slack them?

Mike: I'll work on the API docs. I'll start with GraphQL and see how far I get. But I might need help figuring out what to deprecate and how to handle backwards compatibility.

Alex: I'll set up the CloudWatch alarms in staging. But I might need help figuring out what to monitor and what the thresholds should be. And who should get notified?

John: Okay, let's just keep working on it and sync again soon. Maybe tomorrow? Or next week? I'm not sure what makes sense.

Sarah: Tomorrow works for me but I might be in another meeting. And I'll try to talk to security this week but no promises. And I'm not sure if I should also talk to ops or if that's someone else's job.

Mike: I'll send you a draft of the API docs by... I don't know, Friday? Maybe Monday? And I'll try to include examples but I'm not sure how detailed they should be.

Alex: I'll have the alarms set up by next week. Or maybe this week if I have time. But I might need help testing them and figuring out if the thresholds are right.

John: Sounds good. Let's wrap up. Oh wait, one more thing - we should probably think about the cost implications of all this. Like, is the database upgrade going to cost more? Are we going to need more infrastructure? And what about the monitoring? Will that add to our AWS bill?

Sarah: Good question. I haven't looked at that yet. Should I add that to my list?

John: Yeah, maybe. And also, we should probably document all of this somewhere so we don't forget. And we should probably communicate it to the rest of the company. And maybe get buy-in from leadership?

Mike: Should we also think about the timeline? Like, when do we want to do all of this? This quarter? Next quarter?

Alex: And should we do it all at once or in phases?

John: Good questions. Let's figure that out next time. Alright, I think we're done. Let's sync again soon. Maybe next week? Or the week after?
"""

def store_test_transcript(transcript_text, meeting_name, complexity):
    """Store a test transcript in DynamoDB for processing"""
    import sys
    sys.path.insert(0, '/Users/alexcampbell/Documents/my-aws-project')
    from src.bedrock_service import extract_insights
    from src.storage_service import store_meeting_insights
    
    # Use consistent IDs for testing - same ID every time for the same complexity
    meeting_id = f"test-{complexity}"
    
    print(f"\n{'='*60}")
    print(f"Testing: {meeting_name} ({complexity})")
    print(f"{'='*60}")
    print(f"Meeting ID: {meeting_id}")
    print(f"Transcript length: {len(transcript_text)} characters")
    print(f"Estimated duration: ~{len(transcript_text.split()) // 130} minutes at 130 wpm\n")
    
    # Extract insights
    print("Extracting insights with Bedrock...")
    insights = extract_insights(transcript_text)
    
    print(f"\n📋 Summary:")
    print(f"  {insights.get('summary', 'N/A')}\n")
    
    print(f"✅ Decisions ({len(insights.get('decisions', []))}):")
    for d in insights.get('decisions', []):
        print(f"  • {d}")
    
    print(f"\n🚧 Blockers ({len(insights.get('blockers', []))}):")
    for b in insights.get('blockers', []):
        print(f"  • {b}")
    
    print(f"\n📋 Action Items ({len(insights.get('action_items', []))}):")
    for item in insights.get('action_items', []):
        print(f"  • {item['action']}")
        print(f"    Owner: {item.get('owner', 'Unassigned')} | Priority: {item.get('priority', 'medium')}")
    
    # Store in DynamoDB
    print(f"\nStoring in DynamoDB...")
    metadata = {
        'meeting_id': meeting_id,
        'transcript_length': len(transcript_text),
        'complexity': complexity
    }
    store_meeting_insights(meeting_id, insights, metadata)
    print(f"✅ Stored! Meeting ID: {meeting_id}")
    
    return meeting_id

if __name__ == "__main__":
    print("\n🎙️  Testing Meeting Transcripts with Varying Complexity\n")
    
    # Test all three
    meeting_ids = []
    
    meeting_ids.append(store_test_transcript(
        CLEAN_TRANSCRIPT,
        "Clean Meeting (Structured)",
        "clean"
    ))
    
    meeting_ids.append(store_test_transcript(
        INTERMEDIATE_TRANSCRIPT,
        "Intermediate Noise (Some Ambiguity)",
        "intermediate"
    ))
    
    meeting_ids.append(store_test_transcript(
        HEAVY_NOISE_TRANSCRIPT,
        "Heavy Noise (Chaotic)",
        "heavy"
    ))
    
    print(f"\n{'='*60}")
    print("✅ All test meetings processed!")
    print(f"{'='*60}")
    print("\nMeeting IDs for review:")
    for i, mid in enumerate(meeting_ids, 1):
        print(f"  {i}. {mid}")
    
    print(f"\nView them at:")
    print(f"  https://mmubd07gl3.execute-api.us-east-1.amazonaws.com/Prod/?id=<meeting_id>")
