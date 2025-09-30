"""
Enhanced Chat Assistant Agent with Ollama LLM Integration
"""

import logging
from typing import Dict, Any, List
from .base_agent import BaseAgent, AgentError

logger = logging.getLogger(__name__)

class ChatAssistantAgent(BaseAgent):
    """LLM-powered interactive chat agent"""
    
    def __init__(self):
        super().__init__("chat_assistant")
        
        self.uae_context = """
        You are a helpful assistant for the UAE Social Support AI System.
        You help applicants with:
        - Eligibility criteria for UAE social support programs
        - Document requirements (Emirates ID, bank statements, salary certificates)
        - Application process and status inquiries
        - Training and career development opportunities
        - UAE-specific information by emirate
        
        Be helpful, accurate, and culturally sensitive to UAE context.
        Provide specific, actionable guidance.
        """
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process chat interaction with LLM enhancement"""
        try:
            message = input_data.get("message", "")
            context = input_data.get("context", {})
            
            if not message:
                return {
                    "success": False,
                    "error": "No message provided"
                }
            
            # Enhanced prompt with context
            enhanced_prompt = f"""
            User Question: {message}
            
            Application Context: {context if context else 'No specific application context'}
            
            Provide a helpful, specific response about UAE social support services.
            Include relevant next steps or suggestions.
            """
            
            # Get LLM response
            if self.llm_client and getattr(self.llm_client, "available", False):
                response = await self.llm_analyze(
                    enhanced_prompt, 
                    self.uae_context
                )
                
                # Classify intent using LLM
                intent_prompt = f"Classify this user message into one category: document_help, status_inquiry, eligibility_question, training_inquiry, amount_inquiry, or general_help. Message: {message}"
                intent = await self.llm_analyze(intent_prompt, "Respond with just the category name.")
                
            else:
                # Fallback to rule-based
                response = self._generate_rule_based_response(message, context)
                intent = self._classify_intent_rule_based(message)
            
            # Generate suggested actions
            suggested_actions = self._get_suggested_actions(intent, context)
            
            result = {
                "success": True,
                "intent": intent.strip().lower() if isinstance(intent, str) else "general_help",
                "response": response,
                "suggested_actions": suggested_actions,
                "llm_powered": self.llm_client is not None
            }
            
            await self.log_processing(input_data, result, success=True)
            return result
            
        except Exception as e:
            error_msg = f"Chat processing failed: {str(e)}"
            await self.log_processing(input_data, {}, success=False, error_message=error_msg)
            raise AgentError(error_msg)
    
    def _generate_rule_based_response(self, message: str, context: Dict) -> str:
        """Fallback rule-based response generation"""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ["document", "upload", "file", "paper"]):
            return "For UAE applications, you'll need: Emirates ID (clear photo), recent bank statements (3 months), salary certificate from employer, and assets/liabilities documentation if applicable."
        
        elif any(word in message_lower for word in ["eligible", "qualify", "criteria"]):
            return "UAE eligibility depends on: monthly income relative to your emirate's thresholds, family size and dependents, employment status, and residency type. Dubai residents need income below 15,000 AED for medium support."
        
        elif any(word in message_lower for word in ["training", "course", "skill"]):
            return "Available training programs include: Digital Marketing Certificate (Dubai Future Academy), Healthcare Administration (UAE Health Authority), Banking Excellence (Emirates Institute), and Data Analysis Bootcamp (ADEK Training)."
        
        elif any(word in message_lower for word in ["amount", "money", "aed", "financial"]):
            return "Support amounts range from 5,000 to 50,000 AED based on assessment scores. Higher family size and lower income typically qualify for higher amounts. Duration is usually 6 months."
        
        else:
            return "I'm here to help with your UAE social support application. You can ask about eligibility, documents, training programs, or check your application status."
    
    def _classify_intent_rule_based(self, message: str) -> str:
        """Rule-based intent classification"""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ["document", "upload", "file"]):
            return "document_help"
        elif any(word in message_lower for word in ["status", "progress"]):
            return "status_inquiry"  
        elif any(word in message_lower for word in ["eligible", "qualify"]):
            return "eligibility_question"
        elif any(word in message_lower for word in ["training", "course"]):
            return "training_inquiry"
        elif any(word in message_lower for word in ["amount", "money"]):
            return "amount_inquiry"
        else:
            return "general_help"
    
    def _get_suggested_actions(self, intent: str, context: Dict) -> List[str]:
        """Generate contextual suggested actions"""
        
        base_actions = {
            "document_help": ["View document checklist", "Upload documents", "Check document status"],
            "status_inquiry": ["View application details", "Check processing timeline", "Contact case worker"],
            "eligibility_question": ["Check eligibility calculator", "View criteria by emirate", "Submit application"],
            "training_inquiry": ["Browse training programs", "Check course availability", "Apply for courses"],
            "amount_inquiry": ["Use support calculator", "View amount guidelines", "Check eligibility"],
            "general_help": ["Submit new application", "Check application status", "View help guide"]
        }
        
        return base_actions.get(intent, base_actions["general_help"])