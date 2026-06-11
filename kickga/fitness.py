"""
Fitness functions for KickLang GA experiments.

Includes:
- Vector distance to target (classic optimization)
- HumorDNA-style scorer (self-referential to the ecosystem's Humor DNA + joke scoring logic)
- Pluggable protocol so you can supply any KickLang-evaluable objective
"""

from __future__ import annotations
from typing import Any, Callable, Dict, List, Optional

from .genome import GAGenome, KickVectorGenome, KickListGenome, KickBlockGenome


FitnessFunction = Callable[[GAGenome], float]


def make_vector_target_fitness(target: List[float], penalty: float = 10.0) -> FitnessFunction:
    """
    Euclidean distance to target vector (maximize similarity = minimize distance).
    Returns a fitness where higher = better (i.e. we negate distance).
    """
    tgt = list(target)

    def fitness(g: GAGenome) -> float:
        if not isinstance(g, KickVectorGenome):
            return -penalty
        v = g.vector
        if len(v) != len(tgt):
            return -penalty * abs(len(v) - len(tgt))
        dist = sum((a - b) ** 2 for a, b in zip(v, tgt)) ** 0.5
        return -dist  # higher (less negative) is better

    return fitness


# --- Humor DNA inspired fitness (port of core ideas from HumorForge / humor_dna-0.9.2) ---

# Default "ideal" high-expression DNA for the comedy/swarm style in the ecosystem
DEFAULT_IDEAL_DNA: Dict[str, float] = {
    "meta_ai_irony_literal_roasts": 11.0,
    "kicklang_command_wordplay": 12.5,
    "multi_agent_deadlock": 8.0,
    "short_setups": 13.0,
    "tight_punchlines": 13.5,
    "direct_kicklang_command_usage": 11.0,
    "logic_loop_recursion": 12.0,
    "animal_swarm_logic_loops": 14.0,
    "monkey_typewriter_banana_chaos": 13.5,
    "iterative_laugh_team_deadlock": 12.0,
    "deutsche_query_ironie": 11.5,
    "animal_puns": 9.0,
    "tech_fails": 8.5,
    "self_deprecating": 10.0,
}


def humor_dna_fitness(g: GAGenome, ideal: Optional[Dict[str, float]] = None) -> float:
    """
    Scores a KickVectorGenome whose vector order matches the keys in DEFAULT_IDEAL_DNA (or supplied ideal).

    The scoring logic mirrors the spirit of analyzeAndScore + updateDNA + session laugh heuristics
    from the HumorForge project and the DNA JSON artifacts used in KickLang experiments.

    Higher = funnier / more "on-brand" for the Iterative Laugh Team / KickLang irony swarm style.
    """
    if not isinstance(g, KickVectorGenome):
        return -999.0

    ideal = ideal or DEFAULT_IDEAL_DNA
    keys = list(ideal.keys())
    vec = g.vector

    if len(vec) < len(keys):
        # pad with neutral
        vec = vec + [7.0] * (len(keys) - len(vec))
    vec = vec[: len(keys)]

    score = 7.0  # base

    for i, k in enumerate(keys):
        val = vec[i]
        target = ideal[k]
        # closeness to sweet spot
        diff = abs(val - target)
        if diff < 0.8:
            score += 1.4
        elif diff < 1.8:
            score += 0.7
        else:
            score -= min(2.5, diff * 0.6)

        # specific trait boosts (same spirit as the original humorForgeLogic)
        if k == "tight_punchlines" and val > 11:
            score += 0.9
        if k == "short_setups" and val > 10:
            score += 0.8
        if k == "monkey_typewriter_banana_chaos" and val > 12:
            score += 1.3
        if k == "logic_loop_recursion" and val > 10:
            score += 0.6
        if k == "deutsche_query_ironie" and val > 9.5:
            score += 0.7
        if k == "animal_swarm_logic_loops" and val > 12:
            score += 0.9

    # small bonus for diversity (not all values identical)
    if len(set(round(v, 1) for v in vec)) > max(3, len(vec) // 2):
        score += 0.5

    # clamp to plausible laugh-score range
    return max(2.0, min(15.0, round(score, 3)))


def make_humor_dna_fitness(ideal: Optional[Dict[str, float]] = None) -> FitnessFunction:
    def fn(g: GAGenome) -> float:
        return humor_dna_fitness(g, ideal=ideal)
    return fn


# --- Convenience: wrap any python function as fitness for a specific genome type ---

def make_custom_fitness(fn: Callable[[Any], float], expected_type: Optional[type] = None) -> FitnessFunction:
    def wrapped(g: GAGenome) -> float:
        if expected_type and not isinstance(g, expected_type):
            return -1000.0
        try:
            return float(fn(g))
        except Exception:
            return -999.0
    return wrapped
