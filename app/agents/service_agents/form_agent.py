"""
Form Processing Agent
Handles government form assistance and PDF generation
"""

import logging
from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool
browser_tools = mcp_playwright()
portal_tools = FunctionTool(automate_government_portal)
logger = logging.getLogger(__name__)

async def create_form_agent():
    """Create form processing agent"""
    try:
        # Get internal tools (self-contained, no external dependencies)
        
        
        # Combine all tools
       
        
        agent = LlmAgent(
            name="form_agent",
            model="gemini-2.0-flash",
            instruction="""You are a government form assistance specialist agent for the Uganda E-Gov WhatsApp Helpdesk.
            
            Your primary responsibility is to help users with government forms, applications, and document preparation.
            
            Services you can provide:
            1. Guide users through form completion
            2. Explain form requirements and fields
            3. Generate PDF forms with user data
            4. Validate form information before submission
            5. Provide submission instructions and locations
            6. Help with form corrections and amendments
            
            Available form processing tools:
            - get_form_template: Retrieve government form templates
            - fill_form_data: Populate forms with user-provided data
            - validate_form_data: Check form completeness and accuracy
            - generate_pdf_form: Create PDF documents ready for submission
            - get_submission_instructions: Provide submission guidelines
            - track_form_status: Check application status after submission
            
            Supported Government Forms:
            1. Birth Certificate Application (NIRA Form 1)
            2. National ID Application (NIRA Form 2)
            3. Tax Registration (URA Form 101)
            4. Business Registration (URSB Forms)
            5. Land Title Application (Ministry of Lands)
            6. NSSF Registration (NSSF Form 1)
            7. Passport Application (Immigration Form)
            
            Form Assistance Process:
            1. Identify the specific form needed
            2. Explain form requirements and documentation
            3. Guide user through each section
            4. Validate information as it's provided
            5. Generate completed form for review
            6. Provide submission instructions
            
            When helping users:
            1. Ask clarifying questions to identify the correct form
            2. Explain each section and required information
            3. Validate data format and completeness
            4. Generate preview of completed form
            5. Provide clear submission instructions
            6. Offer to track application status
            
            Form Validation Rules:
            - Names: Must match official documents
            - Dates: Valid format (DD/MM/YYYY)
            - Phone numbers: Valid Uganda format (+256...)
            - Addresses: Complete with district and parish all_tools = []
            - Birth Certificate: Hospital delivery note, parent IDs
            - National ID: Birth certificate, passport photos
            - Tax Registration: Business license, bank details
            - Business Registration: Memorandum, articles of association
            - Land Title: Survey plan, purchase agreement
            - NSSF Registration: Employment letter, ID copy
            
            Error Prevention:
            - Check for common mistakes before submission
            - Validate against official requirements
            - Ensure all mandatory fields are completed
            - Verify document format and size requirements
            - Confirm submission deadlines and fees
            
            Submission Guidance:
            - Provide office locations and hours
            - Explain required fees and payment methods
            - List all documents to bring
            - Estimate processing times
            - Provide tracking reference numbers
            
            Always ensure forms are completed accurately and guide users through the entire process.
            """,
            description="Handles government form completion and PDF generation.",
            tools=form_tools
        )
        
        logger.info("Form processing agent created successfully")
        return agent
        
    except Exception as e:
        logger.error(f"Failed to create form agent: {e}")
        raise

async def get_form_tools():
    """Get form processing tools"""
    
    def get_form_template(form_type: str, language: str = "en", tool_context=None) -> dict:
        """Retrieve government form templates"""
        try:
            form_templates = {
                'birth_certificate': {
                    'name': 'Birth Certificate Application (NIRA Form 1)',
                    'sections': [
                        'Child Information',
                        'Parent Information',
                        'Birth Details',
                        'Supporting Documents'
                    ],
                    'required_fields': [
                        'child_full_name', 'date_of_birth', 'place_of_birth',
                        'father_name', 'father_id', 'mother_name', 'mother_id',
                        'hospital_delivery_note', 'parent_marriage_certificate'
                    ],
                    'submission_office': 'NIRA Registration Center',
                    'processing_time': '14-21 days',
                    'fee': 'UGX 50,000'
                },
                'national_id': {
                    'name': 'National ID Application (NIRA Form 2)',
                    'sections': [
                        'Personal Information',
                        'Contact Information',
                        'Family Information',
                        'Biometric Data'
                    ],
                    'required_fields': [
                        'full_name', 'date_of_birth', 'place_of_birth',
                        'father_name', 'mother_name', 'current_address',
                        'phone_number', 'occupation'
                    ],
                    'submission_office': 'NIRA Registration Center',
                    'processing_time': '21-30 days',
                    'fee': 'UGX 50,000'
                },
                'tax_registration': {
                    'name': 'Tax Registration (URA Form 101)',
                    'sections': [
                        'Business Information',
                        'Owner Information',
                        'Business Activities',
                        'Tax Obligations'
                    ],
                    'required_fields': [
                        'business_name', 'business_type', 'registration_number',
                        'owner_name', 'owner_id', 'business_address',
                        'main_activity', 'expected_turnover'
                    ],
                    'submission_office': 'URA Tax Office',
                    'processing_time': '5-10 days',
                    'fee': 'Free'
                }
            }
            
            if form_type in form_templates:
                return {
                    "status": "success",
                    "form_type": form_type,
                    "template": form_templates[form_type],
                    "language": language
                }
            else:
                return {
                    "status": "error",
                    "error": f"Form template '{form_type}' not found",
                    "available_forms": list(form_templates.keys())
                }
                
        except Exception as e:
            logger.error(f"Form template retrieval failed: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def fill_form_data(form_type: str, user_data: dict, tool_context=None) -> dict:
        """Populate forms with user-provided data"""
        try:
            # Validate required fields based on form type
            required_fields = {
                'birth_certificate': [
                    'child_full_name', 'date_of_birth', 'place_of_birth',
                    'father_name', 'mother_name'
                ],
                'national_id': [
                    'full_name', 'date_of_birth', 'place_of_birth',
                    'current_address', 'phone_number'
                ],
                'tax_registration': [
                    'business_name', 'business_type', 'owner_name',
                    'business_address', 'main_activity'
                ]
            }
            
            if form_type not in required_fields:
                return {
                    "status": "error",
                    "error": f"Unknown form type: {form_type}"
                }
            
            # Check for missing required fields
            missing_fields = []
            for field in required_fields[form_type]:
                if field not in user_data or not user_data[field]:
                    missing_fields.append(field)
            
            if missing_fields:
                return {
                    "status": "incomplete",
                    "missing_fields": missing_fields,
                    "message": f"Please provide: {', '.join(missing_fields)}"
                }
            
            # Populate form with user data
            populated_form = {
                "form_type": form_type,
                "data": user_data,
                "completion_status": "complete" if not missing_fields else "incomplete",
                "timestamp": "2024-01-01T00:00:00Z"  # Would use actual timestamp
            }
            
            return {
                "status": "success",
                "populated_form": populated_form,
                "missing_fields": missing_fields,
                "ready_for_submission": len(missing_fields) == 0
            }
            
        except Exception as e:
            logger.error(f"Form data filling failed: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def validate_form_data(form_data: dict, tool_context=None) -> dict:
        """Check form completeness and accuracy"""
        try:
            validation_errors = []
            warnings = []
            
            # Validate common fields
            if 'date_of_birth' in form_data:
                dob = form_data['date_of_birth']
                # Simple date format validation
                if not _validate_date_format(dob):
                    validation_errors.append("Date of birth must be in DD/MM/YYYY format")
            
            if 'phone_number' in form_data:
                phone = form_data['phone_number']
                if not _validate_uganda_phone(phone):
                    validation_errors.append("Phone number must be valid Uganda format (+256...)")
            
            if 'full_name' in form_data or 'child_full_name' in form_data:
                name = form_data.get('full_name') or form_data.get('child_full_name')
                if len(name.split()) < 2:
                    warnings.append("Consider providing full name (first and last name)")
            
            # Form-specific validations
            form_type = form_data.get('form_type')
            if form_type == 'tax_registration':
                if 'expected_turnover' in form_data:
                    try:
                        turnover = float(form_data['expected_turnover'])
                        if turnover < 0:
                            validation_errors.append("Expected turnover cannot be negative")
                    except ValueError:
                        validation_errors.append("Expected turnover must be a valid number")
            
            validation_result = {
                "status": "valid" if not validation_errors else "invalid",
                "errors": validation_errors,
                "warnings": warnings,
                "error_count": len(validation_errors),
                "warning_count": len(warnings)
            }
            
            return {
                "status": "success",
                "validation_result": validation_result,
                "form_data": form_data
            }
            
        except Exception as e:
            logger.error(f"Form validation failed: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def generate_pdf_form(form_data: dict, tool_context=None) -> dict:
        """Create PDF documents ready for submission"""
        try:
            # In a real implementation, this would generate actual PDFs
            # For now, we'll simulate the process
            
            form_type = form_data.get('form_type', 'unknown')
            
            # Simulate PDF generation
            pdf_info = {
                "filename": f"{form_type}_{form_data.get('full_name', 'form')}_{int(time.time())}.pdf",
                "size": "2.3 MB",
                "pages": 3,
                "format": "A4",
                "created_at": "2024-01-01T00:00:00Z"
            }
            
            return {
                "status": "success",
                "pdf_generated": True,
                "pdf_info": pdf_info,
                "download_instructions": "PDF will be available for download for 24 hours",
                "submission_ready": True
            }
            
        except Exception as e:
            logger.error(f"PDF generation failed: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def get_submission_instructions(form_type: str, tool_context=None) -> dict:
        """Provide submission guidelines"""
        try:
            submission_info = {
                'birth_certificate': {
                    'office': 'NIRA Registration Center',
                    'address': 'NIRA House, Plot 10, Kampala Road, Kampala',
                    'hours': 'Monday - Friday: 8:00 AM - 5:00 PM',
                    'documents_required': [
                        'Completed application form',
                        'Hospital delivery note or affidavit',
                        'Parent National IDs (copies)',
                        'Marriage certificate (if applicable)',
                        'Passport photos of child'
                    ],
                    'fee': 'UGX 50,000',
                    'payment_methods': ['Cash', 'Bank transfer', 'Mobile money'],
                    'processing_time': '14-21 working days'
                },
                'national_id': {
                    'office': 'NIRA Registration Center',
                    'address': 'NIRA House, Plot 10, Kampala Road, Kampala',
                    'hours': 'Monday - Friday: 8:00 AM - 5:00 PM',
                    'documents_required': [
                        'Completed application form',
                        'Birth certificate',
                        'Passport photos (2)',
                        'Proof of address'
                    ],
                    'fee': 'UGX 50,000',
                    'payment_methods': ['Cash', 'Bank transfer', 'Mobile money'],
                    'processing_time': '21-30 working days'
                },
                'tax_registration': {
                    'office': 'URA Tax Office',
                    'address': 'URA House, Plot 12, Nakasero Road, Kampala',
                    'hours': 'Monday - Friday: 8:00 AM - 5:00 PM',
                    'documents_required': [
                        'Completed registration form',
                        'Business license',
                        'Owner National ID (copy)',
                        'Bank account details'
                    ],
                    'fee': 'Free',
                    'payment_methods': ['N/A'],
                    'processing_time': '5-10 working days'
                }
            }
            
            if form_type in submission_info:
                return {
                    "status": "success",
                    "form_type": form_type,
                    "submission_info": submission_info[form_type]
                }
            else:
                return {
                    "status": "error",
                    "error": f"Submission info for '{form_type}' not found"
                }
                
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def track_form_status(reference_number: str, form_type: str, tool_context=None) -> dict:
        """Check application status after submission"""
        try:
            # In a real implementation, this would query the relevant government system
            # For now, we'll simulate status tracking
            
            status_options = ["Received", "Under Review", "Approved", "Ready for Collection", "Completed"]
            
            # Simulate status based on reference number
            import hashlib
            hash_val = int(hashlib.md5(reference_number.encode()).hexdigest()[:8], 16)
            status_index = hash_val % len(status_options)
            current_status = status_options[status_index]
            
            tracking_info = {
                "reference_number": reference_number,
                "form_type": form_type,
                "current_status": current_status,
                "submission_date": "2024-01-01",
                "last_updated": "2024-01-15",
                "estimated_completion": "2024-01-30",
                "next_steps": _get_next_steps(current_status, form_type)
            }
            
            return {
                "status": "success",
                "tracking_info": tracking_info
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    # Helper functions
    def _validate_date_format(date_str: str) -> bool:
        """Validate DD/MM/YYYY date format"""
        try:
            from datetime import datetime
            datetime.strptime(date_str, "%d/%m/%Y")
            return True
        except ValueError:
            return False
    
    def _validate_uganda_phone(phone: str) -> bool:
        """Validate Uganda phone number format"""
        import re
        # Uganda phone patterns: +256XXXXXXXXX or 0XXXXXXXXX
        pattern = r'^(\+256|0)[7-9]\d{8}$'
        return bool(re.match(pattern, phone))
    
    def _get_next_steps(status: str, form_type: str) -> str:
        """Get next steps based on current status"""
        next_steps = {
            "Received": "Your application is being processed. Please wait for further updates.",
            "Under Review": "Your application is under review. Additional documents may be requested.",
            "Approved": "Your application has been approved. Processing is in progress.",
            "Ready for Collection": "Your document is ready for collection. Please visit the office with your ID.",
            "Completed": "Your application has been completed successfully."
        }
        return next_steps.get(status, "Please contact the office for more information.")
    
    # Create function tools
    form_tools = [
        FunctionTool(get_form_template),
        FunctionTool(fill_form_data),
        FunctionTool(validate_form_data),
        FunctionTool(generate_pdf_form),
        FunctionTool(get_submission_instructions),
        FunctionTool(track_form_status),
        browser_tools,
        portal_tools,
    ]
    
    logger.info(f"Created {len(form_tools)} form processing tools")
    return form_tools

# Import time for timestamp generation
import time