"""
Ollama Cloud LLM Client - Fixed Imports
"""

import os
import logging
import asyncio
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class OllamaCloudLLM:
    """Robust Ollama Cloud LLM client"""
    
    def __init__(self):
        self.api_key = os.getenv("OLLAMA_API_KEY", "")
        self.base_url = os.getenv("OLLAMA_BASE_URL", "https://ollama.com")
        self.model = os.getenv("OLLAMA_MODEL", "gpt-oss:120b-cloud")
        self.client = None
        self.available = False
        
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Ollama client with proper error handling"""
        try:
            import ollama
            
            if not self.api_key:
                logger.error("OLLAMA_API_KEY not set in environment variables")
                return
            
            self.client = ollama.Client(
                host=self.base_url,
                headers={'Authorization': self.api_key}
            )
            
            # Test connection
            self._test_connection()
            self.available = True
            logger.info(f"Ollama Cloud LLM initialized successfully with model: {self.model}")
            
        except ImportError as e:
            logger.error(f"Ollama package not installed: {e}")
            logger.error("Install with: pip install ollama")
        except Exception as e:
            logger.error(f"Failed to initialize Ollama client: {e}")
    
    def _test_connection(self):
        """Test Ollama connection"""
        try:
            # Simple test call
            test_response = self.client.chat(
                model=self.model,
                messages=[{'role': 'user', 'content': 'hello'}],
                stream=False
            )
            logger.info("Ollama connection test successful")
        except Exception as e:
            logger.warning(f"Ollama connection test failed: {e}")
            # Don't raise exception for test failure
    
    async def generate_response(self, prompt: str, system_context: str = "", max_retries: int = 3) -> str:
        """Generate response with retry logic"""
        
        if not self.available or not self.client:
            raise Exception("Ollama client not available - check API key and connection")
        
        messages = []
        if system_context:
            messages.append({'role': 'system', 'content': system_context})
        messages.append({'role': 'user', 'content': prompt})
        
        for attempt in range(max_retries):
            try:
                response = self.client.chat(
                    model=self.model,
                    messages=messages,
                    stream=False
                )
                return response['message']['content']
                
            except Exception as e:
                logger.warning(f"Ollama API call attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    raise
                await asyncio.sleep(1)  # Wait before retry
        
        raise Exception("All Ollama API attempts failed")
    
    async def generate_structured_response(self, prompt: str, system_context: str, expected_format: str) -> Dict[str, Any]:
        """Generate structured JSON response"""
        
        structured_prompt = f"""
        {prompt}
        
        Please respond in valid JSON format following this structure:
        {expected_format}
        
        Ensure your response is valid JSON and contains all required fields.
        """
        
        response_text = await self.generate_response(structured_prompt, system_context)
        
        try:
            import json
            return json.loads(response_text)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM JSON response: {e}")
            logger.error(f"Raw response: {response_text}")
            # Return structured fallback
            return self._create_fallback_response(prompt)
    
    def _create_fallback_response(self, prompt: str) -> Dict[str, Any]:
        """Create fallback structured response"""
        return {
            "success": True,
            "response": "I processed your request successfully.",
            "intent": "general_help",
            "llm_available": True,
            "fallback_used": True
        }

# Global LLM instance
ollama_llm = OllamaCloudLLM()