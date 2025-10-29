"""Simple script to start the LupinBot Dashboard"""
import subprocess
import sys
import os

def start_dashboard():
    """Start the dashboard with proper configuration."""
    port = int(os.environ.get('DASHBOARD_PORT', os.environ.get('PORT', '5000')))
    
    print("🚀 Starting LupinBot Dashboard...")
    print(f"📊 Dashboard will be available at: http://localhost:{port}")
    print("⚠️  Make sure your Discord bot is running!")
    print("")
    
    # Check if database exists
    if not os.path.exists('database.db'):
        print("❌ database.db not found!")
        print("💡 Make sure you've run the bot at least once to create the database.")
        print("   Run: python main.py")
        return
    
    # Check if Flask is installed
    try:
        import flask
    except ImportError:
        print("❌ Flask not installed!")
        print("💡 Installing Flask...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "flask"])
        print("✅ Flask installed!")
    
    # Start the dashboard
    try:
        from dashboard import run_dashboard
        print("✅ Starting dashboard server...")
        run_dashboard(host='0.0.0.0', port=5000, debug=True)
    except KeyboardInterrupt:
        print("\n👋 Dashboard stopped.")
    except Exception as e:
        print(f"❌ Error: {e}")
        print("💡 Make sure you're in the project directory.")

if __name__ == '__main__':
    start_dashboard()

