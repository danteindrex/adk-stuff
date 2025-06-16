#!/usr/bin/env python3
"""
WhatsApp Clone Launcher
Launches both the main AI backend and the WhatsApp clone interface
"""

import os
import sys
import subprocess
import time
import signal
import threading
from pathlib import Path

def print_banner():
    """Print startup banner"""
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║                    WhatsApp Clone Launcher                   ║
    ║              Uganda E-Gov AI Assistant Demo                  ║
    ╠══════════════════════════════════════════════════════════════╣
    ║  🤖 AI Backend: http://localhost:8080                       ║
    ║  💬 WhatsApp Clone: http://localhost:8081                   ║
    ║  📱 Demo Mode Available (No Google OAuth required)          ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)

def check_requirements():
    """Check if required files exist"""
    required_files = [
        "main.py",
        "whatsapp_clone/index.html",
        "whatsapp_clone/styles.css",
        "whatsapp_clone/script.js",
        "whatsapp_clone_server.py"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print("❌ Missing required files:")
        for file in missing_files:
            print(f"   - {file}")
        print("\nPlease ensure all WhatsApp clone files are present.")
        return False
    
    print("✅ All required files found")
    return True

def check_environment():
    """Check environment variables"""
    print("\n🔍 Checking environment configuration...")
    
    # Check for .env file
    if not Path(".env").exists():
        print("⚠️  No .env file found. Creating example...")
        create_env_example()
    
    # Check critical variables
    required_vars = ["TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "TWILIO_WHATSAPP_NUMBER"]
    optional_vars = ["GOOGLE_CLIENT_ID"]
    
    missing_required = []
    for var in required_vars:
        if not os.getenv(var):
            missing_required.append(var)
    
    if missing_required:
        print("❌ Missing required environment variables:")
        for var in missing_required:
            print(f"   - {var}")
        print("\nPlease configure your .env file with Twilio credentials.")
        return False
    
    print("✅ Required environment variables found")
    
    # Check optional variables
    for var in optional_vars:
        if os.getenv(var):
            print(f"✅ {var} configured")
        else:
            print(f"⚠️  {var} not configured (demo mode will be used)")
    
    return True

def create_env_example():
    """Create example .env file"""
    env_content = """# Twilio Configuration (Required)
TWILIO_ACCOUNT_SID=your_twilio_account_sid_here
TWILIO_AUTH_TOKEN=your_twilio_auth_token_here
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886

# Google OAuth (Optional - demo mode available)
GOOGLE_CLIENT_ID=your_google_client_id_here

# Other configurations
ENVIRONMENT=development
LOG_LEVEL=INFO
PORT_NO=8080
"""
    
    with open(".env.example", "w") as f:
        f.write(env_content)
    
    print("📝 Created .env.example file")
    print("   Please copy it to .env and configure your credentials")

def start_main_backend():
    """Start the main AI backend"""
    print("\n🚀 Starting main AI backend...")
    try:
        process = subprocess.Popen([
            sys.executable, "main.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # Give it time to start
        time.sleep(3)
        
        if process.poll() is None:
            print("✅ Main AI backend started on http://localhost:8080")
            return process
        else:
            stdout, stderr = process.communicate()
            print(f"❌ Failed to start main backend:")
            print(f"   stdout: {stdout}")
            print(f"   stderr: {stderr}")
            return None
            
    except Exception as e:
        print(f"❌ Error starting main backend: {e}")
        return None

def start_whatsapp_clone():
    """Start the WhatsApp clone server"""
    print("\n💬 Starting WhatsApp clone server...")
    try:
        process = subprocess.Popen([
            sys.executable, "whatsapp_clone_server.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # Give it time to start
        time.sleep(2)
        
        if process.poll() is None:
            print("✅ WhatsApp clone started on http://localhost:8081")
            return process
        else:
            stdout, stderr = process.communicate()
            print(f"❌ Failed to start WhatsApp clone:")
            print(f"   stdout: {stdout}")
            print(f"   stderr: {stderr}")
            return None
            
    except Exception as e:
        print(f"❌ Error starting WhatsApp clone: {e}")
        return None

def monitor_processes(processes):
    """Monitor running processes"""
    print("\n👀 Monitoring processes... (Press Ctrl+C to stop)")
    
    try:
        while True:
            time.sleep(5)
            
            # Check if processes are still running
            for name, process in processes.items():
                if process and process.poll() is not None:
                    print(f"⚠️  {name} process stopped unexpectedly")
                    
            # Check if all processes are dead
            if all(p is None or p.poll() is not None for p in processes.values()):
                print("❌ All processes stopped")
                break
                
    except KeyboardInterrupt:
        print("\n��� Shutdown requested...")
        
        # Terminate all processes
        for name, process in processes.items():
            if process and process.poll() is None:
                print(f"   Stopping {name}...")
                process.terminate()
                
                # Wait for graceful shutdown
                try:
                    process.wait(timeout=5)
                    print(f"   ✅ {name} stopped gracefully")
                except subprocess.TimeoutExpired:
                    print(f"   🔨 Force killing {name}...")
                    process.kill()
                    process.wait()

def open_browser():
    """Open browser windows"""
    import webbrowser
    
    print("\n🌐 Opening browser windows...")
    
    # Wait a moment for servers to be ready
    time.sleep(2)
    
    try:
        # Open WhatsApp clone
        webbrowser.open("http://localhost:8081")
        print("   ✅ Opened WhatsApp clone")
        
        # Optionally open main backend docs
        time.sleep(1)
        webbrowser.open("http://localhost:8080/docs")
        print("   ✅ Opened API documentation")
        
    except Exception as e:
        print(f"   ⚠️  Could not open browser: {e}")
        print("   Please manually open:")
        print("   - WhatsApp Clone: http://localhost:8081")
        print("   - API Docs: http://localhost:8080/docs")

def main():
    """Main launcher function"""
    print_banner()
    
    # Check requirements
    if not check_requirements():
        sys.exit(1)
    
    # Check environment
    if not check_environment():
        print("\n💡 You can still run in demo mode, but Twilio features won't work.")
        response = input("Continue anyway? (y/N): ").lower().strip()
        if response != 'y':
            sys.exit(1)
    
    # Start processes
    processes = {}
    
    # Start main backend
    main_process = start_main_backend()
    processes['Main AI Backend'] = main_process
    
    if not main_process:
        print("❌ Cannot continue without main backend")
        sys.exit(1)
    
    # Start WhatsApp clone
    clone_process = start_whatsapp_clone()
    processes['WhatsApp Clone'] = clone_process
    
    if not clone_process:
        print("❌ Cannot continue without WhatsApp clone")
        if main_process:
            main_process.terminate()
        sys.exit(1)
    
    # Open browser
    threading.Thread(target=open_browser, daemon=True).start()
    
    # Show success message
    print("\n🎉 All services started successfully!")
    print("\n📋 Available URLs:")
    print("   💬 WhatsApp Clone: http://localhost:8081")
    print("   🤖 AI Backend: http://localhost:8080")
    print("   📚 API Docs: http://localhost:8080/docs")
    print("   ❤️  Health Check: http://localhost:8080/health")
    
    print("\n💡 Usage Tips:")
    print("   - Use 'Try Demo' for immediate access (no Google login required)")
    print("   - Configure Google OAuth for full authentication")
    print("   - Enable Twilio integration in settings for real WhatsApp")
    print("   - All messages connect to your AI backend")
    
    # Monitor processes
    monitor_processes(processes)
    
    print("\n👋 Goodbye!")

if __name__ == "__main__":
    main()