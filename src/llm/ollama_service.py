"""
Autonomous Multi-Agent Business Intelligence System - Ollama Service

Local LLM service using Ollama for fast, cost-free inference.
Optimized for 8GB RAM systems.
"""

import logging
from typing import Dict, Any, Optional, Generator
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from ..config import settings

logger = logging.getLogger(__name__)


class OllamaService:
    """
    Ollama LLM service for local inference.
    
    Supports:
    - Text generation
    - Streaming responses
    - Model management
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: float = 120.0
    ):
        """
        Initialize Ollama service.
        
        Args:
            base_url: Ollama API URL (default from settings)
            model: Model name (default from settings)
            timeout: Request timeout in seconds
        """
        self.base_url = base_url or settings.ollama_base_url
        self.model = model or settings.ollama_model
        self.timeout = timeout
        self._client = httpx.Client(timeout=timeout)
        self._async_client = httpx.AsyncClient(timeout=timeout)

    def is_available(self) -> bool:
        """
        Check if Ollama service is available.
        
        Returns:
            bool: True if Ollama is running and responsive
        """
        try:
            response = self._client.get(f"{self.base_url}/api/tags")
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"Ollama not available: {e}")
            return False

    def list_models(self) -> list:
        """
        List available models.
        
        Returns:
            list: Available model names
        """
        try:
            response = self._client.get(f"{self.base_url}/api/tags")
            if response.status_code == 200:
                data = response.json()
                return [m["name"] for m in data.get("models", [])]
        except Exception as e:
            logger.error(f"Failed to list models: {e}")
        return []

    def model_exists(self, model_name: Optional[str] = None) -> bool:
        """
        Check if a specific model is available.
        
        Args:
            model_name: Model to check (default: configured model)
            
        Returns:
            bool: True if model is available
        """
        model = model_name or self.model
        models = self.list_models()
        return any(model in m for m in models)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10)
    )
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate text using Ollama.
        
        Args:
            prompt: User prompt
            system_prompt: System instructions
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0-1)
            **kwargs: Additional Ollama parameters
            
        Returns:
            Dict with 'content', 'model', 'tokens', 'done'
        """
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_predict": max_tokens,
                "temperature": temperature,
                "num_ctx": settings.ollama_num_ctx,
                "num_gpu": settings.ollama_num_gpu,
                **kwargs.get("options", {})
            }
        }

        if system_prompt:
            payload["system"] = system_prompt

        logger.debug(f"Ollama request: model={self.model}, prompt_len={len(prompt)}")

        try:
            response = self._client.post(
                f"{self.base_url}/api/generate",
                json=payload
            )
            response.raise_for_status()
            data = response.json()

            result = {
                "content": data.get("response", ""),
                "model": data.get("model", self.model),
                "tokens": data.get("eval_count", 0),
                "done": data.get("done", True),
                "total_duration": data.get("total_duration", 0),
                "provider": "ollama"
            }

            logger.info(f"Ollama response: tokens={result['tokens']}")
            return result

        except httpx.HTTPStatusError as e:
            logger.error(f"Ollama HTTP error: {e}")
            raise
        except Exception as e:
            logger.error(f"Ollama generation error: {e}")
            raise

    def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        **kwargs
    ) -> Generator[str, None, None]:
        """
        Generate text with streaming response.
        
        Args:
            prompt: User prompt
            system_prompt: System instructions
            max_tokens: Maximum tokens
            temperature: Sampling temperature
            
        Yields:
            str: Token chunks as they're generated
        """
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": True,
            "options": {
                "num_predict": max_tokens,
                "temperature": temperature,
                "num_ctx": settings.ollama_num_ctx,
                "num_gpu": settings.ollama_num_gpu,
            }
        }

        if system_prompt:
            payload["system"] = system_prompt

        try:
            with self._client.stream(
                "POST",
                f"{self.base_url}/api/generate",
                json=payload
            ) as response:
                for line in response.iter_lines():
                    if line:
                        import json
                        data = json.loads(line)
                        if "response" in data:
                            yield data["response"]
                        if data.get("done", False):
                            break
        except Exception as e:
            logger.error(f"Ollama streaming error: {e}")
            raise

    async def generate_async(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Async text generation.
        
        Args:
            prompt: User prompt
            system_prompt: System instructions
            max_tokens: Maximum tokens
            temperature: Sampling temperature
            
        Returns:
            Dict with generation results
        """
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_predict": max_tokens,
                "temperature": temperature,
                "num_ctx": settings.ollama_num_ctx,
                "num_gpu": settings.ollama_num_gpu,
            }
        }

        if system_prompt:
            payload["system"] = system_prompt

        try:
            response = await self._async_client.post(
                f"{self.base_url}/api/generate",
                json=payload
            )
            response.raise_for_status()
            data = response.json()

            return {
                "content": data.get("response", ""),
                "model": data.get("model", self.model),
                "tokens": data.get("eval_count", 0),
                "done": data.get("done", True),
                "provider": "ollama"
            }
        except Exception as e:
            logger.error(f"Ollama async error: {e}")
            raise

    def chat(
        self,
        messages: list,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Chat completion with message history.
        
        Args:
            messages: List of {role, content} messages
            max_tokens: Maximum tokens
            temperature: Sampling temperature
            
        Returns:
            Dict with assistant response
        """
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "num_predict": max_tokens,
                "temperature": temperature,
                "num_ctx": settings.ollama_num_ctx,
                "num_gpu": settings.ollama_num_gpu,
            }
        }

        try:
            response = self._client.post(
                f"{self.base_url}/api/chat",
                json=payload
            )
            response.raise_for_status()
            data = response.json()

            return {
                "content": data.get("message", {}).get("content", ""),
                "model": data.get("model", self.model),
                "tokens": data.get("eval_count", 0),
                "done": data.get("done", True),
                "provider": "ollama"
            }
        except Exception as e:
            logger.error(f"Ollama chat error: {e}")
            raise

    def pull_model(self, model_name: Optional[str] = None) -> bool:
        """
        Pull/download a model.
        
        Args:
            model_name: Model to pull (default: configured model)
            
        Returns:
            bool: True if successful
        """
        model = model_name or self.model
        logger.info(f"Pulling model: {model}")

        try:
            response = self._client.post(
                f"{self.base_url}/api/pull",
                json={"name": model},
                timeout=600  # 10 minute timeout for download
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Failed to pull model: {e}")
            return False

    def __del__(self):
        """Cleanup HTTP clients."""
        try:
            self._client.close()
        except:
            pass
