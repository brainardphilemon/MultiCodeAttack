# openai_log.py (sanitized / anonymized)

import os
import time
from typing import Dict, Any, Optional

from openai import OpenAI
from openai import (
    PermissionDeniedError,
    APIConnectionError,
    RateLimitError,
    AuthenticationError,
    BadRequestError,
    InternalServerError,
)

# -------------------------------
# Configuration via environment
# -------------------------------
# Primary endpoint (used by ask_response)
PRIMARY_MODEL = os.getenv("PRIMARY_MODEL", "Qwen2.5-3B-Instruct")
PRIMARY_BASE_URL = os.getenv("PRIMARY_BASE_URL", "http://localhost:8000/v1")
PRIMARY_API_KEY = os.getenv("PRIMARY_API_KEY", "EMPTY")

# Secondary endpoint (used by ask_custom_response)
SECONDARY_MODEL = os.getenv("SECONDARY_MODEL", "gpt-3.5-turbo")
SECONDARY_BASE_URL = os.getenv("SECONDARY_BASE_URL")
SECONDARY_API_KEY = os.getenv("SECONDARY_API_KEY")

# Generic options
DEFAULT_SLEEP_TIME = int(os.getenv("LLM_SLEEP_TIME", "3"))
MAX_RETRIES = int(os.getenv("LLM_MAX_RETRIES", "6"))

# For local/open models you can still route through an OpenAI-compatible server by setting env vars above.
# If you need per-model “thinking” toggles, register them here.
IS_THINKING_MODEL_BY_NAME = {
    # Hosted APIs
    "gpt-3.5-turbo": False,
    "gpt-4o": False,
    "gpt-4.5-preview": False,
    "claude-3-5-sonnet-20241022": False,
    "gemini-2.0-flash": False,
    "llama-2-70b": False,

    # Open models served behind an OpenAI-compatible endpoint
    "mlx-community/Qwen2.5-7B-Instruct-4bit": False,
    "Qwen2.5-7B-Instruct": False,
    "Qwen2.5-3B-Instruct": False,
    "Qwen2.5-Coder-7B-Instruct": False,
    "Qwen2.5-Coder-14B-Instruct": False,
    "Qwen3-8B": True,
    "Qwen3-14B": True,
    "Qwen3-32B": True,
    "Llama-3.1-8B-Instruct": False,
    "Deepseek-coder-7b": False,
    "DeepseekV2": False,
    "llama-2-13b": False,
}

def _build_client(api_key: Optional[str], base_url: Optional[str]) -> OpenAI:
    """
    Build an OpenAI client from provided credentials.
    Both api_key and base_url should come from environment variables.
    """
    if not api_key:
        raise AuthenticationError("Missing API key. Set PRIMARY_API_KEY / SECONDARY_API_KEY.")
    if not base_url:
        raise ValueError("Missing base URL. Set PRIMARY_BASE_URL / SECONDARY_BASE_URL.")
    return OpenAI(api_key=api_key, base_url=base_url)


def _chat_complete(
    client: OpenAI,
    model: str,
    system_content: str,
    user_content: str,
    enable_thinking: bool = False,
    max_tokens: int = 1024,
    temperature: float = 0.0,
    top_p: float = 1.0,
    sleep_time: int = DEFAULT_SLEEP_TIME,
    max_retries: int = MAX_RETRIES,
) -> Any:
    """
    Robust chat completion wrapper with exponential backoff.
    Returns the raw OpenAI response object.
    """
    attempt = 0
    last_err = None
    extra_body = {"chat_template_kwargs": {"enable_thinking": False}}
    if enable_thinking:
        # Only attach the flag if needed
        extra_body = {"chat_template_kwargs": {"enable_thinking": True}}

    while attempt < max_retries:
        try:
            return client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_content},
                    {"role": "user", "content": user_content},
                ],
                stream=False,
                logprobs=True,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                **({"extra_body": extra_body} if enable_thinking else {}),
            )
        except (APIConnectionError, InternalServerError) as e:
            # Transient server/network issues → backoff and retry
            last_err = e
        except RateLimitError as e:
            # Rate limits → backoff and retry
            last_err = e
        except (AuthenticationError, PermissionDeniedError, BadRequestError) as e:
            # Not retriable in general; surface immediately
            raise e

        # Exponential backoff
        delay = sleep_time * (2 ** attempt)
        time.sleep(delay)
        attempt += 1

    # Out of retries
    if last_err:
        raise last_err
    raise RuntimeError("Exhausted retries without receiving a response.")


def ask_response(system_content: str, user_content: str) -> Any:
    """
    Primary entry point. Uses PRIMARY_* env vars and PRIMARY_MODEL.
    """
    client = _build_client(PRIMARY_API_KEY, PRIMARY_BASE_URL)
    enable_thinking = IS_THINKING_MODEL_BY_NAME.get(PRIMARY_MODEL, False)
    return _chat_complete(
        client=client,
        model=PRIMARY_MODEL,
        system_content=system_content,
        user_content=user_content,
        enable_thinking=enable_thinking,
    )


def ask_custom_response(system_content: str, user_content: str) -> Any:
    """
    Secondary entry point. Uses SECONDARY_* env vars and SECONDARY_MODEL.
    Useful when you want to query a different model/provider for verification or adjudication.
    """
    client = _build_client(SECONDARY_API_KEY, SECONDARY_BASE_URL)
    enable_thinking = IS_THINKING_MODEL_BY_NAME.get(SECONDARY_MODEL, False)
    return _chat_complete(
        client=client,
        model=SECONDARY_MODEL,
        system_content=system_content,
        user_content=user_content,
        enable_thinking=enable_thinking,
    )


# -------------------------------
# Backwards-compatible aliases
# -------------------------------
# The experiment scripts (adaptive_test.py, text2code_adapvetest.py,
# query_template.py, gpt_judge.py, evaluate_responses.py, ...) import these
# names directly. They mirror the PRIMARY_* configuration above so a single
# local endpoint can serve the attacker, judge, and victim roles.
your_model = PRIMARY_MODEL
your_base_url = PRIMARY_BASE_URL
your_api_key = PRIMARY_API_KEY
LLM_MODEL = PRIMARY_MODEL
