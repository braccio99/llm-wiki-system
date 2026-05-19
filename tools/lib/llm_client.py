"""LLM client factory — returns the right client based on config.yaml provider setting.

Supported providers:
  anthropic        → Claude API (with prompt caching). Needs ANTHROPIC_API_KEY.
  ollama           → Local Ollama  (http://localhost:11434). No key needed.
  lmstudio         → Local LM Studio (http://localhost:1234). No key needed.
  vllm             → Local/remote vLLM (http://localhost:8000). No key needed locally.
  openai           → OpenAI API. Needs OPENAI_API_KEY or LLM_API_KEY.
  openai-compatible → Any OpenAI-compatible API. Set llm.base_url in config.yaml.
"""

from typing import Union
from .claude_client import ClaudeClient
from .openai_compat_client import OpenAICompatClient


def get_llm_client(config: dict) -> Union[ClaudeClient, OpenAICompatClient]:
    """
    Factory function. Pass the full parsed config.yaml dict.

    Returns a client with the interface:
      .chat(user_message, system=None, **kwargs) -> str
      .chat_with_context(user_message, context_documents, system=None, **kwargs) -> str
      .get_stats() -> dict
      .reset_stats()
    """
    llm_cfg = config.get("llm", {})
    provider = llm_cfg.get("provider", "anthropic").lower()
    model = llm_cfg.get("model", "")
    temperature = llm_cfg.get("temperature", 0.7)
    max_tokens = llm_cfg.get("max_tokens", 4096)

    if provider == "anthropic":
        return ClaudeClient(model=model)

    # All other providers share the OpenAI-compatible client
    return OpenAICompatClient(
        model=model,
        provider=provider,
        base_url=llm_cfg.get("base_url"),
        api_key=llm_cfg.get("api_key"),
    )
