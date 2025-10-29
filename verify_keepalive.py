#!/usr/bin/env python3
"""
Keep-Alive Setup Verification Script
This script verifies that your LupinBot is properly configured for keep-alive on Replit.
"""

import os
import sys
import requests
from time import sleep

def print_header(text):
    """Print a formatted header."""
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60)

def print_success(text):
    """Print success message."""
    print(f"✅ {text}")

def print_error(text):
    """Print error message."""
    print(f"❌ {text}")

def print_info(text):
    """Print info message."""
    print(f"ℹ️  {text}")

def check_replit_environment():
    """Check if running on Replit."""
    print_header("Checking Replit Environment")
    
    if os.path.exists('/home/runner'):
        print_success("Running on Replit")
        
        repl_slug = os.environ.get('REPL_SLUG', 'unknown')
        repl_owner = os.environ.get('REPL_OWNER', 'unknown')
        port = os.environ.get('PORT', '8080')
        
        print_info(f"Repl Slug: {repl_slug}")
        print_info(f"Repl Owner: {repl_owner}")
        print_info(f"Port: {port}")
        
        if repl_slug != 'unknown' and repl_owner != 'unknown':
            repl_url = f"https://{repl_slug}.{repl_owner}.repl.co"
            print_info(f"Your Repl URL: {repl_url}")
            return True, repl_url
        else:
            print_error("Replit environment variables not properly set")
            return False, None
    else:
        print_error("Not running on Replit")
        print_info("This script is designed for Replit deployments")
        return False, None

def check_web_server(base_url=None):
    """Check if web server is responding."""
    print_header("Checking Web Server")
    
    if not base_url:
        # Try localhost
        base_url = "http://localhost:8080"
        print_info(f"Checking local server: {base_url}")
    
    endpoints = [
        ('/', 'Main Page'),
        ('/health', 'Health Check'),
        ('/ping', 'Ping Endpoint')
    ]
    
    all_working = True
    
    for endpoint, name in endpoints:
        url = f"{base_url}{endpoint}"
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print_success(f"{name} is responding: {url}")
                print_info(f"   Response: {response.text[:100]}...")
            else:
                print_error(f"{name} returned status {response.status_code}")
                all_working = False
        except requests.exceptions.ConnectionError:
            print_error(f"{name} is not accessible: {url}")
            print_info("   Server might not be running yet")
            all_working = False
        except requests.exceptions.Timeout:
            print_error(f"{name} timed out: {url}")
            all_working = False
        except Exception as e:
            print_error(f"{name} error: {str(e)}")
            all_working = False
    
    return all_working

def check_environment_variables():
    """Check required environment variables."""
    print_header("Checking Environment Variables")
    
    required_vars = ['DISCORD_TOKEN']
    optional_vars = ['GEMINI_API_KEY', 'PORT', 'REPL_SLUG', 'REPL_OWNER']
    
    all_present = True
    
    for var in required_vars:
        if os.environ.get(var):
            print_success(f"{var} is set")
        else:
            print_error(f"{var} is missing (REQUIRED)")
            all_present = False
    
    for var in optional_vars:
        if os.environ.get(var):
            print_success(f"{var} is set")
        else:
            print_info(f"{var} is not set (optional)")
    
    return all_present

def print_uptimerobot_instructions(repl_url):
    """Print instructions for setting up UptimeRobot."""
    print_header("UptimeRobot Setup Instructions")
    
    print("\n📋 Follow these steps to keep your bot alive 24/7:\n")
    
    print("1. Go to: https://uptimerobot.com/")
    print("2. Create a free account and verify your email")
    print("3. Click '+ Add New Monitor'")
    print("4. Configure the monitor:\n")
    
    print(f"   Monitor Type: HTTP(s)")
    print(f"   Friendly Name: LupinBot Keep-Alive")
    print(f"   URL: {repl_url}/health")
    print(f"   Monitoring Interval: 5 minutes")
    
    print("\n5. Click 'Create Monitor'")
    print("6. Monitor should show 'Up' status in green")
    print("\n✅ Your bot will now stay online 24/7!\n")
    
    print("Alternative Services:")
    print("  - Freshping: https://www.freshworks.com/website-monitoring/")
    print("  - StatusCake: https://www.statuscake.com/")
    print("  - Uptime.com: https://uptime.com/")

def main():
    """Main verification script."""
    print("\n🦊 LupinBot Keep-Alive Setup Verification")
    print("="*60)
    
    # Check if running on Replit
    is_replit, repl_url = check_replit_environment()
    
    # Check environment variables
    env_ok = check_environment_variables()
    
    if not env_ok:
        print("\n⚠️  Please set all required environment variables before proceeding.")
        print("   Add DISCORD_TOKEN to Replit Secrets or .env file")
        sys.exit(1)
    
    # Check web server
    if is_replit and repl_url:
        print_info("\nWaiting for web server to start...")
        sleep(3)
        server_ok = check_web_server(repl_url)
    else:
        server_ok = check_web_server()
    
    # Final status
    print_header("Verification Summary")
    
    if is_replit and env_ok and server_ok:
        print_success("All systems operational!")
        print_success("Your bot is ready for 24/7 operation")
        print("\n📋 Next Step: Setup external monitoring")
        if repl_url:
            print_uptimerobot_instructions(repl_url)
    elif env_ok and server_ok:
        print_success("Bot is running correctly")
        print_info("Not on Replit - keep-alive not needed for local development")
    else:
        print_error("Some checks failed")
        print_info("Please fix the issues above and try again")
        print_info("\nCommon fixes:")
        print("  1. Make sure the bot is running (python main.py)")
        print("  2. Check that DISCORD_TOKEN is set")
        print("  3. Wait 30 seconds for server to start, then run again")
    
    print("\n" + "="*60)
    print("📚 For more help, see: KEEPALIVE_SETUP.md")
    print("="*60 + "\n")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Verification cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
