# Checkpoint utilities and helper classes
from dataclasses import dataclass
import json
import logging
import os
import random
from typing import Dict, List

import numpy as np
import pandas as pd


# ---------- Data structures ----------
@dataclass
class Template:
    text: str                 # template with placeholders
    language: str = None      # language identifier
    meta: Dict = None         # metadata (e.g., scores)

    def fill(self, cat: str, content: str, mod: str) -> str:
        return (
            self.text
            .replace("{Category}", cat)
            .replace("{Content}", content)
            .replace("{Modifier}", mod)
        )


class UCB1Bandit:
    """Minimal UCB-1 implementation for discrete arms."""
    def __init__(self, arms: List[str]):
        self.arms = arms
        self.Q = {a: 0.0 for a in arms}  # mean reward
        self.N = {a: 0 for a in arms}    # pull counts
        self.total_pulls = 0

    def select(self) -> str:
        import math
        self.total_pulls += 1
        log_total = math.log(self.total_pulls)

        def ucb(a: str) -> float:
            if self.N[a] == 0:
                return float("inf")  # force initial exploration
            return self.Q[a] + math.sqrt(2.0 * log_total / self.N[a])

        return max(self.arms, key=ucb)

    def update(self, arm: str, reward: float):
        self.N[arm] += 1
        # incremental mean update
        self.Q[arm] += (reward - self.Q[arm]) / self.N[arm]


class TemplatePool:
    """Keeps high-scoring templates while preserving some diversity."""
    def __init__(self, max_size: int, min_size: int = 3):
        self.templates: List[Template] = []
        self.max_size = max_size
        self.min_size = min_size
        self.score_history: List[float] = []

    def add(self, templates: List[Template]):
        self.templates.extend(templates)
        self.templates.sort(key=lambda x: x.meta["score"], reverse=True)

        # Keep top-scoring templates plus a random slice for diversity
        if len(self.templates) > self.max_size:
            keep_top = int(self.max_size * 0.7)
            keep_random = self.max_size - keep_top
            tail_len = len(self.templates) - keep_top
            if tail_len > 0 and keep_random > 0:
                rand_idx = random.sample(
                    range(keep_top, len(self.templates)),
                    min(keep_random, tail_len),
                )
                self.templates = self.templates[:keep_top] + [self.templates[i] for i in rand_idx]
            else:
                self.templates = self.templates[:self.max_size]

    def get_best(self) -> Template:
        return max(self.templates, key=lambda x: x.meta["score"])

    def get_templates(self) -> List[Template]:
        return self.templates


class AdaptiveThreshold:
    """Adaptive retention threshold based on recent scores."""
    def __init__(self, initial_threshold: float = 1.1, alpha: float = 0.1, min_threshold: float = 0.5):
        self.threshold = initial_threshold
        self.alpha = alpha
        self.min_threshold = min_threshold
        self.score_history: List[float] = []

    def update(self, new_scores: List[float]):
        if not new_scores:
            return
        self.score_history.extend(new_scores)
        recent = self.score_history[-20:]  # sliding window
        if recent:
            mean = float(np.mean(recent))
            std = float(np.std(recent)) if len(recent) > 1 else 0.0
            self.threshold = max(self.min_threshold, mean + self.alpha * std)

    def get_threshold(self) -> float:
        return self.threshold


def save_checkpoint(
    checkpoint_path: str,
    responses: list,
    total_query_numbers: int,
    last_index: int,
    macro_bandit: UCB1Bandit,
):
    """Persist attack state to disk."""
    checkpoint = {
        "responses": responses,
        "total_query_numbers": total_query_numbers,
        "last_index": last_index,
        "bandit_Q": macro_bandit.Q,
        "bandit_N": macro_bandit.N,
        "bandit_total_pulls": macro_bandit.total_pulls,
    }
    os.makedirs(os.path.dirname(checkpoint_path), exist_ok=True)
    with open(checkpoint_path, "w", encoding="utf-8") as f:
        json.dump(checkpoint, f)
    logging.info(f"Checkpoint saved at index {last_index}")


def load_checkpoint(checkpoint_path: str, macro_bandit: UCB1Bandit):
    """Load attack state from disk; return empty defaults if not found."""
    try:
        with open(checkpoint_path, "r", encoding="utf-8") as f:
            checkpoint = json.load(f)

        # restore bandit state
        macro_bandit.Q = checkpoint["bandit_Q"]
        macro_bandit.N = checkpoint["bandit_N"]
        macro_bandit.total_pulls = checkpoint["bandit_total_pulls"]

        return (
            checkpoint["responses"],
            checkpoint["total_query_numbers"],
            checkpoint["last_index"],
        )
    except FileNotFoundError:
        return [], 0, -1


def setup_logging(log_dir: str, model_name: str, last_processed_index: int) -> str:
    """Configure logging to file + console; append if resuming."""
    model_leaf = os.path.basename(model_name)
    out_dir = os.path.join(log_dir, model_leaf)
    os.makedirs(out_dir, exist_ok=True)

    log_file = f"{out_dir}/attack.log"
    mode = "a" if last_processed_index != -1 else "w"

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_file, mode=mode),
            logging.StreamHandler(),
        ],
    )

    if mode == "a":
        logging.info("\n" + "=" * 50)
        logging.info(f"Resuming attack from index {last_processed_index}")
    else:
        logging.info("Starting new attack")

    return log_file


def read_data_with_target() -> Dict[str, str]:
    """Load goal→target mapping from CSV."""
    df = pd.read_csv("./data/harmful_behaviors_target.csv")
    return dict(zip(df["goal"], df["target"]))