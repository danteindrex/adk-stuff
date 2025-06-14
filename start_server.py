#!/usr/bin/env python3
"""
Simple server startup script for testing admin dashboard
"""

import uvicorn
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

if __name__ == "__main__":
    print("🚀 Starting Uganda E-Gov WhatsApp Helpdesk Server...")
    print("📊 Admin Dashboard will be available at: http://localhost:8080/admin/")
    print("🔐 Login credentials:")
    print("   Username: trevor")
    print("   Password: The$1000")
    print("=" * 60)
    
    # Start the server
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8080,
        reload=True,
        log_level="info"
    )