# Running MultiCodeAttack on Kaggle

The experiment scripts talk to an **OpenAI-compatible endpoint**. On Kaggle we serve
Qwen 2.5 3B locally with **vLLM** (downloaded from Hugging Face on first launch), then
point the scripts at `http://localhost:8000/v1`.

**Recommended accelerator:** `GPU T4 x2` (Notebook settings → Accelerator). Internet must be **ON**.

The three cells below go in a Kaggle notebook, in order.

> **Prerequisite — missing functions.** This sanitized repo does **not** define
> `trans_language_to_first_user_content`, `trans_language_to_assistant_response_4o`,
> `trans_language_to_first_user_code_content`, or `trans_language_to_assistant_code_response_4o`
> (imported by `adaptive_test.py` / `text2code_adapvetest.py` from `query_template.py`).
> They were stripped during sanitization. Restore them from your original copy into
> `query_template.py` before running, or both entry scripts will fail at import.

---

## Cell 1 — Clone repo + install dependencies

```python
import os

# --- PRIVATE repo: store a GitHub token in Add-ons > Secrets as GITHUB_TOKEN ---
from kaggle_secrets import UserSecretsClient
token = UserSecretsClient().get_secret("GITHUB_TOKEN")
repo = f"https://{token}@github.com/brainardphilemon/MultiCodeAttack.git"

# --- If you make the repo PUBLIC instead, comment the 3 lines above and use: ---
# repo = "https://github.com/brainardphilemon/MultiCodeAttack.git"

!rm -rf /kaggle/working/MultiCodeAttack
!git clone {repo} /kaggle/working/MultiCodeAttack
%cd /kaggle/working/MultiCodeAttack

# vLLM (pulls a compatible torch) + client libs. Takes a few minutes.
!pip -q install vllm openai nltk pandas

import nltk
for pkg in ["punkt", "punkt_tab", "averaged_perceptron_tagger", "averaged_perceptron_tagger_eng"]:
    try:
        nltk.download(pkg)
    except Exception as e:
        print("nltk", pkg, "->", e)
```

## Cell 2 — Start the vLLM server (downloads Qwen 2.5 3B from HF)

```python
import subprocess, time, requests, os

# AWQ 4-bit quant (~3 GB) fits on a single T4 and works on T4 (sm75).
server = subprocess.Popen([
    "vllm", "serve", "Qwen/Qwen2.5-3B-Instruct-AWQ",
    "--served-model-name", "Qwen2.5-3B-Instruct",
    "--quantization", "awq",
    "--port", "8000",
    "--max-model-len", "4096",
    "--gpu-memory-utilization", "0.90",
])

# Wait until the endpoint is healthy (first run also downloads the weights).
for _ in range(180):
    try:
        if requests.get("http://localhost:8000/health").status_code == 200:
            print("vLLM server is up"); break
    except Exception:
        pass
    time.sleep(5)
else:
    print("Server did not become healthy in time — check the cell output/logs.")
```

**Alternative — full precision across both T4s** (no quantization, uses both GPUs):

```python
# server = subprocess.Popen([
#     "vllm", "serve", "Qwen/Qwen2.5-3B-Instruct",
#     "--served-model-name", "Qwen2.5-3B-Instruct",
#     "--dtype", "float16",
#     "--tensor-parallel-size", "2",
#     "--port", "8000", "--max-model-len", "4096",
# ])
```

## Cell 3 — Run the attack/eval pipeline

```python
%cd /kaggle/working/MultiCodeAttack
os.environ["PRIMARY_MODEL"]    = "Qwen2.5-3B-Instruct"
os.environ["PRIMARY_BASE_URL"] = "http://localhost:8000/v1"
os.environ["PRIMARY_API_KEY"]  = "EMPTY"

# Step 1 (one-time per model): generate response/<model>/template/specific_template.txt
!python query_template.py

# Step 2: run the TEXT task on 10 samples only
!python adaptive_test.py --store_path data --num_samples 10

# Code task variant (also 10 samples):
# !python text2code_adapvetest.py --store_path data --num_samples 10
```

`--num_samples 10` limits the run to the first 10 sentence-groups (of 520 in
`data/llms/phrases.csv`); use `0` or omit it to run all.

Outputs are written under `response/`, `logs/`, and `test/` in the working directory.

---

### Notes
- `PRIMARY_*` env vars drive the attacker, judge, and victim roles (all Qwen here). To use a
  separate judge model, set `SECONDARY_MODEL` / `SECONDARY_BASE_URL` / `SECONDARY_API_KEY`.
- The served model name (`Qwen2.5-3B-Instruct`) must match `PRIMARY_MODEL`.
- `--served-model-name` avoids a `/` in the name so output paths like `response/<model>/...` stay flat.
- P100 does not support AWQ (sm60); use the full-precision alternative in Cell 2 there, or pick T4 x2.
