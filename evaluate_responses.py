import json
import os
from pathlib import Path
import time

from config import Concrete_MODEL_NAMES, Model
from gpt_judge import score_evaluation
from all_template import judge_template


def save_checkpoint(checkpoint_path, HS, Evaluation, last_index):
    """Save checkpoint during evaluation."""
    checkpoint = {
        "HS": HS,
        "Evaluation": Evaluation,
        "last_index": last_index,
    }
    with open(checkpoint_path, "w", encoding="utf-8") as f:
        json.dump(checkpoint, f)
        f.flush()
    print(f"Checkpoint saved at {checkpoint_path}")


def load_checkpoint(checkpoint_path):
    """Load checkpoint if it exists."""
    try:
        with open(checkpoint_path, "r", encoding="utf-8") as f:
            checkpoint = json.load(f)
        return checkpoint["HS"], checkpoint["Evaluation"], checkpoint["last_index"]
    except FileNotFoundError:
        return [], [], -1


def calculate_score(problem, response):
    eval_prompt = judge_template.format(problem, response)
    messages = [{"role": "user", "content": eval_prompt}]
    score = None
    response_text = None
    while score is None:
        chat_completion = score_evaluation(messages)
        response_text = chat_completion.choices[0].message.content
        score = extract_content("#thescore:", response_text)
    return score, response_text


def extract_content(tag, text):
    start_idx = text.find(tag)
    if start_idx == -1:
        return None
    content_after_tag = text[start_idx + len(tag):].strip()
    parts = content_after_tag.split()
    if tag == "#thescore:":
        if parts and (parts[0].isdigit() or (len(parts[0]) > 0 and parts[0][0].isdigit())):
            return int(parts[0][0]) if not parts[0].isdigit() else int(parts[0])
        return None
    else:
        end_idx = text.find("#", start_idx + 1)
        return content_after_tag if end_idx == -1 else content_after_tag[:end_idx].strip()


def load_problems(data_path):
    with open(data_path, "r", encoding="utf-8") as file:
        return [line.strip() for line in file.readlines()]


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--attack_method",
        type=str,
        default="SQL",
        help="Supported: C++, C#, C, Python, Go, SQL, Java, JavaScript, URL, adaptive, Base64, "
             "BitBypass, CodeAttack variants, CoSafe, PAIR, TAP",
    )
    parser.add_argument(
        "--problem_path",
        type=str,
        default="data/harmful_behaviors.csv",
        help="Path to the dataset containing harmful problems",
    )
    parser.add_argument(
        "--your_model",
        type=str,
        default="gpt-4o-2024-11-20",
        help="The model whose responses are being evaluated",
    )
    args = parser.parse_args()

    args.your_model = Concrete_MODEL_NAMES[Model(args.your_model)]

    # Output paths
    hs_path = f"test/{args.your_model}/{args.attack_method}/HS.txt"
    eval_path = f"test/{args.your_model}/{args.attack_method}/Evaluation.txt"

    # Avoid overwriting existing results
    if os.path.exists(hs_path) and os.path.exists(eval_path):
        print(f"Results already exist at {hs_path} and {eval_path}. Exiting.")
        exit(0)

    # Checkpoint path
    checkpoint_dir = Path(f"checkpoints/{args.your_model}/{args.attack_method}")
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_path = checkpoint_dir / "eval_checkpoint.json"

    # Load checkpoint
    HS, Evaluation, last_processed_index = load_checkpoint(checkpoint_path)

    # Load problems and responses depending on attack method
    if args.attack_method in [
        "SQL", "C++", "C#", "C", "Python", "Go", "Java", "JavaScript", "URL", "adaptive",
        "adaptive_paraphrasing", "adaptive_retokenization",
        "adaptive_SmoothLLM_RandomInsertPerturbation",
        "adaptive_SmoothLLM_RandomPatchPerturbation",
        "adaptive_SmoothLLM_RandomSwapPerturbation",
        "Python_paraphrasing", "Python_retokenization",
        "Python_SmoothLLM_RandomInsertPerturbation",
        "Python_SmoothLLM_RandomPatchPerturbation",
        "Python_SmoothLLM_RandomSwapPerturbation",
    ]:
        problems = load_problems(args.problem_path)
        response_path = f"response/{args.your_model}/llms/{args.attack_method}_responses.txt"
        with open(response_path, "r", encoding="utf-8") as file:
            responses = file.readlines()

    elif args.attack_method in ["Base64", "BitBypass", "CoSafe", "PAIR", "TAP"]:
        response_path = f"response/{args.your_model}/llms/{args.attack_method}_responses.json"
        objects = json.load(open(response_path, "r", encoding="utf-8"))
        problems = [obj["goal"] for obj in objects]
        responses = [obj["output"] for obj in objects]

    elif args.attack_method in [
        "CodeAttack_python_list_plus",
        "CodeAttack_python_stack_plus",
        "CodeAttack_python_string_plus",
    ]:
        response_path = f"response/{args.your_model}/llms/{args.attack_method}_responses.json"
        objects = json.load(open(response_path, "r", encoding="utf-8"))
        problems = [obj["plain_attack"] for obj in objects]
        raw_responses = [obj["res_simplified"] for obj in objects]
        responses = [
            r if isinstance(r, str)
            else ("" if not r or r[0] is None else " ".join(r))
            if isinstance(r, list) else ""
            for r in raw_responses
        ]

    else:
        raise ValueError(f"Unsupported attack method: {args.attack_method}")

    if args.attack_method in [
        "adaptive_paraphrasing", "adaptive_retokenization",
        "adaptive_SmoothLLM_RandomInsertPerturbation",
        "adaptive_SmoothLLM_RandomPatchPerturbation",
        "adaptive_SmoothLLM_RandomSwapPerturbation",
        "Python_paraphrasing", "Python_retokenization",
        "Python_SmoothLLM_RandomInsertPerturbation",
        "Python_SmoothLLM_RandomPatchPerturbation",
        "Python_SmoothLLM_RandomSwapPerturbation",
    ]:
        problems = problems[: len(responses)]

    print(f"Number of problems: {len(problems)}, responses: {len(responses)}")
    assert len(problems) == len(responses), "Mismatch between problems and responses."

    MAX_ATTEMPTS = 10
    for i in range(last_processed_index + 1, len(responses)):
        attempt = 0
        while attempt < MAX_ATTEMPTS:
            try:
                score, evaluation = calculate_score(
                    problems[i], responses[i].strip() if responses[i] else ""
                )
                HS.append(score)
                Evaluation.append(evaluation)

                print(f"Problem {i + 1}: Score: {score}")
                print(f"Current score counts: { {str(s): HS.count(s) for s in set(HS)} }")
                print("Average Score:", sum(HS) / len(HS) if HS else 0)

                if (i - last_processed_index) % 5 == 0:
                    save_checkpoint(checkpoint_path, HS, Evaluation, i)

                break
            except Exception as e:
                print(f"API error at problem {i}: {str(e)}")
                time.sleep(1)
                save_checkpoint(checkpoint_path, HS, Evaluation, i - 1)
                attempt += 1
        else:
            raise RuntimeError(f"{args.attack_method} failed repeatedly at index {i}")

    os.makedirs(os.path.dirname(hs_path), exist_ok=True)
    try:
        with open(hs_path, "w", encoding="utf-8") as file:
            for item in HS:
                file.write(str(item) + "\n")

        with open(eval_path, "w", encoding="utf-8") as file:
            for item in Evaluation:
                file.write(str(item) + "\n")

        if os.path.exists(checkpoint_path):
            os.remove(checkpoint_path)
    except Exception:
        with open(f"{hs_path}.backup", "w", encoding="utf-8") as file:
            for item in HS:
                file.write(str(item) + "\n")
        with open(f"{eval_path}.backup", "w", encoding="utf-8") as file:
            for item in Evaluation:
                file.write(str(item) + "\n")