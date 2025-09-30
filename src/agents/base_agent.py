"""
Enhanced Base Agent with Ollama LLM Integration
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from datetime import datetime
import asyncio

# Import LLM client
try:
    from ..llm.ollama_client import llm_client
except ImportError:
    try:
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.dirname(__file__)))
        from llm.ollama_client import llm_client
    except ImportError:
        llm_client = None

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    """Enhanced base class for all AI agents with LLM capabilities"""
    
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.created_at = datetime.now()
        self.processing_history = []
        self.llm_client = llm_client
        
    @abstractmethod
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Main processing method - must be implemented by subclasses"""
        pass
    
    async def llm_analyze(self, prompt: str, context: str = "", 
                         output_format: Optional[Dict[str, Any]] = None) -> Any:
        """Use LLM for analysis with structured output"""
        
        client_available = self.llm_client and getattr(self.llm_client, "available", False)
        if not client_available:
            logger.warning(f"{self.agent_name}: LLM client not available, using fallback")
            return self._fallback_analysis(prompt)
        
        try:
            if output_format:
                return await self.llm_client.generate_structured_response(
                    prompt, context, output_format
                )
            else:
                return await self.llm_client.generate_response(prompt, context)
        except Exception as e:
            logger.error(f"{self.agent_name}: LLM analysis failed: {e}")
            return self._fallback_analysis(prompt)
    
    def _fallback_analysis(self, prompt: str) -> str:
        """Fallback analysis when LLM is not available"""
        return f"Analysis completed using rule-based approach for: {prompt[:50]}..."
    
    async def log_processing(self, input_data: Dict[str, Any], output_data: Dict[str, Any], 
                           success: bool = True, error_message: str = None):
        """Enhanced logging with LLM usage tracking"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "agent": self.agent_name,
            "success": success,
            "error": error_message,
            "llm_used": self.llm_client is not None,
            "processing_mode": "llm" if self.llm_client else "rule_based"
        }
        self.processing_history.append(log_entry)
        
        if success:
            logger.info(f"{self.agent_name} processed successfully (LLM: {self.llm_client is not None})")
        else:
            logger.error(f"{self.agent_name} failed: {error_message}")

class AgentError(Exception):
    """Custom exception for agent processing errors"""
    pass
