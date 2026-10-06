from enum import Enum
import os

# =========================
# Global generation settings
# =========================
ATTACK_TEMP = 1.0
TARGET_TEMP = 0.0
ATTACK_TOP_P = 0.9
TARGET_TOP_P = 1.0

# Increase to allow more parallel streams (may increase memory usage)
# Decrease to reduce memory footprint
MAX_PARALLEL_STREAMS = 5


# =========================
# Model registry
# =========================
class Model(Enum):
    vicuna = "vicuna-13b-v1.5"
    gpt_3_5 = "gpt-3.5-turbo"
    gpt_4 = "gpt-4o-2024-11-20"
    claude_3_5 = "claude-3-5-sonnet-20241022"
    qwen2_5_3b = "Qwen2.5-3B-Instruct"
    qwen2_5_coder_7b = "Qwen2.5-Coder-7B-Instruct"
    qwen2_5_coder_14b = "Qwen2.5-Coder-14B-Instruct"
    qwen3_14b = "Qwen3-14B"
    qwen3_8b = "Qwen3-8B"
    qwen3_32b = "Qwen3-32B"
    llama_3_1_8b = "Llama-3.1-8B-Instruct"
    gemini_2_0_flash = "gemini-2.0-flash"
    deepseek_coder_7b = "Deepseek-coder-7b"
    deepseek_v2 = "DeepseekV2"
    llama2_70b = "llama-2-70b"
    llama2_13b = "llama-2-13b"


MODEL_NAMES = [m.value for m in Model]


# =========================
# Concrete model identifiers
# Use public IDs where applicable; use placeholders for local models.
# =========================
Concrete_MODEL_NAMES: dict[Model, str] = {
    Model.vicuna: "<PATH_OR_HUB_ID_FOR_VICUNA>",  # e.g., "lmsys/vicuna-13b-v1.5"
    Model.gpt_3_5: "gpt-3.5-turbo",
    Model.gpt_4: "gpt-4o-2024-11-20",
    Model.claude_3_5: "claude-3-5-sonnet-20241022",
    Model.qwen2_5_3b: "Qwen/Qwen2.5-3B-Instruct",
    Model.qwen2_5_coder_7b: "Qwen/Qwen2.5-Coder-7B-Instruct",
    Model.qwen2_5_coder_14b: "<LOCAL_OR_HUB_ID_FOR_QWEN2.5-CODER-14B-INSTRUCT>",
    Model.qwen3_14b: "Qwen/Qwen3-14B",
    Model.qwen3_8b: "Qwen/Qwen3-8B",
    Model.qwen3_32b: "<LOCAL_OR_HUB_ID_FOR_QWEN3-32B>",
    Model.gemini_2_0_flash: "gemini-2.0-flash",
    Model.llama_3_1_8b: "meta-llama/Llama-3.1-8B-Instruct",
    Model.deepseek_coder_7b: "<LOCAL_OR_HUB_ID_FOR_DEEPSEEK-CODER-7B>",
    Model.deepseek_v2: "<LOCAL_OR_HUB_ID_FOR_DEEPSEEKV2>",
    Model.llama2_70b: "llama-2-70b",
    Model.llama2_13b: "<LOCAL_OR_HUB_ID_FOR_LLAMA2-13B>",
}


# =========================
# Chat template names (for routers like FastChat)
# =========================
FASTCHAT_TEMPLATE_NAMES: dict[Model, str] = {
    Model.gpt_3_5: "gpt-3.5-turbo",
    Model.gpt_4: "gpt-4",
    Model.claude_3_5: "claude-3-sonnet",
    Model.gemini_2_0_flash: "gemini-flash",
    Model.vicuna: "vicuna_v1.5",
    Model.llama_3_1_8b: "llama-3-chat",
    Model.llama2_70b: "llama-2-chat",
    Model.llama2_13b: "llama-2-chat",
    Model.qwen2_5_3b: "qwen2",
    Model.qwen2_5_coder_7b: "qwen2",
    Model.qwen2_5_coder_14b: "qwen2",
    Model.qwen3_8b: "qwen3",
    Model.qwen3_14b: "qwen3",
    Model.qwen3_32b: "qwen3",
    Model.deepseek_coder_7b: "deepseek-coder",
    Model.deepseek_v2: "deepseek-chat",
}


# =========================
# API keys and base URLs
# NOTE: Do NOT hardcode secrets. Read from environment variables instead.
# =========================

# Example environment variable names (set them externally for experiments):
#   OPENAI_API_KEY
#   ANTHROPIC_API_KEY
#   GEMINI_API_KEY
#   DEFAULT_API_KEY
#   OPENAI_BASE_URL
#   CLAUDE_BASE_URL
#   GEMINI_BASE_URL
#   LOCAL_ENDPOINT_0, LOCAL_ENDPOINT_1, ...

def _env(name: str, default: str = "<SET_ME>") -> str:
    return os.getenv(name, default)


API_KEY_NAMES: dict[Model, str | None] = {
    Model.gpt_3_5: _env("OPENAI_API_KEY", None),
    Model.gpt_4: _env("OPENAI_API_KEY", None),
    Model.claude_3_5: _env("ANTHROPIC_API_KEY", None),
    Model.gemini_2_0_flash: _env("GEMINI_API_KEY", None),
    Model.vicuna: _env("DEFAULT_API_KEY", None),
    Model.llama_3_1_8b: _env("DEFAULT_API_KEY", None),
    Model.qwen2_5_3b: _env("DEFAULT_API_KEY", None),
    Model.qwen2_5_coder_7b: _env("DEFAULT_API_KEY", None),
    Model.qwen2_5_coder_14b: _env("DEFAULT_API_KEY", None),
    Model.qwen3_8b: _env("DEFAULT_API_KEY", None),
    Model.qwen3_14b: _env("DEFAULT_API_KEY", None),
    Model.qwen3_32b: _env("DEFAULT_API_KEY", None),
    Model.deepseek_coder_7b: _env("DEFAULT_API_KEY", None),
    Model.deepseek_v2: _env("DEFAULT_API_KEY", None),
    Model.llama2_70b: _env("DEFAULT_API_KEY", None),
    Model.llama2_13b: _env("DEFAULT_API_KEY", None),
}


BASE_URLS: dict[Model, str] = {
    Model.gpt_3_5: _env("OPENAI_BASE_URL", "<BASE_URL>"),
    Model.gpt_4: _env("OPENAI_BASE_URL", "<BASE_URL>"),
    Model.claude_3_5: _env("CLAUDE_BASE_URL", "<BASE_URL>"),
    Model.gemini_2_0_flash: _env("GEMINI_BASE_URL", "<BASE_URL>"),
    Model.vicuna: _env("LOCAL_ENDPOINT_0", "<LOCAL_ENDPOINT>"),
    Model.llama_3_1_8b: _env("LOCAL_ENDPOINT_1", "<LOCAL_ENDPOINT>"),
    Model.llama2_70b: _env("LOCAL_ENDPOINT_2", "<LOCAL_ENDPOINT>"),
    Model.llama2_13b: _env("LOCAL_ENDPOINT_3", "<LOCAL_ENDPOINT>"),
    Model.qwen2_5_3b: _env("LOCAL_ENDPOINT_4", "<LOCAL_ENDPOINT>"),
    Model.qwen2_5_coder_7b: _env("LOCAL_ENDPOINT_4", "<LOCAL_ENDPOINT>"),
    Model.qwen2_5_coder_14b: _env("LOCAL_ENDPOINT_5", "<LOCAL_ENDPOINT>"),
    Model.qwen3_8b: _env("LOCAL_ENDPOINT_6", "<LOCAL_ENDPOINT>"),
    Model.qwen3_14b: _env("LOCAL_ENDPOINT_7", "<LOCAL_ENDPOINT>"),
    Model.qwen3_32b: _env("LOCAL_ENDPOINT_8", "<LOCAL_ENDPOINT>"),
    Model.deepseek_coder_7b: _env("LOCAL_ENDPOINT_9", "<LOCAL_ENDPOINT>"),
    Model.deepseek_v2: _env("LOCAL_ENDPOINT_10", "<LOCAL_ENDPOINT>"),
}


# =========================
# Thinking-mode flags
# =========================
IS_THINKING_MODEL: dict[Model, bool] = {
    Model.gpt_3_5: False,
    Model.gpt_4: False,
    Model.claude_3_5: False,
    Model.gemini_2_0_flash: False,
    Model.vicuna: False,
    Model.llama_3_1_8b: False,
    Model.qwen2_5_3b: False,
    Model.qwen2_5_coder_7b: False,
    Model.qwen2_5_coder_14b: False,
    Model.qwen3_8b: True,
    Model.qwen3_14b: True,
    Model.qwen3_32b: True,
    Model.deepseek_coder_7b: False,
    Model.deepseek_v2: False,
    Model.llama2_70b: False,
    Model.llama2_13b: False,
}