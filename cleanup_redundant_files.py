#!/usr/bin/env python3
"""
Cleanup script to remove redundant files from the Uganda E-Gov WhatsApp project
"""

import os
import shutil
from pathlib import Path

def remove_file_safe(file_path):
    """Safely remove a file if it exists"""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"✅ Removed: {file_path}")
            return True
        else:
            print(f"⚠️  Not found: {file_path}")
            return False
    except Exception as e:
        print(f"❌ Error removing {file_path}: {e}")
        return False

def remove_dir_safe(dir_path):
    """Safely remove a directory if it exists"""
    try:
        if os.path.exists(dir_path):
            shutil.rmtree(dir_path)
            print(f"✅ Removed directory: {dir_path}")
            return True
        else:
            print(f"⚠️  Directory not found: {dir_path}")
            return False
    except Exception as e:
        print(f"❌ Error removing directory {dir_path}: {e}")
        return False

def main():
    """Main cleanup function"""
    print("🧹 Starting cleanup of redundant files...")
    print("=" * 60)
    
    # Change to project directory
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    removed_count = 0
    
    # 1. Remove redundant startup scripts (keep start_local_fixed.py)
    print("\n📁 Cleaning up startup scripts...")
    startup_files = [
        "start_local.py",
        "start_server.py"
    ]
    
    for file in startup_files:
        if remove_file_safe(file):
            removed_count += 1
    
    # 2. Remove redundant deployment scripts (keep deploy_fixed.sh and deploy-to-cloudrun.sh)
    print("\n📁 Cleaning up deployment scripts...")
    deploy_files = [
        "deploy.sh",
        "deploy-to-cloudrun.ps1",
        "setup-secrets.ps1"
    ]
    
    for file in deploy_files:
        if remove_file_safe(file):
            removed_count += 1
    
    # 3. Remove redundant WhatsApp clone files (keep Supabase versions)
    print("\n📁 Cleaning up WhatsApp clone files...")
    whatsapp_files = [
        "whatsapp_clone/index.html",
        "whatsapp_clone/index_backup.html", 
        "whatsapp_clone/script.js"
    ]
    
    for file in whatsapp_files:
        if remove_file_safe(file):
            removed_count += 1
    
    # 4. Remove redundant session managers (keep simple_session_manager.py)
    print("\n📁 Cleaning up session managers...")
    session_files = [
        "app/services/session_manager.py",
        "app/services/google_session_manager.py"
    ]
    
    for file in session_files:
        if remove_file_safe(file):
            removed_count += 1
    
    # 5. Remove redundant documentation files
    print("\n📁 Cleaning up redundant documentation...")
    doc_files = [
        "ADMIN_DASHBOARD.md",
        "ADMIN_NO_MOCK_DATA.md", 
        "CLEANUP_SUMMARY.md",
        "CLOUD_RUN_DEPLOYMENT.md",
        "DEPLOYMENT_READY.md",
        "DOCKER_SETUP.md",
        "INTELLIGENT_AGENT_READY.md",
        "PRODUCTION_CHECKLIST.md",
        "QUICK_START_CLOUD_RUN.md",
        "WHATSAPP_SETUP_GUIDE.md"
    ]
    
    for file in doc_files:
        if remove_file_safe(file):
            removed_count += 1
    
    # 6. Remove redundant database schema (keep supabase_whatsapp_schema.sql)
    print("\n📁 Cleaning up database schemas...")
    if remove_file_safe("database_schema.sql"):
        removed_count += 1
    
    # 7. Remove test file in root (keep tests/ directory)
    print("\n📁 Cleaning up test files...")
    if remove_file_safe("test_system.py"):
        removed_count += 1
    
    # 8. Remove unnecessary files
    print("\n📁 Cleaning up miscellaneous files...")
    misc_files = [
        "import secrets.py",  # Seems like a mistake file
        "package.json",       # Not needed for Python project
        "service.yaml"        # Redundant with docker-compose.yml
    ]
    
    for file in misc_files:
        if remove_file_safe(file):
            removed_count += 1
    
    # 9. Remove empty or unnecessary directories
    print("\n📁 Cleaning up directories...")
    dirs_to_check = [
        "langgraph",
        "app/mcp_servers"  # Empty directory
    ]
    
    for dir_path in dirs_to_check:
        if os.path.exists(dir_path):
            # Check if directory is empty or contains only __init__.py
            contents = os.listdir(dir_path)
            if not contents or (len(contents) == 1 and contents[0] == "__init__.py"):
                if remove_dir_safe(dir_path):
                    removed_count += 1
    
    print("\n" + "=" * 60)
    print(f"🎉 Cleanup completed! Removed {removed_count} redundant files/directories.")
    print("\n📋 Remaining key files:")
    print("  ✅ main.py (main application)")
    print("  ✅ start_local_fixed.py (startup script)")
    print("  ✅ deploy_fixed.sh (deployment)")
    print("  ✅ deploy-to-cloudrun.sh (cloud deployment)")
    print("  ✅ setup-secrets.sh (setup script)")
    print("  ✅ whatsapp_clone/index_supabase.html (WhatsApp UI)")
    print("  ✅ whatsapp_clone/script_supabase.js (WhatsApp logic)")
    print("  ✅ app/services/simple_session_manager.py (session management)")
    print("  ✅ supabase_whatsapp_schema.sql (database schema)")
    print("  ✅ SUPABASE_SETUP.md (setup guide)")
    print("  ✅ WHATSAPP_CLONE_COMPLETE.md (documentation)")
    print("  ✅ README.md (main documentation)")
    
    print("\n💡 Next step: Clean up requirements.txt duplicates")

if __name__ == "__main__":
    main()