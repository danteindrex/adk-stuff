#!/usr/bin/env python3
"""
Session Management Fix for Uganda E-Gov WhatsApp Helpdesk
Adds automatic session creation for new users in the webhook
"""

def add_session_creation_to_webhook():
    """Add session creation logic to the main webhook function"""
    
    # Read the main.py file
    with open('main.py', 'r') as f:
        content = f.read()
    
    # Find the webhook function and add session creation
    webhook_start = content.find('print(f"\\n🎯 FINAL EXTRACTED DATA:")')
    webhook_end = content.find('# Generate response with detailed logging', webhook_start)
    
    if webhook_start == -1 or webhook_end == -1:
        print("❌ Could not find webhook function sections")
        return False
    
    # Insert session creation code
    session_creation_code = '''
        # Ensure session exists for this user before generating response
        print(f"\\n🔧 ENSURING USER SESSION EXISTS:")
        try:
            # Check if user has an active session
            existing_session = await session_manager.get_user_active_session(user_id)
            
            if not existing_session:
                print(f"   📝 Creating new session for WhatsApp user: {user_id}")
                session_id = await session_manager.create_session(
                    user_id=user_id,
                    initial_data={
                        "first_message": user_text,
                        "created_via": "whatsapp_webhook",
                        "source": "whatsapp_business_api",
                        "user_phone": user_id
                    }
                )
                print(f"   ✅ Created session: {session_id}")
                
                # Log new user session creation
                if monitoring_service:
                    await monitoring_service.log_conversation_event({
                        "event": "new_whatsapp_user_session",
                        "user_id": user_id,
                        "session_id": session_id,
                        "first_message": user_text[:100]
                    })
            else:
                print(f"   ✅ Using existing session: {existing_session['session_id']}")
                
        except Exception as session_error:
            print(f"   ⚠️  Session creation error: {session_error}")
            logger.warning(f"Failed to create session for user {user_id}: {session_error}")

        '''
    
    # Insert the code before the response generation
    new_content = content[:webhook_end] + session_creation_code + content[webhook_end:]
    
    # Write back to file
    with open('main.py', 'w') as f:
        f.write(new_content)
    
    print("✅ Successfully added session creation to webhook")
    return True

if __name__ == "__main__":
    print("🔧 Adding session creation to WhatsApp webhook...")
    success = add_session_creation_to_webhook()
    
    if success:
        print("🎉 Session management fix applied successfully!")
        print("📝 The webhook will now automatically create sessions for new users")
    else:
        print("❌ Failed to apply session management fix")