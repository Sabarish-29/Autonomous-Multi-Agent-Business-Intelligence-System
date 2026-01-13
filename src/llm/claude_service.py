"""
Autonomous Multi-Agent Business Intelligence System - Claude Service

Cloud LLM service using Anthropic's Claude API.
Used for complex queries requiring higher reasoning capability.
"""

import logging
from typing import Dict, Any, Optional, List, Generator
from tenacity import retry, stop_after_attempt, wait_exponential

from ..config import settings

logger = logging.getLogger(__name__)


class ClaudeService:
    """
    Claude API service for cloud inference.
    
    Features:
    - High-quality text generation
    - Complex reasoning tasks
    - Context-aware responses
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        max_retries: int = 3
    ):
        """
        Initialize Claude service.
        
        Args:
            api_key: Anthropic API key (default from settings)
            model: Claude model name (default from settings)
            max_retries: Maximum retry attempts
        """
        self.api_key = api_key or settings.anthropic_api_key
        self.model = model or settings.anthropic_model
        self.max_retries = max_retries
        self._client = None

        if self.api_key:
            self._initialize_client()

    def _initialize_client(self):
        """Initialize the Anthropic client."""
        try:
            import anthropic
            self._client = anthropic.Anthropic(api_key=self.api_key)
            logger.info(f"Claude client initialized with model: {self.model}")
        except ImportError:
            logger.error("anthropic package not installed. Run: pip install anthropic")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize Claude client: {e}")
            raise

    def is_available(self) -> bool:
        """
        Check if Claude service is available.
        
        Returns:
            bool: True if API key is configured and valid
        """
        if not self._client:
            return False
        
        try:
            # Test with minimal request
            response = self._client.messages.create(
                model=self.model,
                max_tokens=10,
                messages=[{"role": "user", "content": "test"}]
            )
            return True
        except Exception as e:
            logger.warning(f"Claude not available: {e}")
            return False

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10)
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
        Generate text using Claude.
        
        Args:
            prompt: User prompt
            system_prompt: System instructions
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0-1)
            **kwargs: Additional parameters
            
        Returns:
            Dict with 'content', 'model', 'tokens', 'cost'
        """
        if not self._client:
            raise RuntimeError("Claude client not initialized. Check API key.")

        messages = [{"role": "user", "content": prompt}]
        
        request_params = {
            "model": self.model,
            "max_tokens": max_tokens,
            "messages": messages,
            "temperature": temperature,
        }

        if system_prompt:
            request_params["system"] = system_prompt

        logger.debug(f"Claude request: model={self.model}, prompt_len={len(prompt)}")

        try:
            response = self._client.messages.create(**request_params)

            # Extract content from response
            content = ""
            for block in response.content:
                if hasattr(block, "text"):
                    content += block.text

            # Calculate cost (approximate)
            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens
            cost = self._calculate_cost(input_tokens, output_tokens)

            result = {
                "content": content,
                "model": response.model,
                "tokens": input_tokens + output_tokens,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cost": cost,
                "stop_reason": response.stop_reason,
                "provider": "claude"
            }

            logger.info(
                f"Claude response: tokens={result['tokens']}, cost=${cost:.4f}"
            )
            return result

        except Exception as e:
            logger.error(f"Claude generation error: {e}")
            raise

    def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 2000,
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
        if not self._client:
            raise RuntimeError("Claude client not initialized")

        messages = [{"role": "user", "content": prompt}]

        try:
            with self._client.messages.stream(
                model=self.model,
                max_tokens=max_tokens,
                messages=messages,
                system=system_prompt or "",
                temperature=temperature
            ) as stream:
                for text in stream.text_stream:
                    yield text
        except Exception as e:
            logger.error(f"Claude streaming error: {e}")
            raise

    async def generate_async(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 2000,
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
        if not self.api_key:
            raise RuntimeError("Claude API key not configured")

        import anthropic
        async_client = anthropic.AsyncAnthropic(api_key=self.api_key)

        messages = [{"role": "user", "content": prompt}]

        try:
            response = await async_client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                messages=messages,
                system=system_prompt or "",
                temperature=temperature
            )

            content = ""
            for block in response.content:
                if hasattr(block, "text"):
                    content += block.text

            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens
            cost = self._calculate_cost(input_tokens, output_tokens)

            return {
                "content": content,
                "model": response.model,
                "tokens": input_tokens + output_tokens,
                "cost": cost,
                "provider": "claude"
            }
        except Exception as e:
            logger.error(f"Claude async error: {e}")
            raise
        finally:
            await async_client.close()

    def chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        max_tokens: int = 2000,
        temperature: float = 0.7,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Multi-turn chat completion.
        
        Args:
            messages: List of {role, content} messages
            system_prompt: System instructions
            max_tokens: Maximum tokens
            temperature: Sampling temperature
            
        Returns:
            Dict with assistant response
        """
        if not self._client:
            raise RuntimeError("Claude client not initialized")

        try:
            response = self._client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                messages=messages,
                system=system_prompt or "",
                temperature=temperature
            )

            content = ""
            for block in response.content:
                if hasattr(block, "text"):
                    content += block.text

            return {
                "content": content,
                "model": response.model,
                "tokens": response.usage.input_tokens + response.usage.output_tokens,
                "cost": self._calculate_cost(
                    response.usage.input_tokens,
                    response.usage.output_tokens
                ),
                "provider": "claude"
            }
        except Exception as e:
            logger.error(f"Claude chat error: {e}")
            raise

    def _calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """
        Calculate approximate cost for Claude API usage.
        
        Pricing (as of 2024):
        - Claude Sonnet: $3/1M input, $15/1M output
        - Claude Opus: $15/1M input, $75/1M output
        - Claude Haiku: $0.25/1M input, $1.25/1M output
        
        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            
        Returns:
            float: Estimated cost in USD
        """
        # Default to Sonnet pricing
        if "opus" in self.model.lower():
            input_cost = 15.0 / 1_000_000
            output_cost = 75.0 / 1_000_000
        elif "haiku" in self.model.lower():
            input_cost = 0.25 / 1_000_000
            output_cost = 1.25 / 1_000_000
        else:  # Sonnet
            input_cost = 3.0 / 1_000_000
            output_cost = 15.0 / 1_000_000

        return (input_tokens * input_cost) + (output_tokens * output_cost)

    def count_tokens(self, text: str) -> int:
        """
        Estimate token count for text.
        
        Args:
            text: Input text
            
        Returns:
            int: Estimated token count
        """
        # Rough estimation: 1 token ≈ 4 characters for English
        return len(text) // 4
