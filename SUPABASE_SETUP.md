# Supabase Setup Guide

This guide will help you set up Supabase for the WhatsApp Clone functionality.

## Quick Fix for "Failed to create new user" Error

The error you're experiencing is likely due to missing Supabase configuration. Here's how to fix it:

### 1. Set up Supabase Project

1. Go to [supabase.com](https://supabase.com) and create a free account
2. Create a new project
3. Wait for the project to be fully provisioned (this can take a few minutes)

### 2. Get Your Credentials

1. In your Supabase dashboard, go to **Settings** → **API**
2. Copy the following values:
   - **Project URL** (looks like: `https://your-project-id.supabase.co`)
   - **Anon/Public Key** (starts with `eyJ...`)

### 3. Update Your Environment Variables

Add these lines to your `.env` file:

```bash
# Supabase Configuration (Required for WhatsApp Clone)
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_ANON_KEY=your-anon-key-here

# Google OAuth Configuration (Optional - for Google login)
GOOGLE_CLIENT_ID=your-google-client-id-here
```

### 4. Create Database Tables

1. In your Supabase dashboard, go to **SQL Editor**
2. Copy the entire contents of `supabase_whatsapp_schema.sql` file
3. Paste it into the SQL Editor and click **Run**
4. This will create all necessary tables and indexes

### 5. Test Your Setup

Run the test script to verify everything is working:

```bash
python test_supabase.py
```

This will check:
- ✅ Environment variables are set
- ✅ Database connection works
- ✅ Tables exist and are accessible
- ✅ User creation/retrieval works

## Common Issues and Solutions

### Issue 1: "SUPABASE_URL is not set"
**Solution:** Add `SUPABASE_URL=https://your-project.supabase.co` to your `.env` file

### Issue 2: "SUPABASE_ANON_KEY is not set"
**Solution:** Add `SUPABASE_ANON_KEY=your-anon-key` to your `.env` file

### Issue 3: "relation 'whatsapp_users' does not exist"
**Solution:** Run the SQL schema in your Supabase SQL Editor:
1. Copy contents of `supabase_whatsapp_schema.sql`
2. Paste in Supabase SQL Editor
3. Click Run

### Issue 4: "Failed to create user - no data returned from insert"
**Solution:** This usually means RLS (Row Level Security) is blocking the insert:
1. Go to Supabase Dashboard → Authentication → Policies
2. Temporarily disable RLS for testing, or
3. Make sure you're using the service role key for server-side operations

### Issue 5: "Invalid email format"
**Solution:** Ensure the email field contains a valid email address with @ and . characters

## Features Enabled by Supabase

Once properly configured, you'll have:

- ✅ User authentication and profiles
- ✅ Chat session management
- ✅ Message history storage
- ✅ Search functionality
- ✅ User analytics
- ✅ Real-time updates
- ✅ Data persistence across sessions

## Testing the Integration

After setup, test these features:

1. **User Creation:**
   ```bash
   curl -X POST http://localhost:8080/api/user/create \
     -H "Content-Type: application/json" \
     -d '{"email":"test@example.com","name":"Test User"}'
   ```

2. **Session Creation:**
   ```bash
   curl -X POST http://localhost:8080/api/session/create \
     -H "Content-Type: application/json" \
     -d '{"user_id":"user-id-here","title":"Test Chat"}'
   ```

3. **Send Message:**
   ```bash
   curl -X POST http://localhost:8080/whatsapp/webhook \
     -H "Content-Type: application/json" \
     -d '{"Body":"Hello","From":"test-user","user_data":{"email":"test@example.com","name":"Test User"}}'
   ```

## Security Notes

- The `SUPABASE_ANON_KEY` is safe to use in client-side code
- For server-side operations, you might need the `SUPABASE_SERVICE_ROLE_KEY`
- Row Level Security (RLS) is enabled by default for data protection
- All user data is isolated by user ID

## Need Help?

If you're still having issues:

1. Run `python test_supabase.py` and share the output
2. Check your Supabase project logs in the dashboard
3. Verify your `.env` file has the correct credentials
4. Make sure your Supabase project is fully provisioned (not still setting up)

The application will fall back to basic functionality without Supabase, but you'll lose:
- User profiles and authentication
- Message history
- Session management
- Search functionality