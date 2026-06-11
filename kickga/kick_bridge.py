"""
KickLang <-> GAlib bridge.

Provides:
- Declarative GA experiment specs using KickLang-style ⫻ blocks (compatible with both
  the ritual/affirmation style and the compiler PLAN style).
- Loading those specs into runnable GASimpleGA configs.
- Emitting evolved results back as valid KickLang fragments (ready to paste into
  .kick files, humor_dna blocks, or OCS data/var payloads).

The simple directive parser here is intentionally small and self-contained so
kickga does not hard-depend on the full t20 or t314 parsers (you can still feed
full .kick sources through them first if desired).
"""

from __future__ import annotations
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .genome import KickVectorGenome, KickListGenome, KickBlockGenome, GAGenome
from .ga import GASimpleGA
from .fitness import make_humor_dna_fitness, make_vector_target_fitness

# Playbook schema wiring (task 4)
try:
    from .playbook_schema import (
        TAS, PTAS, Anchor, PlaybookEvent,
        tas_from_genome_vector, ptas_from_tas, anchor_from_ptas,
        create_playbook_event,
        to_json as playbook_to_json,
    )
except Exception:
    TAS = PTAS = Anchor = PlaybookEvent = None  # type: ignore
    tas_from_genome_vector = ptas_from_tas = anchor_from_ptas = None  # type: ignore
    create_playbook_event = None  # type: ignore
    playbook_to_json = None  # type: ignore


DIRECTIVE_RE = re.compile(r"^⫻([\w:/-]+)$")
KV_RE = re.compile(r"^([A-Za-z0-9_.-]+):\s*(.*)$")
LIST_ITEM_RE = re.compile(r"^\s*-\s*(.+)$")


@dataclass
class KickGAConfig:
    """Structured config parsed from a ⫻ga:experiment (or equivalent) block."""
    id: str = "ga-experiment"
    genome_type: str = "vector"          # vector | list | block
    pop_size: int = 40
    generations: int = 60
    p_crossover: float = 0.85
    p_mutation: float = 0.025
    fitness: str = "humor_dna"           # humor_dna | target | tas_coherence | custom
    target: Optional[List[float]] = None
    vector_length: int = 14
    vector_bounds: Optional[List[tuple]] = None
    seed: Optional[int] = None
    # TAS / Playbook wiring (task 4)
    tas_keys: Optional[List[str]] = None
    extra: Dict[str, Any] = field(default_factory=dict)


def _parse_simple_kick(source: str) -> Dict[str, Dict[str, Any]]:
    """Very small parser for the ⫻ style used in runtime.kick / humor.kick / dna blocks."""
    tree: Dict[str, Dict[str, Any]] = {}
    current_block: Optional[str] = None
    current_key: Optional[str] = None

    for raw in source.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue

        dm = DIRECTIVE_RE.match(line)
        if dm:
            directive = dm.group(1)
            block_name = directive.split(":")[-1] if ":" in directive else directive
            current_block = block_name
            if current_block not in tree:
                tree[current_block] = {"_type": directive}
            current_key = None
            continue

        kvm = KV_RE.match(line)
        if kvm and current_block:
            k, v = kvm.groups()
            v = v.strip()
            if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
                v = v[1:-1]
            # array?
            if v.startswith("[") and v.endswith("]"):
                items = [x.strip().strip('"\'') for x in v[1:-1].split(",") if x.strip()]
                tree[current_block][k] = items
            else:
                tree[current_block][k] = v
            current_key = k
            continue

        lm = LIST_ITEM_RE.match(raw)
        if lm and current_block and current_key:
            item = lm.group(1).strip()
            blk = tree[current_block]
            if current_key not in blk or not isinstance(blk[current_key], list):
                blk[current_key] = []
            blk[current_key].append(item)

    return tree


def load_kick_ga_spec(source: str) -> KickGAConfig:
    """
    Parse a KickLang source containing a ⫻ga:experiment (or ga:experiment) block
    and return a KickGAConfig.

    Falls back to sensible defaults if the block is absent (you can still drive
    everything from Python).
    """
    tree = _parse_simple_kick(source)

    # Look for ga experiment or generic ga block
    blk = None
    for key in ("ga:experiment", "experiment", "ga_experiment", "ga"):
        if key in tree:
            blk = tree[key]
            break
    if blk is None:
        # try last block that has 'ga' in type
        for v in tree.values():
            if "ga" in str(v.get("_type", "")).lower():
                blk = v
                break

    if not blk:
        blk = {}

    cfg = KickGAConfig(
        id=blk.get("id", blk.get("name", "ga-experiment-from-kick")),
        genome_type=blk.get("genome_type", blk.get("genome", "vector")),
        pop_size=int(blk.get("pop_size", blk.get("population", 40))),
        generations=int(blk.get("generations", blk.get("ngen", 60))),
        p_crossover=float(blk.get("p_crossover", blk.get("pc", 0.85))),
        p_mutation=float(blk.get("p_mutation", blk.get("pm", 0.025))),
        fitness=blk.get("fitness", blk.get("objective", "humor_dna")),
        vector_length=int(blk.get("vector_length", blk.get("length", 14))),
        tas_keys=blk.get("tas_keys") or blk.get("tas_dimensions"),
    )

    if "target" in blk:
        try:
            cfg.target = [float(x) for x in blk["target"]]
        except Exception:
            pass

    # bounds if present as two parallel arrays or inline
    if "bounds_low" in blk and "bounds_high" in blk:
        lows = [float(x) for x in blk["bounds_low"]]
        highs = [float(x) for x in blk["bounds_high"]]
        cfg.vector_bounds = list(zip(lows, highs))

    cfg.extra = {k: v for k, v in blk.items() if k not in {"id", "genome", "pop_size", "generations"}}
    return cfg


def build_initial_population(cfg: KickGAConfig, seed_dna: Optional[Dict[str, Any]] = None) -> List[GAGenome]:
    """Create a starting population from the config + optional seed (e.g. current HumorDNA)."""
    import random as _rnd
    rnd_state = _rnd.getstate()
    if cfg.seed is not None:
        _rnd.seed(cfg.seed)

    pop: List[GAGenome] = []
    n = cfg.pop_size

    if cfg.genome_type == "vector":
        base = [7.0] * cfg.vector_length
        if seed_dna and "core_preferences" in seed_dna:
            prefs = seed_dna["core_preferences"]
            # take in definition order or sorted for determinism
            vals = list(prefs.values())[: cfg.vector_length]
            if len(vals) < cfg.vector_length:
                vals += [7.0] * (cfg.vector_length - len(vals))
            base = [float(v) for v in vals][: cfg.vector_length]

        # TAS mode: use sensible defaults for coherence/anchor etc. (0.6-0.9 range)
        if cfg.fitness == "tas_coherence":
            # Prefer 8-locus TAS vectors unless user overrode length
            if cfg.vector_length == 14:  # common humor default
                cfg.vector_length = 8
            base = [round(0.65 + _rnd.random() * 0.22, 3) for _ in range(cfg.vector_length)]

        bounds = cfg.vector_bounds or [(0.0, 16.0)] * cfg.vector_length
        for _ in range(n):
            v = [round(b[0] + _rnd.random() * (b[1] - b[0]), 4) for b in bounds]
            # bias first few toward seed
            if _ < max(2, n // 6):
                for i in range(min(len(base), len(v))):
                    v[i] = round(0.6 * base[i] + 0.4 * v[i], 4)
            g = KickVectorGenome(vector=v, bounds=bounds, name=cfg.id)
            pop.append(g)

    elif cfg.genome_type == "list":
        seed_items: List[str] = []
        if seed_dna:
            seed_items = seed_dna.get("signature_jokes", []) or seed_dna.get("evolution_history", [])
        if not seed_items:
            seed_items = ["baseline", "loop recursion", "banana meeting", "deutsche ironie"]
        for _ in range(n):
            items = list(seed_items)
            _rnd.shuffle(items)
            # vary length a little
            if len(items) > 3:
                items = items[: max(3, len(items) - _rnd.randint(0, 1))]
            pop.append(KickListGenome(items=items, name=cfg.id))

    else:
        # block
        base_data = {"version": "ga-seed", "evolved": False}
        if seed_dna:
            base_data.update({k: v for k, v in seed_dna.items() if isinstance(v, (str, int, float, list))})
        for _ in range(n):
            d = dict(base_data)
            pop.append(KickBlockGenome(data=d, block_type=cfg.id))

    if cfg.seed is not None:
        _rnd.setstate(rnd_state)
    return pop


def create_ga_from_kick(source_or_cfg: str | KickGAConfig, seed: Optional[Dict[str, Any]] = None) -> GASimpleGA:
    """One-shot: load spec (string or pre-parsed), build pop, wire fitness, return ready-to-evolve GA."""
    if isinstance(source_or_cfg, str):
        cfg = load_kick_ga_spec(source_or_cfg)
    else:
        cfg = source_or_cfg

    pop = build_initial_population(cfg, seed_dna=seed)

    if cfg.fitness == "humor_dna":
        fitness = make_humor_dna_fitness()
    elif cfg.fitness == "target" and cfg.target:
        fitness = make_vector_target_fitness(cfg.target)
    elif cfg.fitness == "tas_coherence":
        # Use the new TAS/playbook coherence fitness (task 4)
        from .fitness import make_tas_coherence_fitness
        fitness = make_tas_coherence_fitness(keys=cfg.tas_keys)
    else:
        # default to humor style (most fun for KickLang context)
        fitness = make_humor_dna_fitness()

    ga = GASimpleGA(pop, fitness_fn=fitness, maximize=True)
    ga.populationSize(cfg.pop_size)
    ga.pCrossover = cfg.p_crossover
    ga.pMutation = cfg.p_mutation
    ga.nGenerations = cfg.generations
    return ga


def emit_kick_dna_block(
    genome: GAGenome,
    version: str = "evolved",
    directive: str = "⫻humor:dna:block",
) -> str:
    """
    Emit a KickLang-style DNA or result block from an evolved genome.

    Works for vector (core_preferences), list, or block genomes.
    """
    lines: List[str] = [directive]
    lines.append(f"id: {getattr(genome, 'name', 'evolved-dna')}_{version}")
    lines.append("scope: ga_evolved")
    lines.append("mode: generative")
    lines.append("mutability: extensible")
    lines.append('intent: "higher laugh density + stronger KickLang co-agency"')
    lines.append(f"version: {version}")

    if isinstance(genome, KickVectorGenome):
        # Map back to classic HumorDNA keys (order must be stable with DEFAULT_IDEAL_DNA)
        from .fitness import DEFAULT_IDEAL_DNA
        keys = list(DEFAULT_IDEAL_DNA.keys())
        prefs = {}
        for i, k in enumerate(keys):
            if i < len(genome.vector):
                prefs[k] = round(genome.vector[i], 3)
        lines.append("core_preferences:")
        for k, v in prefs.items():
            lines.append(f"  {k}: {v}")
        if genome.score is not None:
            lines.append(f"laugh_score: {round(genome.score, 3)}")

    elif isinstance(genome, KickListGenome):
        lines.extend(genome.to_kick_lines(key="evolved_items"))

    elif isinstance(genome, KickBlockGenome):
        lines.append(genome.to_kick_block(directive="").split("\n", 1)[-1])  # reuse its emitter sans directive

    else:
        lines.append(f"# unknown genome type: {type(genome)}")
        if genome.score is not None:
            lines.append(f"score: {genome.score}")

    lines.append(f"# emitted by kickga (GAlib-style) — best score: {genome.score}")
    return "\n".join(lines)


def emit_evolution_history_entry(ga: GASimpleGA, label: str = "ga-session") -> str:
    s = ga.statistics()
    return f"v{ga.generation}: {label} best={round(s.best_score,2)} avg={round(s.avg_score,2)} (kickga)"


# =============================================================================
# Playbook Schema / TAS emitters (task 4: wire into OCS + meta-playbook)
# =============================================================================

def emit_tas_block(tas: "TAS", directive: str = "⫻data/tas") -> str:
    """Emit a canonical ⫻data/tas block from a TAS dataclass (or dict)."""
    if isinstance(tas, dict):
        t = tas
    else:
        t = tas.to_dict() if hasattr(tas, "to_dict") else tas
    lines = [directive]
    lines.append(f"id: {t.get('id')}")
    lines.append(f"raw_input: {t.get('raw_input', '')[:120]}")
    lines.append(f"atomic_intent: {t.get('atomic_intent', '')[:140]}")
    lines.append("signals:")
    for k, v in t.get("signals", {}).items():
        lines.append(f"  {k}: {v}")
    lines.append(f"extracted_by: {t.get('extracted_by', 'KickForge')}")
    lines.append(f"timestamp: {t.get('timestamp')}")
    lines.append("# source: kickga + UnifiedPlaybookSchema")
    return "\n".join(lines)


def emit_ptas_block(ptas: "PTAS", directive: str = "⫻data/ptas") -> str:
    if isinstance(ptas, dict):
        p = ptas
    else:
        p = ptas.to_dict() if hasattr(ptas, "to_dict") else ptas
    lines = [directive]
    lines.append(f"id: {p.get('id')}")
    lines.append(f"source_tas_id: {p.get('source_tas_id')}")
    lines.append(f"purified_intent: {p.get('purified_intent', '')[:140]}")
    lines.append("constraints:")
    for c in p.get("constraints", []):
        lines.append(f"  - {c}")
    ea = p.get("ethical_alignment", {})
    lines.append(f"ethical_alignment: {ea.get('status', 'aligned')}")
    if ea.get("notes"):
        lines.append(f"  notes: {ea['notes']}")
    lines.append(f"consent_status: {p.get('consent_status')}")
    lines.append(f"ready_for_pipeline: {p.get('ready_for_pipeline')}")
    lines.append("# source: kickga (KickGuard-purified)")
    return "\n".join(lines)


def emit_anchor_block(anchor: "Anchor", directive: str = "⫻data/anchor") -> str:
    if isinstance(anchor, dict):
        a = anchor
    else:
        a = anchor.to_dict() if hasattr(anchor, "to_dict") else anchor
    lines = [directive]
    lines.append(f"anchor_id: {a.get('anchor_id')}")
    lines.append(f"ptas_id: {a.get('ptas_id')}")
    lines.append(f"stability_score: {a.get('stability_score')}")
    lines.append(f"pipe_channel: {a.get('pipe_channel')}")
    sc = a.get("somatic_context", {})
    lines.append("somatic_context:")
    for k, v in sc.items():
        lines.append(f"  {k}: {v}")
    if a.get("ritual_frame"):
        lines.append(f"ritual_frame: {a['ritual_frame']}")
    lines.append("# source: kickga (EmbodiedPipe)")
    return "\n".join(lines)


def emit_playbook_event_block(
    event: Union["PlaybookEvent", Dict[str, Any]],
    directive: str = "⫻playbook:event",
    indent: str = "",
) -> str:
    """Emit a single playbook event in KickLang-friendly form.

    Use indent="  " (or "    ") for nested output inside a cycle.
    """
    if isinstance(event, dict):
        e = event
    else:
        e = event.to_dict() if hasattr(event, "to_dict") else event

    prefix = indent
    lines = [f"{prefix}{directive}" if directive else ""]
    lines.append(f"{prefix}  event_id: {e.get('event_id')}")
    lines.append(f"{prefix}  event_type: {e.get('event_type')}")
    lines.append(f"{prefix}  source: {e.get('source')}")
    lines.append(f"{prefix}  timestamp: {e.get('timestamp')}")
    payload = e.get("payload", {})
    lines.append(f"{prefix}  payload:")
    for k, v in payload.items():
        val = v if not isinstance(v, (dict, list)) else str(v)
        lines.append(f"{prefix}    {k}: {val}")
    # drop leading empty line if no directive was wanted
    return "\n".join(line for line in lines if line is not None and line != "")


def emit_full_playbook_cycle(
    genome: GAGenome,
    version: str = "ga-tas-1.0",
) -> str:
    """
    Given a best-of-run TAS-parameter genome, simulate the full happy-path
    playbook cycle (TAS_EXTRACTED → ... → CYCLE_SEALED) and emit a rich
    KickLang block containing the domain objects + event stream.

    This is the primary integration point between kickga evolution and
    OCS / UnifiedPlaybookSchema consumers.
    """
    if not isinstance(genome, KickVectorGenome):
        return "# emit_full_playbook_cycle requires a KickVectorGenome (TAS vector)"

    # Use the simulation helper from fitness (which already pulls in schema)
    from .fitness import simulate_playbook_cycle_from_vector  # local import to avoid circulars at load
    cycle = simulate_playbook_cycle_from_vector(genome.vector)

    if "error" in cycle:
        return f"# {cycle['error']}"

    tas_d = cycle["tas"]
    ptas_d = cycle["ptas"]
    anchor_d = cycle["anchor"]
    events = cycle["events"]

    lines: List[str] = ["⫻playbook:cycle"]
    lines.append(f"id: tas_cycle_{version}_{genome.name or 'evolved'}")
    lines.append(f"version: {version}")
    lines.append(f"ga_score: {genome.score}")
    lines.append("")

    lines.append("# --- Domain Objects (canonical) ---")
    lines.append(emit_tas_block(tas_d))
    lines.append("")
    lines.append(emit_ptas_block(ptas_d))
    lines.append("")
    lines.append(emit_anchor_block(anchor_d))
    lines.append("")

    lines.append("# --- Event Stream (16-type schema) ---")
    lines.append("⫻playbook:events")
    for ev in events:
        # Use indent for clean nested KickLang-style output
        block = emit_playbook_event_block(ev, directive="event:", indent="  ")
        lines.append(block)
    lines.append("")

    lines.append(f"# cycle_summary: {cycle.get('cycle_summary')}")
    lines.append("# emitted by kickga (wired to UnifiedPlaybookSchema)")
    lines.append(f"# best_vector[:4]: { [round(x,3) for x in genome.vector[:4]] }")

    return "\n".join(lines)
