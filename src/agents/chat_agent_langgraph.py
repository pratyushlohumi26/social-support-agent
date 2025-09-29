"""
LangGraph-based Chat Agent for UAE Social Support - Fixed Imports
"""

import logging
import sys
import os
from typing import Dict, Any, List, TypedDict
from datetime import datetime
import json

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

logger = logging.getLogger(__name__)

# Import dependencies with proper error handling
try:
    from langgraph.graph import StateGraph, END
    from langgraph.checkpoint.memory import MemorySaver
    LANGGRAPH_AVAILABLE = True
    logger.info("LangGraph imported successfully")
except ImportError as e:
    logger.error(f"LangGraph import failed: {e}")
    LANGGRAPH_AVAILABLE = False

# Import Ollama client
try:
    # Try direct import first
    from llm.ollama_client import ollama_llm
    OLLAMA_CLIENT_AVAILABLE = True
    logger.info("Ollama client imported successfully")
except ImportError:
    try:
        # Try absolute import
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
        from llm.ollama_client import ollama_llm
        OLLAMA_CLIENT_AVAILABLE = True
        logger.info("Ollama client imported with path adjustment")
    except ImportError as e:
        logger.error(f"Ollama client import failed: {e}")
        OLLAMA_CLIENT_AVAILABLE = False
        ollama_llm = None

class ChatState(TypedDict):
    """State for chat interactions"""
    message: str
    context: Dict[str, Any]
    response: str
    intent: str
    suggested_actions: List[str]
    processing_stage: str
    error: str

class UAEChatAgent:
    """LangGraph-powered chat agent for UAE Social Support"""
    
    def __init__(self):
        if not LANGGRAPH_AVAILABLE:
            raise ImportError("LangGraph not available. Install with: pip install langgraph")
        
        if not OLLAMA_CLIENT_AVAILABLE or not ollama_llm:
            raise Exception("Ollama client not available")
        
        if not ollama_llm.available:
            raise Exception("Ollama LLM not available - check API key and connection")
        
        self.agent_name = "uae_chat_agent"
        self.llm = ollama_llm
        
        # Build LangGraph workflow
        self.workflow = self._build_chat_workflow()
        self.memory = MemorySaver()
        
        logger.info("UAE Chat Agent with LangGraph initialized successfully")
    
    def _build_chat_workflow(self) -> StateGraph:
        """Build LangGraph workflow for chat processing"""
        
        workflow = StateGraph(ChatState)
        
        # Add nodes
        workflow.add_node("classify_intent", self._classify_intent_node)
        workflow.add_node("generate_response", self._generate_response_node)
        workflow.add_node("create_actions", self._create_actions_node)
        
        # Add edges
        workflow.set_entry_point("classify_intent")
        workflow.add_edge("classify_intent", "generate_response")
        workflow.add_edge("generate_response", "create_actions")
        workflow.add_edge("create_actions", END)
        
        return workflow.compile(checkpointer=self.memory)
    
    async def _classify_intent_node(self, state: ChatState) -> ChatState:
        """Classify user intent using LLM"""
        
        try:
            message = state["message"]
            
            intent_prompt = f"""
            Classify this UAE social support user message into ONE of these categories:
            - document_help
            - eligibility_question  
            - application_process
            - training_programs
            - support_amounts
            - status_inquiry
            - general_help
            
            User message: "{message}"
            
            Respond with just the category name.
            """
            
            intent = await self.llm.generate_response(
                intent_prompt,
                "You are a classification system. Respond with only the category name."
            )
            
            state["intent"] = intent.strip().lower()
            state["processing_stage"] = "intent_classified"
            logger.info(f"Intent classified: {state['intent']}")
            
        except Exception as e:
            logger.error(f"Intent classification failed: {e}")
            state["intent"] = "general_help"
            state["error"] = str(e)
        
        return state
    
    async def _generate_response_node(self, state: ChatState) -> ChatState:
        """Generate contextual response using LLM"""
        
        try:
            message = state["message"]
            intent = state.get("intent", "general_help")
            context = state.get("context", {})
            
            # UAE-specific context
            uae_context = """
            You are a helpful UAE Social Support AI assistant.
            
            Provide specific, actionable guidance about:
            - UAE income thresholds by emirate
            - Required documents (Emirates ID, bank statements)
            - Application processes and timelines
            - Training programs and career development
            - Cultural sensitivity for UAE residents
            
            Be conversational, supportive, and specific to UAE context.
            """
            
            response_prompt = f"""
            User Intent: {intent}
            User Message: "{message}"
            Context: {json.dumps(context) if context else "None"}
            
            Provide a helpful, detailed response addressing their question with UAE-specific information.
            """
            
            response = await self.llm.generate_response(response_prompt, uae_context)
            
            state["response"] = response
            state["processing_stage"] = "response_generated"
            logger.info("Response generated successfully")
            
        except Exception as e:
            logger.error(f"Response generation failed: {e}")
            state["response"] = self._get_fallback_response(state.get("intent", "general_help"), state["message"])
            state["error"] = str(e)
        
        return state
    
    async def _create_actions_node(self, state: ChatState) -> ChatState:
        """Create suggested actions"""
        
        try:
            intent = state.get("intent", "general_help")
            actions = self._get_suggested_actions(intent)
            
            state["suggested_actions"] = actions
            state["processing_stage"] = "completed"
            logger.info("Actions created successfully")
            
        except Exception as e:
            logger.error(f"Action creation failed: {e}")
            state["suggested_actions"] = ["Get help", "Try again", "Contact support"]
            state["error"] = str(e)
        
        return state
    
    def _get_fallback_response(self, intent: str, message: str) -> str:
        """Fallback responses when LLM fails"""
        
        responses = {
            "document_help": "For UAE applications, you need Emirates ID, bank statements (3 months), salary certificate, and family book. Ensure all documents are clear and recent.",
            
            "eligibility_question": "UAE eligibility depends on income level by emirate, family size, and employment status. Dubai: up to 25,000 AED/month, Abu Dhabi: 23,000 AED/month.",
            
            "application_process": "Apply online: 1) Check eligibility, 2) Gather documents, 3) Complete application form, 4) Submit for review. Processing takes 1-2 weeks.",
            
            "training_programs": "UAE offers Digital Marketing (3 months), Healthcare Administration (6 months), Banking Excellence (5 months), and other career programs.",
            
            "support_amounts": "Support ranges from 5,000-50,000 AED based on family size, income level, and needs. Duration typically 3-12 months.",
            
            "status_inquiry": "Check status via online portal, SMS notifications, or support hotline. Updates provided at each processing stage.",
            
            "general_help": "I help with UAE social support applications - eligibility, documents, process, training programs, and status updates. What do you need help with?"
        }
        
        return responses.get(intent, responses["general_help"])
    
    def _get_suggested_actions(self, intent: str) -> List[str]:
        """Get suggested actions based on intent"""
        
        action_map = {
            "document_help": ["📋 View document checklist", "📤 Upload documents", "📞 Contact support"],
            "eligibility_question": ["✅ Check eligibility", "🧮 Use calculator", "🚀 Start application"],
            "application_process": ["📝 Start application", "📖 Read guide", "🎥 Watch tutorial"],
            "training_programs": ["🎓 Browse programs", "📅 View schedules", "📞 Contact coordinator"],
            "support_amounts": ["🧮 Use calculator", "📊 View guidelines", "💰 Check limits"],
            "status_inquiry": ["🔍 Check status", "📱 Update info", "📞 Contact case worker"],
            "general_help": ["🚀 Submit application", "🔍 Check status", "💬 Get help"]
        }
        
        return action_map.get(intent, action_map["general_help"])
    
    async def process_chat(self, message: str, context: Dict[str, Any] = None, session_id: str = None) -> Dict[str, Any]:
        """Process chat message through LangGraph workflow"""
        
        try:
            # Initialize state
            initial_state = ChatState(
                message=message.strip(),
                context=context or {},
                response="",
                intent="",
                suggested_actions=[],
                processing_stage="started",
                error=""
            )
            
            # Configure workflow
            config = {
                "configurable": {
                    "thread_id": session_id or f"chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                }
            }
            
            # Execute workflow
            logger.info("Starting chat workflow execution")
            result = await self.workflow.ainvoke(initial_state, config)
            
            return {
                "success": True,
                "response": result["response"],
                "intent": result["intent"],
                "suggested_actions": result["suggested_actions"],
                "processing_stage": result["processing_stage"],
                "llm_powered": True,
                "langgraph_used": True,
                "timestamp": datetime.now().isoformat(),
                "error": result.get("error", "")
            }
            
        except Exception as e:
            logger.error(f"Chat processing workflow failed: {e}")
            return {
                "success": False,
                "response": f"I understand you're asking about: '{message}'. I'm experiencing technical issues right now, but I'm here to help with UAE social support applications. Please try rephrasing your question.",
                "intent": "error",
                "suggested_actions": [
                    "🔄 Try rephrasing question",
                    "📞 Contact support team",
                    "🌐 Visit support portal"
                ],
                "error": str(e),
                "llm_powered": True,
                "langgraph_used": True,
                "timestamp": datetime.now().isoformat()
            }

# Initialize chat agent
uae_chat_agent = None
try:
    uae_chat_agent = UAEChatAgent()
    logger.info("UAE Chat Agent initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize UAE Chat Agent: {e}")
    uae_chat_agent = None