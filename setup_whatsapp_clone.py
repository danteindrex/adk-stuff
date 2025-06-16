#!/usr/bin/env python3
"""
WhatsApp Clone Setup Script
Ensures all components are properly configured
"""

import os
import sys
from pathlib import Path
import subprocess

def print_setup_banner():
    """Print setup banner"""
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║                WhatsApp Clone Setup                          ║
    ║            Uganda E-Gov AI Assistant                         ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)

def check_python_version():
    """Check Python version"""
    print("🐍 Checking Python version...")
    
    if sys.version_info < (3, 8):
        print(f"❌ Python 3.8+ required, found {sys.version}")
        return False
    
    print(f"✅ Python {sys.version.split()[0]} - OK")
    return True

def check_required_files():
    """Check if all required files exist"""
    print("\n📁 Checking required files...")
    
    required_files = [
        "main.py",
        "requirements.txt",
        "whatsapp_clone/index.html",
        "whatsapp_clone/styles.css",
        "whatsapp_clone/script.js",
        "whatsapp_clone/README.md",
        "whatsapp_clone_server.py",
        "launch_whatsapp_clone.py",
        "demo_whatsapp_clone.py"
    ]
    
    missing_files = []
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path}")
            missing_files.append(file_path)
    
    if missing_files:
        print(f"\n❌ Missing {len(missing_files)} required files")
        return False
    
    print(f"\n✅ All {len(required_files)} required files present")
    return True

def check_dependencies():
    """Check Python dependencies"""
    print("\n📦 Checking Python dependencies...")
    
    required_packages = [
        "fastapi",
        "uvicorn",
        "python-dotenv",
        "twilio",
        "google-adk"
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package}")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n⚠️  Missing {len(missing_packages)} packages")
        print("   Run: pip install -r requirements.txt")
        return False
    
    print(f"\n✅ All {len(required_packages)} packages installed")
    return True

def check_environment_config():
    """Check environment configuration"""
    print("\n🔧 Checking environment configuration...")
    
    # Check for .env file
    if not Path(".env").exists():
        print("⚠️  No .env file found")
        create_env_template()
        return False
    
    print("✅ .env file exists")
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Check required variables
    required_vars = {
        "TWILIO_ACCOUNT_SID": "Twilio Account SID",
        "TWILIO_AUTH_TOKEN": "Twilio Auth Token", 
        "TWILIO_WHATSAPP_NUMBER": "Twilio WhatsApp Number"
    }
    
    optional_vars = {
        "GOOGLE_CLIENT_ID": "Google OAuth Client ID"
    }
    
    missing_required = []
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value:
            print(f"✅ {var} - {description}")
        else:
            print(f"❌ {var} - {description}")
            missing_required.append(var)
    
    for var, description in optional_vars.items():
        value = os.getenv(var)
        if value and value != "YOUR_GOOGLE_CLIENT_ID":
            print(f"✅ {var} - {description}")
        else:
            print(f"⚠️  {var} - {description} (optional)")
    
    if missing_required:
        print(f"\n❌ Missing {len(missing_required)} required environment variables")
        print("   Please configure your .env file")
        return False
    
    print("\n✅ Environment configuration complete")
    return True

def create_env_template():
    """Create .env template"""
    print("📝 Creating .env template...")
    
    template = """# Twilio Configuration (Required for WhatsApp integration)
TWILIO_ACCOUNT_SID=your_twilio_account_sid_here
TWILIO_AUTH_TOKEN=your_twilio_auth_token_here
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886

# Google OAuth (Optional - demo mode available without this)
GOOGLE_CLIENT_ID=your_google_client_id_here

# Application Configuration
ENVIRONMENT=development
LOG_LEVEL=INFO
PORT_NO=8080

# Optional: Database and other services
# DATABASE_URL=sqlite:///./app.db
# REDIS_URL=redis://localhost:6379
"""
    
    with open(".env", "w") as f:
        f.write(template)
    
    print("✅ Created .env file with template")
    print("   Please edit .env and add your actual credentials")

def test_basic_functionality():
    """Test basic functionality"""
    print("\n🧪 Testing basic functionality...")
    
    try:
        # Test imports
        from whatsapp_clone_server import clone_app
        print("✅ WhatsApp clone server imports")
        
        # Test main app import
        import main
        print("✅ Main AI backend imports")
        
        return True
        
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def show_next_steps():
    """Show next steps"""
    steps = """
    🚀 SETUP COMPLETE! Next Steps:
    
    1. 📝 Configure Environment (if not done):
       - Edit .env file with your Twilio credentials
       - Optionally add Google OAuth Client ID
    
    2. 🎬 Run Demo:
       python demo_whatsapp_clone.py
    
    3. 🚀 Launch Full Application:
       python launch_whatsapp_clone.py
    
    4. 🌐 Access URLs:
       - WhatsApp Clone: http://localhost:8081
       - AI Backend: http://localhost:8080
       - API Docs: http://localhost:8080/docs
    
    5. 💡 Demo Features:
       - Use "Try Demo" button for immediate access
       - Test AI conversations with government services
       - Configure Twilio for real WhatsApp integration
       - Try on mobile devices for responsive design
    
    📚 Documentation:
       - Read whatsapp_clone/README.md for detailed setup
       - Check .env file for configuration options
    """
    print(steps)

def main():
    """Main setup function"""
    print_setup_banner()
    
    success = True
    
    # Run all checks
    if not check_python_version():
        success = False
    
    if not check_required_files():
        success = False
    
    if not check_dependencies():
        success = False
    
    if not check_environment_config():
        success = False
    
    if success and not test_basic_functionality():
        success = False
    
    print("\n" + "="*60)
    
    if success:
        print("🎉 SETUP SUCCESSFUL!")
        show_next_steps()
    else:
        print("❌ SETUP INCOMPLETE")
        print("\nPlease resolve the issues above and run setup again:")
        print("python setup_whatsapp_clone.py")
    
    print("="*60)

if __name__ == "__main__":
    main()