"""
Autonomous Multi-Agent Business Intelligence System - Groq Service

Fast cloud LLM service using Groq's inference API.
Ultra-fast responses with competitive accuracy.
"""

import logging
from typing import Dict, Any, Optional
from tenacity import retry, stop_after_attempt, wait_exponential

from ..config import settings

logger = logging.getLogger(__name__)


class GroqService:
    """
    Groq API service for fast cloud inference.
    
    Features:
    - Ultra-fast inference (tokens/sec)
    - High-quality models (Llama, Mixtral)
    - Cost-effective
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        max_retries: int = 3
    ):
        """
        Initialize Groq service.
        
        Args:
            api_key: Groq API key (default from settings)
            model: Groq model name (default from settings)
            max_retries: Maximum retry attempts
        """
        self.api_key = api_key or getattr(settings, 'groq_api_key', None)
        self.model = model or getattr(settings, 'groq_model', 'llama-3.1-70b-versatile')
        self.max_retries = max_retries
        self._client = None

        if self.api_key:
            self._initialize_client()

    def _initialize_client(self):
        """Initialize the Groq client."""
        try:
            from groq import Groq
            self._client = Groq(api_key=self.api_key)
            logger.info(f"Groq client initialized with model: {self.model}")
        except ImportError:
            logger.error("groq package not installed. Run: pip install groq")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize Groq client: {e}")
            raise

    def is_available(self) -> bool:
        """
        Check if Groq service is available.
        
        Returns:
            bool: True if API key is configured
        """
        return self._client is not None

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True
    )
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 2000,
        temperature: float = 0.7,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate text using Groq.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system instructions
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0-1)
            **kwargs: Additional parameters
            
        Returns:
            Dict with 'content', 'model', 'tokens', 'cost'
        """
        if not self._client:
            raise RuntimeError("Groq client not initialized")

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        logger.debug(f"Groq request: model={self.model}, prompt_len={len(prompt)}")

        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                **kwargs
            )

            content = response.choices[0].message.content
            tokens = response.usage.total_tokens if hasattr(response, 'usage') else 0

            # Groq pricing (approximate)
            cost = self._estimate_cost(tokens)

            result = {
                "content": content,
                "model": self.model,
                "tokens": tokens,
                "cost": cost,
                "provider": "groq"
            }

            logger.info(f"Groq response: tokens={tokens}, cost=${cost:.4f}")
            return result

        except Exception as e:
            msg = str(e)
            if "Invalid API Key" in msg or "invalid_api_key" in msg:
                logger.error("Groq authentication failed: Invalid API key")
                raise RuntimeError("Invalid Groq API key. Please update GROQ_API_KEY in .env and restart.")
            logger.error(f"Groq generation error: {e}")
            raise

    def _estimate_cost(self, tokens: int) -> float:
        """
        Estimate cost based on tokens.
        
        Args:
            tokens: Total tokens used
            
        Returns:
            float: Estimated cost in USD
        """
        # Groq pricing (approximate, check current rates)
        # llama-3.1-70b-versatile: ~$0.59/1M input + $0.79/1M output
        cost_per_1k = 0.00069  # Average
        return (tokens / 1000) * cost_per_1k
