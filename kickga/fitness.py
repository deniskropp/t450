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

# Import the playbook schema for TAS-aware fitness (wire #4)
try:
    from .playbook_schema import (
        TAS, PTAS, Anchor,
        tas_from_genome_vector, ptas_from_tas, anchor_from_ptas,
        CoherenceStatus, ConsentStatus,
        create_playbook_event,
        TasExtractedPayload, ConsentGrantedPayload, AnchorCreatedPayload,
        CoherenceHighPayload, CycleSealedPayload,
    )
except Exception:  # allow import before playbook_schema is fully wired during dev
    TAS = PTAS = Anchor = None  # type: ignore
    tas_from_genome_vector = ptas_from_tas = anchor_from_ptas = None  # type: ignore
    CoherenceStatus = ConsentStatus = None  # type: ignore
    create_playbook_event = None  # type: ignore
    TasExtractedPayload = ConsentGrantedPayload = AnchorCreatedPayload = None  # type: ignore
    CoherenceHighPayload = CycleSealedPayload = None  # type: ignore


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


# =============================================================================
# TAS / Playbook Schema aware fitness (task 4 wiring)
# =============================================================================

DEFAULT_TAS_KEYS = [
    "coherence_target",      # target coherence for the evolved TAS
    "anchor_stability",      # how stable the EmbodiedPipe anchor should be
    "consent_weight",        # weight given to explicit consent gates
    "resequence_tendency",   # tendency to trigger resequence (lower is usually better)
    "ethical_threshold",     # KickGuard ethical bar (higher = stricter)
    "somatic_valence",       # somatic / EmbodiedPipe valence strength
    "pipeline_efficiency",   # how efficiently KickFlow can turn PTAS into pipeline
    "drift_tolerance",       # tolerance for coherence drift before COHERENCE_LOW
]


def tas_coherence_fitness(
    g: GAGenome,
    keys: Optional[List[str]] = None,
    raw_input: str = "GA-evolved TAS parameters for OCS meta-playbook",
) -> float:
    """
    Fitness function that treats a KickVectorGenome as a set of TAS parameters.

    Higher score = better "playbook health":
      - High coherence
      - High anchor stability
      - High consent / ethical scores
      - Low resequence_tendency + low drift
      - Good pipeline efficiency

    This directly wires the UnifiedPlaybookSchema concepts into kickga evolution.
    The best genomes can later be turned into real TAS/PTAS/Anchor + event streams.
    """
    if not isinstance(g, KickVectorGenome):
        return -888.0

    k = keys or DEFAULT_TAS_KEYS
    vec = list(g.vector)

    # Pad or trim to expected length
    if len(vec) < len(k):
        vec = vec + [0.65] * (len(k) - len(vec))
    vec = vec[: len(k)]

    # Named access (clamped 0-1 where meaningful)
    def get(name: str, default: float = 0.65) -> float:
        try:
            idx = k.index(name)
            v = float(vec[idx])
            return max(0.0, min(1.0, v)) if name not in {"resequence_tendency", "drift_tolerance"} else max(0.0, min(1.0, v))
        except ValueError:
            return default

    coherence = get("coherence_target", 0.72)
    stability = get("anchor_stability", 0.78)
    consent_w = get("consent_weight", 0.81)
    reseq = get("resequence_tendency", 0.25)   # lower better
    ethical = get("ethical_threshold", 0.80)
    somatic = get("somatic_valence", 0.74)
    pipeline = get("pipeline_efficiency", 0.69)
    drift_tol = get("drift_tolerance", 0.22)   # lower better

    # Core scoring (inspired by KickGuard + coherence monitoring)
    score = 5.0

    # Coherence & stability are primary (like CoherenceHigh vs Low events)
    score += (coherence - 0.5) * 6.0
    score += (stability - 0.5) * 5.5

    # Consent and ethics (KickGuard gates)
    score += (consent_w - 0.5) * 3.8
    score += (ethical - 0.5) * 4.2

    # Somatic grounding (EmbodiedPipe / Anchor)
    score += (somatic - 0.5) * 3.0

    # Pipeline quality (KickFlow)
    score += (pipeline - 0.5) * 3.5

    # Penalize high resequence tendency and high drift tolerance
    score -= reseq * 4.5
    score -= drift_tol * 3.8

    # Bonus for balanced "healthy" TAS (not extreme in any single dimension)
    balance = 1.0 - (max(vec) - min(vec))
    score += balance * 1.8

    # Simulate a tiny "cycle success" probability
    simulated_cycle_success = min(0.98, 0.55 + 0.4 * coherence + 0.3 * stability - 0.25 * reseq)
    score += simulated_cycle_success * 2.0

    # Clamp to a nice KickLang-friendly range (roughly 2..18 like humor scores)
    final = max(1.5, min(17.5, round(score, 3)))
    return final


def make_tas_coherence_fitness(keys: Optional[List[str]] = None) -> FitnessFunction:
    """Factory returning a fitness suitable for TAS-param vector genomes."""
    def fn(g: GAGenome) -> float:
        return tas_coherence_fitness(g, keys=keys)
    return fn


def simulate_playbook_cycle_from_vector(
    vector: List[float],
    keys: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Given an evolved TAS vector, simulate a minimal happy-path playbook cycle
    using the Python schema mirrors. Returns a dict with tas/ptas/anchor + event list.

    This is the bridge between GA search and real OCS / meta-playbook consumption.
    """
    if tas_from_genome_vector is None:
        return {"error": "playbook_schema not available"}

    k = keys or DEFAULT_TAS_KEYS
    tas = tas_from_genome_vector(vector, keys=k)
    ptas = ptas_from_tas(tas, consent=ConsentStatus.GRANTED)
    anchor = anchor_from_ptas(ptas, stability=float(min(0.95, max(0.6, vector[1] if len(vector) > 1 else 0.82))))

    # Build a tiny happy-path event stream (using the schema factories)
    events = []
    events.append(create_playbook_event(
        "TAS_EXTRACTED", "KickForge", TasExtractedPayload(
            tas_id=tas.id,
            raw_input=tas.raw_input,
            grounded_context=tas.grounded_context,
            atomic_intent=tas.atomic_intent,
            signals=tas.signals,
        )
    ))
    events.append(create_playbook_event(
        "CONSENT_GRANT", "KickGuard", ConsentGrantedPayload(
            ptas_id=ptas.id,
            source_tas_id=ptas.source_tas_id,
            purified_intent=ptas.purified_intent,
            ethical_alignment="aligned",
            consent_status="granted",
        )
    ))
    events.append(create_playbook_event(
        "ANCHOR_CREATED", "EmbodiedPipe", AnchorCreatedPayload(
            anchor_id=anchor.anchor_id,
            ptas_id=anchor.ptas_id,
            somatic_context=anchor.somatic_context,
            ritual_frame=anchor.ritual_frame,
            pipe_channel=anchor.pipe_channel,
            stability_score=anchor.stability_score,
        )
    ))
    events.append(create_playbook_event(
        "COHERENCE_HIGH", "KickGuard", CoherenceHighPayload(
            coherence_status="high",
            metrics={"coherence": round(0.88 + (vector[0]-0.5)*0.1 if vector else 0.89, 3)},
            anchor_id=anchor.anchor_id,
        )
    ))
    events.append(create_playbook_event(
        "CYCLE_SEALED", "KickFlow", CycleSealedPayload(
            cycle_id=f"cycle_{tas.id[-6:]}",
            summary="GA-evolved TAS parameters produced high-coherence sealed cycle.",
            final_coherence="high",
            sealed_at=tas.timestamp,
            key_artifacts=[f"tas:{tas.id}", f"ptas:{ptas.id}", f"anchor:{anchor.anchor_id}"],
        )
    ))

    return {
        "tas": tas.to_dict(),
        "ptas": ptas.to_dict(),
        "anchor": anchor.to_dict(),
        "events": [e.to_dict() for e in events],
        "cycle_summary": "happy_path_sealed",
    }
