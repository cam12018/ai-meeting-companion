#!/usr/bin/env python3
"""
Check available Jira projects
"""
import sys
import os
import json
import requests
from base64 import b64encode

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from jira_service import get_jira_config

if __name__ == "__main__":
    print("🔍 Checking Jira Projects")
    print("=" * 50)
    print()
    
    try:
        config = get_jira_config()
        
        if not config:
            print("❌ No Jira configuration found")
            sys.exit(1)
        
        print(f"Jira URL: {config['url']}")
        print(f"Email: {config['email']}")
        print(f"Configured Project Key: {config['project_key']}")
        print()
        
        # Create auth header
        auth_string = f"{config['email']}:{config['api_token']}"
        auth_header = b64encode(auth_string.encode()).decode()
        
        headers = {
            "Authorization": f"Basic {auth_header}",
            "Content-Type": "application/json"
        }
        
        # Get all projects
        print("Fetching available projects...")
        url = f"{config['url']}/rest/api/3/project"
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        projects = response.json()
        
        print(f"\n✅ Found {len(projects)} project(s):")
        print()
        
        for project in projects:
            print(f"  • Key: {project['key']}")
            print(f"    Name: {project['name']}")
            print(f"    ID: {project['id']}")
            print()
        
        # Check if configured project exists
        project_keys = [p['key'] for p in projects]
        if config['project_key'] in project_keys:
            print(f"✅ Configured project '{config['project_key']}' exists!")
        else:
            print(f"⚠️  Configured project '{config['project_key']}' not found")
            print(f"   Available keys: {', '.join(project_keys)}")
        
    except requests.exceptions.HTTPError as e:
        print(f"❌ HTTP error: {e.response.status_code}")
        print(f"Response: {e.response.text}")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
