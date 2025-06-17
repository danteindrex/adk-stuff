from app.database.supabase_client import get_supabase_client

try:
    db = get_supabase_client()
    print("✅ Supabase connection successful!")
except Exception as e:
    print(f"❌ Connection failed: {e}")