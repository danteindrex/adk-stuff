#!/usr/bin/env python3
"""
WhatsApp Clone Demo Script
Demonstrates all features of the WhatsApp clone with Uganda E-Gov AI Assistant
"""

import os
import time
import webbrowser
import subprocess
import sys
from pathlib import Path

def print_demo_banner():
    """Print demo banner"""
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║                  WhatsApp Clone Demo                         ║
    ║              Uganda E-Gov AI Assistant                       ║
    ╠══════════════════════════════════════════════════════════════╣
    ║  🎯 Perfect WhatsApp UI Clone                                ║
    ║  🔐 Google OAuth + Demo Mode                                 ║
    ║  🤖 AI Government Services                                   ║
    ║  🌍 Multi-language Support                                   ║
    ║  📱 Mobile Responsive                                        ║
    ║  🔄 Real-time Messaging                                      ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)

def show_features():
    """Show available features"""
    features = """
    🎨 WHATSAPP CLONE FEATURES:
    
    ✅ Identical WhatsApp Web Interface
       - Pixel-perfect recreation of WhatsApp UI
       - Dark theme matching original
       - Responsive design for all devices
       - Real-time message animations
    
    🔐 Authentication Options
       - Google OAuth integration
       - Demo mode (no login required)
       - Secure user session management
       - Profile management
    
    🤖 AI Assistant Capabilities
       - Birth Certificate (NIRA) status checking
       - Tax Status (URA) balance inquiries
       - NSSF contribution verification
       - Land ownership verification (NLIS)
       - Multi-language support (English, Luganda, Luo, Runyoro)
    
    🔄 WhatsApp Business API Integration
    - Send/receive WhatsApp messages
    - Media sharing (images, docs, audio)
    - Message status updates
    - Webhook integration
       - Toggle on/off functionality
       - Seamless backend integration
    
    💾 Data Management
       - Local storage for chat history
       - User preferences saving
       - Offline capability (PWA)
       - Export chat functionality
    
    🌐 Technical Features
       - Progressive Web App (PWA)
       - Service Worker for offline use
       - Fast loading and caching
       - Cross-browser compatibility
    """
    print(features)

def show_demo_scenarios():
    """Show demo scenarios"""
    scenarios = """
    🎭 DEMO SCENARIOS TO TRY:
    
    1. 📋 Birth Certificate Check
       Type: "Check my birth certificate NIRA/2023/123456"
       
    2. 💰 Tax Status Inquiry
       Type: "My TIN is 1234567890, what's my tax status?"
       
    3. 🏦 NSSF Balance Check
       Type: "Check my NSSF balance, membership 987654321"
       
    4. 🏡 Land Verification
       Type: "I need help with land verification for plot 123 in Kampala"
       
    5. 🌍 Multi-language Test
       Type: "Oli otya?" (Luganda greeting)
       
    6. ❓ General Help
       Type: "What services can you help me with?"
       
    7. 📱 WhatsApp Message Test
       - Send a test message to the demo
       - Try different message types (text, image, document)
       - Send a message and receive it on your phone
    """
    print(scenarios)

def check_demo_requirements():
    """Check if demo can run"""
    print("\n🔍 Checking demo requirements...")
    
    required_files = [
        "whatsapp_clone/index.html",
        "whatsapp_clone/styles.css", 
        "whatsapp_clone/script.js",
        "whatsapp_clone_server.py",
        "main.py"
    ]
    
    missing = []
    for file in required_files:
        if not Path(file).exists():
            missing.append(file)
    
    if missing:
        print("❌ Missing files:")
        for file in missing:
            print(f"   - {file}")
        return False
    
    print("✅ All required files present")
    return True

def start_demo_servers():
    """Start demo servers"""
    print("\n🚀 Starting demo servers...")
    
    # Start main backend
    print("   Starting AI backend...")
    main_process = subprocess.Popen([
        sys.executable, "main.py"
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    time.sleep(3)
    
    # Start WhatsApp clone
    print("   Starting WhatsApp clone...")
    clone_process = subprocess.Popen([
        sys.executable, "whatsapp_clone_server.py"
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    time.sleep(2)
    
    return main_process, clone_process

def open_demo_browser():
    """Open browser for demo"""
    print("\n🌐 Opening demo in browser...")
    
    try:
        # Open WhatsApp clone
        webbrowser.open("http://localhost:8081")
        print("   ✅ WhatsApp Clone: http://localhost:8081")
        
        time.sleep(1)
        
        # Open API docs in new tab
        webbrowser.open("http://localhost:8080/docs")
        print("   ✅ API Documentation: http://localhost:8080/docs")
        
    except Exception as e:
        print(f"   ⚠️  Browser error: {e}")
        print("   Please manually open: http://localhost:8081")

def show_demo_instructions():
    """Show demo instructions"""
    instructions = """
    📖 DEMO INSTRUCTIONS:
    
    1. 🔑 LOGIN OPTIONS:
       - Click "Try Demo" for immediate access (recommended)
       - Or use Google OAuth if configured
    
    2. 💬 MESSAGING:
       - Type messages in the input field at bottom
       - Press Enter or click send button
       - AI responds with government service help
    
    3. ⚙️  SETTINGS:
       - Click menu (⋮) in top right
       - Configure Twilio integration
       - View profile information
    
    4. 📞 TWILIO TESTING:
       - Go to Settings → Twilio Settings
       - Enter your WhatsApp number (+256XXXXXXXXX)
       - Enable "Send messages to actual WhatsApp"
       - Send a message and receive it on your phone!
    
    5. 🎨 UI FEATURES:
       - Notice the identical WhatsApp interface
       - Try on mobile device for responsive design
       - Messages save automatically
    
    6. 🤖 AI TESTING:
       - Try the demo scenarios listed above
       - Test different languages
       - Ask about various government services
    """
    print(instructions)

def wait_for_demo_completion():
    """Wait for user to complete demo"""
    print("\n⏳ Demo is running...")
    print("   💬 WhatsApp Clone: http://localhost:8081")
    print("   🤖 AI Backend: http://localhost:8080")
    print("   📚 API Docs: http://localhost:8080/docs")
    print("\n   Press Ctrl+C to stop the demo")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n🛑 Stopping demo...")

def cleanup_demo(processes):
    """Clean up demo processes"""
    print("   Stopping servers...")
    
    for process in processes:
        if process and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
    
    print("   ✅ Demo stopped successfully")

def main():
    """Main demo function"""
    print_demo_banner()
    show_features()
    show_demo_scenarios()
    
    if not check_demo_requirements():
        print("\n❌ Demo requirements not met")
        print("   Please ensure all WhatsApp clone files are present")
        return
    
    print("\n🎬 Starting WhatsApp Clone Demo...")
    
    try:
        # Start servers
        processes = start_demo_servers()
        
        # Open browser
        open_demo_browser()
        
        # Show instructions
        show_demo_instructions()
        
        # Wait for completion
        wait_for_demo_completion()
        
    except Exception as e:
        print(f"\n❌ Demo error: {e}")
    
    finally:
        # Cleanup
        cleanup_demo(processes)
        
        print("\n🎉 Thanks for trying the WhatsApp Clone demo!")
        print("   💡 To run again: python demo_whatsapp_clone.py")

if __name__ == "__main__":
    main()