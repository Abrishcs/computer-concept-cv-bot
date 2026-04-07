#!/usr/bin/env python3
"""
Ping service to keep Render web service awake
Runs every 14 minutes via Render Cron Job
"""
import os
import requests
from datetime import datetime

SERVICE_URL = os.getenv('SERVICE_URL', 'https://your-app-name.onrender.com')

def ping_service():
    try:
        response = requests.get(SERVICE_URL, timeout=30)
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        if response.status_code == 200:
            print(f"[{timestamp}] ✅ Service is alive! Response: {response.text}")
        else:
            print(f"[{timestamp}] ⚠️ Service responded with status {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] ❌ Failed to ping service: {e}")

if __name__ == "__main__":
    ping_service()
