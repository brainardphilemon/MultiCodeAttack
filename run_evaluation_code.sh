#!/bin/bash

TARGET_MODEL=""
ATTACK_METHOD=""

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

if [ -z "$TARGET_MODEL" ]; then
  echo "Usage: bash run_evaluation_code.sh --target_model <model_name> [--attack_method <method>]"
  exit 1
fi

# ALL_METHODS=(
#   "adaptive" "Base64" "BitBypass" "RAW"
# )

# ALL_METHODS=(
#   "abla1" "abla2" "abla3" "abla4"
# )

ALL_METHODS=(
  "BitBypass_paraphrasing" "BitBypass_retokenization" 
  "BitBypass_SmoothLLM_RandomInsertPerturbation" "BitBypass_SmoothLLM_RandomPatchPerturbation"
  "BitBypass_SmoothLLM_RandomSwapPerturbation"
)

run_evaluation() {
  local model=$1
  local method=$2

  echo ">> Evaluating [$method] for [$model]..."
  python test2code_eval.py \
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