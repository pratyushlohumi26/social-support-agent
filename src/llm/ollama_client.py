"""
Ollama Cloud LLM client helpers used across the application.
"""

import asyncio
import json
import logging
import os
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class OllamaCloudLLM:
    """Wrapper around the Ollama Python client with async helpers."""

    def __init__(self) -> None:
        self.mode = os.getenv("OLLAMA_MODE", "cloud").lower()
        self.enabled = os.getenv("OLLAMA_ENABLED", "true").lower() == "true"
        self.api_key = os.getenv("OLLAMA_API_KEY", "")
        default_base = "http://localhost:11434" if self.mode == "offline" else "https://ollama.com"
        self.base_url = os.getenv("OLLAMA_BASE_URL", default_base)
        self.model = os.getenv("OLLAMA_MODEL", "gpt-oss:120b-cloud")
        self.client = None
        self.available = False
        self._initialize_client()

    def _initialize_client(self) -> None:
        """Initialise the underlying Ollama client if dependencies are present."""
        try:
            import ollama
        except ImportError as exc:
            logger.warning("ollama package not installed: %s", exc)
            return

        if not self.enabled:
            logger.info("Ollama client disabled via OLLAMA_ENABLED")
            return

        headers: Optional[Dict[str, str]] = None
        if self.mode == "cloud":
            if not self.api_key:
                logger.warning("OLLAMA_API_KEY not set; set it or switch to offline mode")
                return
            headers = {"Authorization": self.api_key}
        else:
            self.api_key = ""

        try:
            self.client = ollama.Client(host=self.base_url, headers=headers)
            self._test_connection()
            self.available = True
            logger.info("Ollama client initialised in %s mode with model %s", self.mode, self.model)
        except Exception as exc:
            logger.error("Failed to initialise Ollama client: %s", exc)
            self.client = None
            self.available = False

    def _chat(self, messages: list[dict[str, str]]) -> Any:
        """Blocking helper that executes a chat completion call."""
        if not self.client:
            raise RuntimeError("Ollama client is not configured")
        return self.client.chat(model=self.model, messages=messages, stream=False)

    def _test_connection(self) -> None:
        """Perform a best-effort connectivity check."""
        self._chat([{"role": "user", "content": "hello"}])

    async def generate_response(
        self,
        prompt: str,
        system_context: str = "",
        max_retries: int = 3,
        *,
        images: Optional[List[str]] = None,
    ) -> str:
        """Return the assistant message content for the given prompt."""

        if not self.available or not self.client:
            raise RuntimeError("Ollama client not available - configure credentials")

        messages: list[dict[str, Any]] = []
        if system_context:
            messages.append({"role": "system", "content": system_context})
        user_message: dict[str, Any] = {"role": "user", "content": prompt}
        if images:
            user_message["images"] = images
        messages.append(user_message)

        for attempt in range(max_retries):
            try:
                response = await asyncio.to_thread(self._chat, messages)
                return response["message"]["content"]
            except Exception as exc:
                logger.warning("Ollama API call attempt %s failed: %s", attempt + 1, exc)
                if attempt == max_retries - 1:
                    raise
                await asyncio.sleep(1)

        raise RuntimeError("Ollama API retries exhausted")

    async def generate_structured_response(
        self,
        prompt: str,
        system_context: str,
        expected_format: Any,
        *,
        images: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Request a JSON-formatted response and parse it into a dict."""

        structure_description = expected_format if isinstance(expected_format, str) else json.dumps(expected_format)
        structured_prompt = (
            f"{prompt}\n\n"
            "Respond in valid JSON following this structure:\n"
            f"{structure_description}\n"
            "Return only JSON with all required fields."
        )

        response_text = await self.generate_response(
            structured_prompt, system_context, images=images
        )

        try:
            return json.loads(response_text)
        except json.JSONDecodeError as exc:
            logger.error("Failed to parse LLM JSON response: %s", exc)
            logger.debug("Raw LLM response: %s", response_text)
            return self._create_fallback_response()

    async def _acall(
        self, prompt: str, system_context: str = "", *, images: Optional[List[str]] = None
    ) -> str:
        """Compatibility helper used by older LangGraph integrations."""
        return await self.generate_response(prompt, system_context, images=images)

    def _create_fallback_response(self) -> Dict[str, Any]:
        """Fallback payload returned when JSON parsing fails."""
        return {
            "success": False,
            "response": "Unable to produce structured output.",
            "fallback_used": True,
        }


ollama_llm = OllamaCloudLLM()
llm_client = ollama_llm
