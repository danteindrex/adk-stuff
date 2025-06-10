"""
Intent Classification Agent
Classifies user intent and routes to appropriate service agents
"""

import logging
from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool

logger = logging.getLogger(__name__)

async def create_intent_agent():
    """Create intent classification agent"""
    try:
        # Create intent classification tools
        intent_tools = await get_intent_tools()
        
        agent = LlmAgent(
            name="intent_agent",
            model="gemini-2.0-flash",
            instruction="""You are an intent classification agent for the Uganda E-Gov WhatsApp Helpdesk.
            
            Your primary responsibility is to analyze user messages and determine their intent to route them to the appropriate service agent.
            
            Supported service categories:
            1. BIRTH_CERTIFICATE - Birth certificate status checks, applications, collections
            2. TAX_STATUS - Tax balance, payment history, compliance status
            3. NSSF_BALANCE - Pension contributions, account balance, membership details
            4. LAND_RECORDS - Land ownership verification, title status, property details
            5. FORM_ASSISTANCE - Help with government forms, PDF generation
            6. GENERAL_HELP - General assistance, navigation, information
            7. AUTHENTICATION - Login, logout, account management
            8. LANGUAGE_CHANGE - Language preference changes
            
            Intent classification guidelines:
            - Analyze keywords, phrases, and context
            - Consider user's current conversation state
            - Handle ambiguous requests by asking clarifying questions
            - Support multiple languages (English, Luganda, Luo, Runyoro)
            - Recognize government service abbreviations (NIRA, URA, NSSF, NLIS)
            
            Available tools:
            - classify_intent: Determine the primary intent of a message
            - extract_entities: Extract relevant entities (numbers, dates, names)
            - get_confidence_score: Get confidence level for classification
            - suggest_clarification: Generate clarifying questions for ambiguous intents
            - route_to_agent: Determine which agent should handle the request
            
            Keywords to recognize:
            Birth Certificate: "birth", "certificate", "NIRA", "registration", "born", "delivery"
            Tax: "tax", "URA", "TIN", "payment", "balance", "compliance", "revenue"
            NSSF: "NSSF", "pension", "contribution", "social security", "retirement"
            Land: "land", "NLIS", "title", "ownership", "plot", "property", "deed"
            
            Multi-language keywords:
            Luganda: "mazaalibwa" (birth), "omusolo" (tax), "ttaka" (land)
            Luo: "nywol" (birth), "kodi" (tax), "lowo" (land)
            Runyoro: "kuzaarwa" (birth), "omusoro" (tax), "itaka" (land)
            
            When classifying intent:
            1. Analyze the message for keywords and context
            2. Extract relevant entities (reference numbers, dates, etc.)
            3. Determine confidence level
            4. If confidence is low, suggest clarifying questions
            5. Route to the appropriate service agent
            """,
            description="Classifies user intent and routes requests to appropriate service agents.",
            tools=intent_tools
        )
        
        logger.info("Intent classification agent created successfully")
        return agent
        
    except Exception as e:
        logger.error(f"Failed to create intent agent: {e}")
        raise

async def get_intent_tools():
    """Get intent classification tools"""
    
    def classify_intent(message: str, context: dict = None, tool_context=None) -> dict:
        """Classify the intent of a user message"""
        try:
            message_lower = message.lower().strip()
            
            # Define intent patterns
            intent_patterns = {
                'BIRTH_CERTIFICATE': [
                    'birth', 'certificate', 'nira', 'registration', 'born', 'delivery',
                    'mazaalibwa', 'nywol', 'kuzaarwa', 'birth cert', 'certificate of birth'
                ],
                'TAX_STATUS': [
                    'tax', 'ura', 'tin', 'payment', 'balance', 'compliance', 'revenue',
                    'omusolo', 'kodi', 'omusoro', 'tax status', 'tax balance'
                ],
                'NSSF_BALANCE': [
                    'nssf', 'pension', 'contribution', 'social security', 'retirement',
                    'balance', 'fund', 'social fund'
                ],
                'LAND_RECORDS': [
                    'land', 'nlis', 'title', 'ownership', 'plot', 'property', 'deed',
                    'ttaka', 'lowo', 'itaka', 'land title', 'land ownership'
                ],
                'FORM_ASSISTANCE': [
                    'form', 'application', 'pdf', 'document', 'fill', 'submit',
                    'help with form', 'how to fill'
                ],
                'AUTHENTICATION': [
                    'login', 'logout', 'sign in', 'sign out', 'account', 'password',
                    'register', 'profile'
                ],
                'LANGUAGE_CHANGE': [
                    'language', 'luganda', 'english', 'luo', 'runyoro',
                    'change language', 'olulimi', 'dhok', 'orurimi'
                ],
                'GENERAL_HELP': [
                    'help', 'assist', 'support', 'what can you do', 'services',
                    'nnyamba', 'kony', 'mbeire'
                ]
            }
            
            # Score each intent
            intent_scores = {}
            for intent, keywords in intent_patterns.items():
                score = 0
                matched_keywords = []
                
                for keyword in keywords:
                    if keyword in message_lower:
                        score += 1
                        matched_keywords.append(keyword)
                
                if score > 0:
                    intent_scores[intent] = {
                        'score': score,
                        'keywords': matched_keywords
                    }
            
            # Determine primary intent
            if intent_scores:
                primary_intent = max(intent_scores.keys(), key=lambda x: intent_scores[x]['score'])
                confidence = min(intent_scores[primary_intent]['score'] / 3.0, 1.0)  # Normalize to 0-1
                
                return {
                    "status": "success",
                    "primary_intent": primary_intent,
                    "confidence": confidence,
                    "matched_keywords": intent_scores[primary_intent]['keywords'],
                    "all_intents": intent_scores,
                    "message_length": len(message),
                    "requires_clarification": confidence < 0.5
                }
            else:
                return {
                    "status": "unclear",
                    "primary_intent": "GENERAL_HELP",
                    "confidence": 0.1,
                    "matched_keywords": [],
                    "all_intents": {},
                    "requires_clarification": True,
                    "suggestion": "No clear intent detected, defaulting to general help"
                }
                
        except Exception as e:
            logger.error(f"Intent classification failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "primary_intent": "GENERAL_HELP",
                "confidence": 0.0
            }
    
    def extract_entities(message: str, intent: str = None, tool_context=None) -> dict:
        """Extract relevant entities from the message"""
        try:
            import re
            
            entities = {}
            
            # Extract reference numbers
            # NIRA format: NIRA/YYYY/NNNNNN
            nira_pattern = r'NIRA/\d{4}/\d{6}'
            nira_matches = re.findall(nira_pattern, message, re.IGNORECASE)
            if nira_matches:
                entities['nira_reference'] = nira_matches[0]
            
            # Extract TIN numbers (10 digits)
            tin_pattern = r'\b\d{10}\b'
            tin_matches = re.findall(tin_pattern, message)
            if tin_matches:
                entities['tin_number'] = tin_matches[0]
            
            # Extract NSSF membership numbers (8-12 digits)
            nssf_pattern = r'\b\d{8,12}\b'
            nssf_matches = re.findall(nssf_pattern, message)
            if nssf_matches and intent == 'NSSF_BALANCE':
                entities['nssf_membership'] = nssf_matches[0]
            
            # Extract plot numbers
            plot_pattern = r'plot\s+(\w+)'
            plot_matches = re.findall(plot_pattern, message, re.IGNORECASE)
            if plot_matches:
                entities['plot_number'] = plot_matches[0]
            
            # Extract GPS coordinates
            gps_pattern = r'(-?\d+\.?\d*),\s*(-?\d+\.?\d*)'
            gps_matches = re.findall(gps_pattern, message)
            if gps_matches:
                entities['gps_coordinates'] = f"{gps_matches[0][0]},{gps_matches[0][1]}"
            
            # Extract phone numbers
            phone_pattern = r'\+?256\d{9}|\b0\d{9}\b'
            phone_matches = re.findall(phone_pattern, message)
            if phone_matches:
                entities['phone_number'] = phone_matches[0]
            
            # Extract dates
            date_pattern = r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b'
            date_matches = re.findall(date_pattern, message)
            if date_matches:
                entities['date'] = date_matches[0]
            
            return {
                "status": "success",
                "entities": entities,
                "entity_count": len(entities),
                "message": message
            }
            
        except Exception as e:
            logger.error(f"Entity extraction failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "entities": {}
            }
    
    def get_confidence_score(classification_result: dict, tool_context=None) -> dict:
        """Calculate confidence score for intent classification"""
        try:
            base_confidence = classification_result.get('confidence', 0.0)
            
            # Adjust confidence based on various factors
            adjustments = 0.0
            
            # Boost confidence if specific entities are found
            if classification_result.get('matched_keywords'):
                keyword_count = len(classification_result['matched_keywords'])
                adjustments += min(keyword_count * 0.1, 0.3)
            
            # Reduce confidence for very short messages
            message_length = classification_result.get('message_length', 0)
            if message_length < 10:
                adjustments -= 0.2
            
            # Boost confidence for longer, more descriptive messages
            elif message_length > 50:
                adjustments += 0.1
            
            final_confidence = min(max(base_confidence + adjustments, 0.0), 1.0)
            
            return {
                "status": "success",
                "base_confidence": base_confidence,
                "adjustments": adjustments,
                "final_confidence": final_confidence,
                "confidence_level": "high" if final_confidence > 0.7 else "medium" if final_confidence > 0.4 else "low"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "final_confidence": 0.0
            }
    
    def suggest_clarification(intent: str, confidence: float, tool_context=None) -> dict:
        """Suggest clarifying questions for ambiguous intents"""
        try:
            clarification_questions = {
                'BIRTH_CERTIFICATE': [
                    "Do you want to check the status of an existing birth certificate application?",
                    "Do you need help applying for a new birth certificate?",
                    "Do you have a NIRA reference number to check?"
                ],
                'TAX_STATUS': [
                    "Do you want to check your tax balance or payment history?",
                    "Do you have your TIN number ready?",
                    "Are you looking for tax compliance information?"
                ],
                'NSSF_BALANCE': [
                    "Do you want to check your NSSF account balance?",
                    "Do you have your NSSF membership number?",
                    "Are you looking for contribution history?"
                ],
                'LAND_RECORDS': [
                    "Do you want to verify land ownership?",
                    "Do you have a plot number or GPS coordinates?",
                    "Are you checking land title status?"
                ],
                'GENERAL_HELP': [
                    "What specific government service do you need help with?",
                    "Are you looking for birth certificates, tax information, NSSF balance, or land records?",
                    "How can I assist you today?"
                ]
            }
            
            questions = clarification_questions.get(intent, clarification_questions['GENERAL_HELP'])
            
            return {
                "status": "success",
                "intent": intent,
                "confidence": confidence,
                "clarification_questions": questions,
                "suggested_question": questions[0] if questions else "How can I help you?",
                "needs_clarification": confidence < 0.5
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "suggested_question": "How can I help you?"
            }
    
    def route_to_agent(intent: str, entities: dict = None, tool_context=None) -> dict:
        """Determine which agent should handle the request"""
        try:
            agent_routing = {
                'BIRTH_CERTIFICATE': 'birth_agent',
                'TAX_STATUS': 'tax_agent',
                'NSSF_BALANCE': 'nssf_agent',
                'LAND_RECORDS': 'land_agent',
                'FORM_ASSISTANCE': 'form_agent',
                'AUTHENTICATION': 'auth_agent',
                'LANGUAGE_CHANGE': 'language_agent',
                'GENERAL_HELP': 'help_agent'
            }
            
            target_agent = agent_routing.get(intent, 'help_agent')
            
            # Prepare context for the target agent
            agent_context = {
                "intent": intent,
                "entities": entities or {},
                "routing_confidence": 1.0 if intent in agent_routing else 0.5
            }
            
            return {
                "status": "success",
                "target_agent": target_agent,
                "intent": intent,
                "agent_context": agent_context,
                "routing_reason": f"Intent '{intent}' maps to '{target_agent}'"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "target_agent": "help_agent",
                "intent": "GENERAL_HELP"
            }
    
    # Create function tools
    intent_tools = [
        FunctionTool(classify_intent),
        FunctionTool(extract_entities),
        FunctionTool(get_confidence_score),
        FunctionTool(suggest_clarification),
        FunctionTool(route_to_agent)
    ]
    
    logger.info(f"Created {len(intent_tools)} intent classification tools")
    return intent_tools