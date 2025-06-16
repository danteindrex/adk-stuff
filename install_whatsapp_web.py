#!/usr/bin/env python3
"""
WhatsApp Web Installation Script
Installs and sets up WhatsApp Web automation dependencies
"""

import os
import sys
import subprocess
import asyncio
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(f"   Command: {command}")
        print(f"   Error: {e.stderr}")
        return False

def main():
    """Main installation function"""
    print("🚀 WhatsApp Web Automation Setup")
    print("=" * 40)
    print("Setting up browser automation for Uganda E-Gov Helpdesk")
    print()
    
    # Check if we're in a virtual environment
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("⚠️  Warning: Not in a virtual environment")
        print("💡 Recommended: Create and activate a virtual environment first")
        print("   python -m venv venv")
        print("   source venv/bin/activate  # Linux/Mac")
        print("   venv\\Scripts\\activate     # Windows")
        print()
        
        response = input("Continue anyway? (y/N): ").lower()
        if response != 'y':
            print("👋 Installation cancelled")
            return
    
    print("📦 Installing Python dependencies...")
    
    # Install playwright
    if not run_command("pip install playwright", "Installing Playwright"):
        return
    
    # Install playwright browsers
    if not run_command("playwright install chromium", "Installing Chromium browser"):
        return
    
    # Install additional dependencies if needed
    dependencies = [
        "python-json-logger",  # For the logging issue
        "asyncio",
        "pathlib"
    ]
    
    for dep in dependencies:
        run_command(f"pip install {dep}", f"Installing {dep}")
    
    print("\n🧪 Testing installation...")
    
    # Test playwright installation
    try:
        from playwright.async_api import async_playwright
        print("✅ Playwright imported successfully")
    except ImportError as e:
        print(f"❌ Playwright import failed: {e}")
        return
    
    print("\n🎉 Installation completed successfully!")
    print("\n📋 Next steps:")
    print("1. Set up WhatsApp Web authentication:")
    print("   python start_whatsapp_web.py")
    print()
    print("2. Test the setup:")
    print("   python start_whatsapp_web.py test")
    print()
    print("3. Start the message listener:")
    print("   python whatsapp_web_listener.py")
    print()
    print("4. Or start the full application:")
    print("   python main.py")
    print()
    print("📱 Phone number configured: +256726294861")
    print("🔐 You'll need to scan QR code on first setup")

if __name__ == "__main__":
    main()