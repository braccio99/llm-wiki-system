"""OpenAI-compatible client — works with Ollama, LM Studio, vLLM, OpenAI, and any OpenAI-API provider"""

import os
import time
import logging
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

# Default base URLs per provider
PROVIDER_DEFAULTS: Dict[str, Dict[str, str]] = {
    "ollama":            {"base_url": "http://localhost:11434/v1", "api_key": "ollama"},
    "lmstudio":          {"base_url": "http://localhost:1234/v1",  "api_key": "lm-studio"},
    "vllm":              {"base_url": "http://localhost:8000/v1",  "api_key": "vllm"},
    "openai":            {"base_url": "https://api.openai.com/v1", "api_key": None},
    "openai-compatible": {"base_url": None,                        "api_key": None},
}


class OpenAICompatClient:
    """
    Unified client for any OpenAI-compatible API.

    Supports: Ollama, LM Studio, vLLM, OpenAI, Groq, Together AI, Mistral, etc.
    Same interface as ClaudeClient — drop-in replacement.
    """

    def __init__(
        self,
        model: str,
        provider: str = "openai-compatible",
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
    ):
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError(
                "openai package required for non-Anthropic providers.\n"
                "Install with: pip install openai"
            )

        self.model = model
        self.provider = provider

        # Resolve base_url: explicit > config > provider default > env
        defaults = PROVIDER_DEFAULTS.get(provider, PROVIDER_DEFAULTS["openai-compatible"])
        resolved_base_url = (
            base_url
            or os.environ.get("LLM_BASE_URL")
            or defaults.get("base_url")
        )
        if not resolved_base_url:
            raise ValueError(
                f"base_url required for provider '{provider}'. "
                "Set it in config.yaml (llm.base_url) or env LLM_BASE_URL."
            )

        # Resolve api_key: explicit > env vars > provider default (dummy key for local)
        resolved_api_key = (
            api_key
            or os.environ.get("LLM_API_KEY")
            or os.environ.get("OPENAI_API_KEY")
            or defaults.get("api_key")
            or "not-needed"  # local providers ignore this
        )

        self.client = OpenAI(base_url=resolved_base_url, api_key=resolved_api_key)
        self.stats = {"input_tokens": 0, "output_tokens": 0}

        logger.debug(f"OpenAICompatClient init: provider={provider}, base_url={resolved_base_url}, model={model}")

    def _make_request(
        self,
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        retries: int = 3,
        **_kwargs,  # absorb unsupported kwargs like use_cache
    ) -> str:
        if system:
            messages = [{"role": "system", "content": system}] + messages

        for attempt in range(retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                )
                if response.usage:
                    self.stats["input_tokens"] += response.usage.prompt_tokens or 0
                    self.stats["output_tokens"] += response.usage.completion_tokens or 0

                return response.choices[0].message.content or ""

            except Exception as e:
                err = str(e).lower()
                # Retry on rate limit or transient errors
                if any(kw in err for kw in ("rate", "timeout", "connect", "502", "503", "529")):
                    wait = min(2 ** attempt, 30)
                    if attempt < retries - 1:
                        logger.warning(f"Request error ({e}), retrying in {wait}s ({attempt+1}/{retries})")
                        time.sleep(wait)
                        continue
                raise

        raise RuntimeError(f"Request failed after {retries} retries")

    def chat(self, user_message: str, system: Optional[str] = None, **kwargs) -> str:
        messages = [{"role": "user", "content": user_message}]
        return self._make_request(messages, system=system, **kwargs)

    def chat_with_context(
        self,
        user_message: str,
        context_documents: List[str],
        system: Optional[str] = None,
        **kwargs,
    ) -> str:
        context_str = "\n\n---\n\n".join(context_documents)
        full_message = f"Context documents:\n\n{context_str}\n\n---\n\nQuestion: {user_message}"
        return self.chat(full_message, system=system, **kwargs)

    def get_stats(self) -> Dict[str, int]:
        return self.stats.copy()

    def reset_stats(self):
        self.stats = {"input_tokens": 0, "output_tokens": 0}
