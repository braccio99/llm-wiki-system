"""Claude API client wrapper with prompt caching support"""

import os
import json
import time
import logging
from typing import Optional, List, Dict, Any
import anthropic

logger = logging.getLogger(__name__)


class ClaudeClient:
    """Wrapper around Anthropic SDK with prompt caching and retry logic"""

    def __init__(self, model: str = "claude-haiku-4-5-20251001", api_key: Optional[str] = None):
        """Initialize Claude client

        Args:
            model: Model ID to use (default: haiku-4.5)
            api_key: Anthropic API key (reads from ANTHROPIC_API_KEY env if not provided)
        """
        self.model = model
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment")

        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.stats = {
            "input_tokens": 0,
            "output_tokens": 0,
            "cache_creation_input_tokens": 0,
            "cache_read_input_tokens": 0,
        }

    def _make_request(
        self,
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        use_cache: bool = True,
        retries: int = 3,
    ) -> str:
        """Make request to Claude with exponential backoff and prompt caching

        Args:
            messages: List of message dicts with 'role' and 'content'
            system: System prompt
            max_tokens: Max tokens in response
            temperature: Temperature for sampling
            use_cache: Whether to use prompt caching
            retries: Number of retries on failure

        Returns:
            Response text from Claude
        """
        for attempt in range(retries):
            try:
                kwargs = {
                    "model": self.model,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "messages": messages,
                }

                if system:
                    kwargs["system"] = system

                # Add prompt caching control
                if use_cache:
                    kwargs["system"] = [
                        {
                            "type": "text",
                            "text": system or "",
                            "cache_control": {"type": "ephemeral"}
                        }
                    ] if system else [{"type": "text", "text": "", "cache_control": {"type": "ephemeral"}}]

                response = self.client.messages.create(**kwargs)

                # Update token statistics
                self.stats["input_tokens"] += response.usage.input_tokens
                self.stats["output_tokens"] += response.usage.output_tokens
                if hasattr(response.usage, "cache_creation_input_tokens"):
                    self.stats["cache_creation_input_tokens"] += response.usage.cache_creation_input_tokens
                if hasattr(response.usage, "cache_read_input_tokens"):
                    self.stats["cache_read_input_tokens"] += response.usage.cache_read_input_tokens

                logger.debug(f"Response usage: input={response.usage.input_tokens}, output={response.usage.output_tokens}")

                return response.content[0].text

            except anthropic.RateLimitError as e:
                wait_time = min(2 ** attempt, 60)  # Exponential backoff, max 60s
                if attempt < retries - 1:
                    logger.warning(f"Rate limited, waiting {wait_time}s before retry {attempt + 1}/{retries}")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Rate limited after {retries} retries")
                    raise
            except anthropic.APIError as e:
                if attempt < retries - 1:
                    wait_time = min(2 ** attempt, 60)
                    logger.warning(f"API error: {e}, retrying in {wait_time}s ({attempt + 1}/{retries})")
                    time.sleep(wait_time)
                else:
                    raise

    def chat(
        self,
        user_message: str,
        system: Optional[str] = None,
        **kwargs
    ) -> str:
        """Send a chat message to Claude

        Args:
            user_message: User message text
            system: System prompt
            **kwargs: Additional arguments passed to _make_request (max_tokens, temperature, etc)

        Returns:
            Response text from Claude
        """
        messages = [{"role": "user", "content": user_message}]
        return self._make_request(messages, system=system, **kwargs)

    def chat_with_context(
        self,
        user_message: str,
        context_documents: List[str],
        system: Optional[str] = None,
        **kwargs
    ) -> str:
        """Send a chat message with context documents (benefits from prompt caching)

        Args:
            user_message: User question
            context_documents: List of document contents to provide as context
            system: System prompt
            **kwargs: Additional arguments passed to _make_request

        Returns:
            Response text from Claude
        """
        context_str = "\n\n---\n\n".join(context_documents)
        full_message = f"Context documents:\n\n{context_str}\n\n---\n\nQuestion: {user_message}"
        return self.chat(full_message, system=system, **kwargs)

    def get_stats(self) -> Dict[str, int]:
        """Get token usage statistics"""
        return self.stats.copy()

    def reset_stats(self):
        """Reset token usage statistics"""
        self.stats = {
            "input_tokens": 0,
            "output_tokens": 0,
            "cache_creation_input_tokens": 0,
            "cache_read_input_tokens": 0,
        }
