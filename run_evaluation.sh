#!/bin/bash

TARGET_MODEL=""
ATTACK_METHOD=""

# Argument parsing
while [[ $# -gt 0 ]]; do
  key="$1"
  case $key in
    --target_model)
      TARGET_MODEL="$2"
      shift; shift
      ;;
    --attack_method)
      ATTACK_METHOD="$2"
      shift; shift
      ;;
    *)
      echo "Unknown argument: $1"
      exit 1
      ;;
  esac
done

# Argument check
if [ -z "$TARGET_MODEL" ]; then
  echo "Usage: bash run_evaluation.sh --target_model <model_name> [--attack_method <method>]"
  exit 1
fi

# Supported evaluation methods
# ALL_METHODS=(
#   "C++" "C#" "C" "Python" "Go" "SQL" "Java" "JavaScript" "URL"
#   "Base64" "BitBypass"
#   "CodeAttack_python_list_plus" "CodeAttack_python_stack_plus" "CodeAttack_python_string_plus"
#   "CoSafe" "PAIR" "TAP" "adaptive"
# )

ALL_METHODS=(
  "adaptive_paraphrasing" "adaptive_retokenization" "adaptive_SmoothLLM_RandomInsertPerturbation"
  "adaptive_SmoothLLM_RandomPatchPerturbation" "adaptive_SmoothLLM_RandomSwapPerturbation"
)

# ALL_METHODS=(
#   "Python_paraphrasing" "Python_retokenization" "Python_SmoothLLM_RandomInsertPerturbation"
#   "Python_SmoothLLM_RandomPatchPerturbation" "Python_SmoothLLM_RandomSwapPerturbation"
# )

mkdir -p logs/${TARGET_MODEL}

run_evaluation() {
  local model=$1
  local method=$2

  echo ">> Evaluating [$method] for [$model]..."
  python evaluate_responses.py \
    --your_model "$model" \
    --attack_method "$method"
}

if [ -z "$ATTACK_METHOD" ]; then
  for method in "${ALL_METHODS[@]}"; do
    run_evaluation "$TARGET_MODEL" "$method"
  done
else
  run_evaluation "$TARGET_MODEL" "$ATTACK_METHOD"
fi