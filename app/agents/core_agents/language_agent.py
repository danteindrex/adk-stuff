"""
Language Detection and Translation Agent
Handles multi-language support for Uganda E-Gov WhatsApp Helpdesk
"""

import logging
from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool

logger = logging.getLogger(__name__)

async def create_language_agent():
    """Create language detection and translation agent"""
    try:
        # Create language processing tools
        language_tools = await get_language_tools()
        
        agent = LlmAgent(
            name="language_agent",
            model="gemini-2.0-flash",
            instruction="""You are a language detection and translation agent for the Uganda E-Gov WhatsApp Helpdesk.
            
            Supported languages:
            - English (en) - Primary language
            - Luganda (lg) - Central Uganda
            - Luo (luo) - Northern Uganda  
            - Runyoro (nyn) - Western Uganda
            
            Your responsibilities:
            - Detect the language of incoming user messages
            - Translate messages between supported languages
            - Maintain language preferences for users
            - Provide localized responses and error messages
            - Handle code-switching (mixing languages in one message)
            
            Available tools:
            - detect_language: Identify the language of a text
            - translate_text: Translate text between supported languages
            - get_language_preference: Get user's preferred language
            - set_language_preference: Set user's language preference
            - get_localized_message: Get pre-translated system messages
            
            Language detection guidelines:
            - Analyze the entire message for language patterns
            - Consider common greetings and phrases in each language
            - Handle mixed-language messages by identifying the primary language
            - Default to English if detection is uncertain
            
            Translation guidelines:
            - Preserve the meaning and context of the original message
            - Use appropriate formal/informal tone based on the language
            - Handle government terminology correctly
            - Maintain cultural sensitivity in translations
            
            Common phrases to recognize:
            English: "hello", "help", "birth certificate", "tax", "balance"
            Luganda: "nkusanyuse", "njagala", "birth certificate", "omusolo", "ssente"
            Luo: "ber", "amito", "birth certificate", "kodi", "pesa"
            Runyoro: "oraire ota", "ninkunda", "birth certificate", "omusoro", "sente"
            
            When processing a message:
            1. Detect the language using available patterns and tools
            2. If not English, translate to English for processing
            3. Store the user's language preference
            4. Ensure responses are in the user's preferred language
            """,
            description="Detects user language and provides translation services for multi-language support.",
            tools=language_tools
        )
        
        logger.info("Language agent created successfully")
        return agent
        
    except Exception as e:
        logger.error(f"Failed to create language agent: {e}")
        raise

async def get_language_tools():
    """Get language processing tools"""
    
    def detect_language(text: str, tool_context=None) -> dict:
        """Detect the language of input text"""
        try:
            # Import language detection library
            from langdetect import detect, detect_langs
            
            # Clean the text
            cleaned_text = text.strip().lower()
            
            # Check for common Ugandan language patterns first
            ugandan_patterns = {
                'lg': ['nkusanyuse', 'njagala', 'webale', 'ssebo', 'nnyabo', 'bwoba', 'kale'],
                'luo': ['ber', 'amito', 'erokamano', 'latin', 'dako', 'wuon', 'nyako'],
                'nyn': ['oraire ota', 'ninkunda', 'webale', 'mukama', 'nyabingi', 'omukazi']
            }
            
            # Check for Ugandan language patterns
            for lang_code, patterns in ugandan_patterns.items():
                for pattern in patterns:
                    if pattern in cleaned_text:
                        return {
                            "status": "success",
                            "language": lang_code,
                            "confidence": 0.9,
                            "method": "pattern_matching"
                        }
            
            # Use langdetect for other languages
            detected = detect(cleaned_text)
            
            # Get confidence scores
            lang_probs = detect_langs(cleaned_text)
            confidence = max([prob.prob for prob in lang_probs if prob.lang == detected], default=0.5)
            
            # Map some common misdetections
            if detected in ['sw', 'zu', 'xh']:  # Swahili or other African languages
                detected = 'lg'  # Default to Luganda for African language patterns
            
            return {
                "status": "success",
                "language": detected,
                "confidence": confidence,
                "method": "langdetect",
                "alternatives": [{"lang": prob.lang, "confidence": prob.prob} for prob in lang_probs[:3]]
            }
            
        except Exception as e:
            logger.error(f"Language detection failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "fallback_language": "en"
            }
    
    def translate_text(
        text: str,
        target_language: str,
        source_language: str = None,
        tool_context=None
    ) -> dict:
        """Translate text between supported languages"""
        try:
            # For now, we'll use a simple translation approach
            # In production, you'd use Google Translate API or similar
            
            # Common translations for government services
            translations = {
                'en_to_lg': {
                    'hello': 'nkusanyuse',
                    'help': 'nnyamba',
                    'birth certificate': 'birth certificate',  # Keep technical terms
                    'tax': 'omusolo',
                    'balance': 'ssente',
                    'status': 'embeera',
                    'check': 'kebera',
                    'thank you': 'webale nyo'
                },
                'en_to_luo': {
                    'hello': 'ber',
                    'help': 'kony',
                    'birth certificate': 'birth certificate',
                    'tax': 'kodi',
                    'balance': 'pesa',
                    'status': 'kit',
                    'check': 'nen',
                    'thank you': 'erokamano'
                },
                'en_to_nyn': {
                    'hello': 'oraire ota',
                    'help': 'mbeire',
                    'birth certificate': 'birth certificate',
                    'tax': 'omusoro',
                    'balance': 'sente',
                    'status': 'embeera',
                    'check': 'rora',
                    'thank you': 'webale'
                }
            }
            
            # Simple word-by-word translation for basic phrases
            if target_language in ['lg', 'luo', 'nyn'] and source_language == 'en':
                translation_key = f"en_to_{target_language}"
                if translation_key in translations:
                    translated_text = text.lower()
                    for en_word, local_word in translations[translation_key].items():
                        translated_text = translated_text.replace(en_word, local_word)
                    
                    return {
                        "status": "success",
                        "translated_text": translated_text,
                        "source_language": source_language,
                        "target_language": target_language,
                        "method": "dictionary_lookup"
                    }
            
            # For complex translations, you would integrate with Google Translate API
            # For now, return the original text with a note
            return {
                "status": "partial",
                "translated_text": text,
                "source_language": source_language,
                "target_language": target_language,
                "method": "passthrough",
                "note": "Complex translation requires external service"
            }
            
        except Exception as e:
            logger.error(f"Translation failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "original_text": text
            }
    
    def get_language_preference(user_id: str, tool_context=None) -> dict:
        """Get user's language preference"""
        try:
            # This would typically query the user's profile from the database
            # For now, we'll return a default
            return {
                "status": "success",
                "user_id": user_id,
                "language_preference": "en",  # Default to English
                "source": "default"
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def set_language_preference(user_id: str, language: str, tool_context=None) -> dict:
        """Set user's language preference"""
        try:
            # Validate language
            supported_languages = ['en', 'lg', 'luo', 'nyn']
            if language not in supported_languages:
                return {
                    "status": "error",
                    "error": f"Unsupported language: {language}",
                    "supported_languages": supported_languages
                }
            
            # This would typically update the user's profile in the database
            # For now, we'll just return success
            return {
                "status": "success",
                "user_id": user_id,
                "language_preference": language,
                "message": f"Language preference set to {language}"
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def get_localized_message(message_key: str, language: str = "en", tool_context=None) -> dict:
        """Get pre-translated system messages"""
        try:
            # Pre-translated system messages
            messages = {
                'welcome': {
                    'en': 'Welcome to Uganda E-Gov WhatsApp Helpdesk! How can I help you today?',
                    'lg': 'Nkusanyuse ku Uganda E-Gov WhatsApp Helpdesk! Nnyinza ntya okukuyamba leero?',
                    'luo': 'Ber bino i Uganda E-Gov WhatsApp Helpdesk! Ere an anyalo kony ki tin?',
                    'nyn': 'Oraire ota ku Uganda E-Gov WhatsApp Helpdesk! Ninyine nkukore ota leero?'
                },
                'help_menu': {
                    'en': 'I can help you with:\n1. Birth certificates\n2. Tax status\n3. NSSF balance\n4. Land records',
                    'lg': 'Nnyinza okukuyamba ku:\n1. Birth certificates\n2. Embeera y\'omusolo\n3. NSSF ssente\n4. Ebikwata ku ttaka',
                    'luo': 'Anyalo kony gi:\n1. Birth certificates\n2. Kit pa kodi\n3. NSSF pesa\n4. Buk pa lowo',
                    'nyn': 'Ninyine nkukore ku:\n1. Birth certificates\n2. Embeera y\'omusoro\n3. NSSF sente\n4. Ebikwata ku itaka'
                },
                'error': {
                    'en': 'Sorry, I encountered an error. Please try again.',
                    'lg': 'Nsonyiwa, nafunye ekizibu. Ddamu okugezaako.',
                    'luo': 'Kica, an onongo ki bal. Tem doki.',
                    'nyn': 'Ihangane, nahabire ekizibu. Ongire okugezaho.'
                }
            }
            
            if message_key in messages and language in messages[message_key]:
                return {
                    "status": "success",
                    "message": messages[message_key][language],
                    "language": language,
                    "message_key": message_key
                }
            else:
                # Fallback to English
                fallback_message = messages.get(message_key, {}).get('en', 'Message not found')
                return {
                    "status": "fallback",
                    "message": fallback_message,
                    "language": "en",
                    "message_key": message_key,
                    "note": f"No translation available for {language}"
                }
                
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    # Create function tools
    language_tools = [
        FunctionTool(detect_language),
        FunctionTool(translate_text),
        FunctionTool(get_language_preference),
        FunctionTool(set_language_preference),
        FunctionTool(get_localized_message)
    ]
    
    logger.info(f"Created {len(language_tools)} language processing tools")
    return language_tools