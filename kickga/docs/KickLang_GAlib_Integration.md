# GAlib + KickLang Integration (t450)

**Status:** Initial implementation (v0.1)  
**Location:** This worktree (`kickga/`)  
**Inspiration:** Matthew Wall's GAlib (C++ Genetic Algorithm Library) — genomes, GASimpleGA, selectors, scaling, classic operators.

## Why?

KickLang already contains strong evolutionary motifs:

- `humor_dna-*.kick` + `evolution_history`
- HumorForge (DNAVisualizer, iterative scoring + `updateDNA`)
- Iterative Laugh Team Gen2, "evolution-predictor" skill
- Dynamic weighting (`⫻cmd/weight`), swarm loops, TAS purification cycles

Genetic Algorithms give us a principled, population-based, fitness-driven way to **actually search** the space of possible:

- Numeric "DNA" vectors (HumorDNA core_preferences, role weights, OCS var values)
- Symbolic lists (signature jokes, affirm lists, banned structures, pipeline stages)
- Whole declarative blocks / plan fragments

Instead of only hand-tuning or predictor-based forecasting, we can run real evolutionary loops that improve co-agency artifacts.

## Architecture

```
kickga/
├── genome.py          # GAGenome base + Kick*Genome (vector/list/block) — mirrors GA1DArrayGenome etc.
├── ga.py              # GASimpleGA + GAStatistics + Selectors + Scaling (roulette, tournament, elitism)
├── operators.py       # gaussian, uniform, order-crossover, swap — reusable and Kick-friendly
├── fitness.py         # humor_dna_fitness (self-referential), vector target, pluggable
├── kick_bridge.py     # load_kick_ga_spec(), create_ga_from_kick(), emit_kick_dna_block()
├── examples/
│   ├── evolve_humor_dna.py
│   └── humor_dna_ga_spec.kick
└── docs/
```

The Python implementation is deliberately **GAlib-flavored** in naming and flow so that moving to a real GAlib C++ component later (or calling out via subprocess/FFI) is a small conceptual jump.

## KickLang Syntax Extensions (Proposed)

We use existing ⫻ directive style for GA specs (no compiler change required for v0.1).

```kick
⫻ga:experiment
id: EvolveHumorDNA_v1
genome: vector          # vector | list | block
pop_size: 42
generations: 70
p_crossover: 0.87
p_mutation: 0.019
fitness: humor_dna      # humor_dna | target | <custom>
vector_length: 14
```

Results are emitted as first-class KickLang blocks:

```kick
⫻humor:dna:block
id: EvolveHumorDNA_ga-1.0
core_preferences:
  monkey_typewriter_banana_chaos: 13.82
  ...
laugh_score: 13.9
# emitted by kickga (GAlib-style)
```

You can also evolve:

- `⫻plan/team` member order / presence
- `⫻data/var` weight vectors for Sentinel dynamic weighting
- `evolution_history` + `signature_jokes` via list genomes
- Full pipeline fragments via block genomes

## Usage

```python
from kickga import create_ga_from_kick, emit_kick_dna_block

with open("humor_dna_ga_spec.kick") as f:
    spec = f.read()

ga = create_ga_from_kick(spec, seed=current_humor_dna_dict)
ga.evolve()

best = ga.best()
print(emit_kick_dna_block(best, version="ga-1.0"))
```

Or drive 100% from Python (see `examples/evolve_humor_dna.py`).

## Native GAlib Path (Future / Optional)

When you want the real C++ performance and the full GAlib feature set (GASteadyStateGA, custom replacement, sharing, etc.):

1. Build GAlib (https://github.com/s-martin/galib or original lancet.mit.edu/ga)
2. Write a thin CLI or shared-lib wrapper that accepts JSON genomes + fitness callback (or pre-defined objectives).
3. Call it from `kickga.native` or directly from a KickLang runtime step.

A minimal stub lives in `native/` (to be added) showing the GAlib include + GA1DArrayGenome<float> pattern that matches our `KickVectorGenome`.

## Relation to Existing Pieces

- `kicklang-evolution-predictor` skill → forecasting / TAS roadmap. kickga → actual population search.
- HumorForge DNA + scoring → the primary fitness oracle today.
- OCS / TAS / meta-playbook → the consumers of the evolved artifacts (weights, lists, blocks).
- **Unified Playbook Schema** (via `/unified-playbook-schema` + `kickga/playbook_schema.py`) → TAS/PTAS/Anchor + 16 event types are now first-class evolvable dimensions and emittable artifacts.
- Single_Kick parser + t20 compiler → can be extended later with first-class `⫻ga:*` productions or a GA stage in the planner.

## Next Steps (Ideas)

- Evolve entire `⫻role:*` capability lists or PLAN nesting depth.
- Multi-objective (coherence + laugh + consent) with NSGA-style or weighted sum.
- Online GA inside a running KickLang swarm (micro-populations between sessions).
- Persist populations as `⫻state:ga_population` blocks.
- Wire into MCP skill so `⫻cmd/exec kickga-evolve` becomes a first-class OCS action.

## TAS / Playbook Schema Integration (v0.2+)

kickga is now wired to the canonical **Unified Playbook Schema** (delivered by `/unified-playbook-schema`).

- `kickga/playbook_schema.py` = Python dataclass mirror of the TS schema (TAS, PTAS, Anchor, all 16 `PlaybookEvent` types, `create_playbook_event`, Role/ConsentStatus/etc enums).
- New fitness: `tas_coherence_fitness` / `make_tas_coherence_fitness()` — evolves 8-dimensional vectors representing:
  `coherence_target`, `anchor_stability`, `consent_weight`, `resequence_tendency`, `ethical_threshold`, `somatic_valence`, `pipeline_efficiency`, `drift_tolerance`
- New emitters:
  - `emit_tas_block()`, `emit_ptas_block()`, `emit_anchor_block()`
  - `emit_full_playbook_cycle(genome)` → produces a complete `⫻playbook:cycle` containing domain objects + the full event stream (TAS_EXTRACTED ... CYCLE_SEALED)
- `KickGAConfig` + `⫻ga:experiment` now understand `fitness: tas_coherence` (and optional `tas_keys`).
- The main demo (`evolve_humor_dna.py` Path C) runs a full TAS evolution and emits a ready-to-consume playbook cycle.

These artifacts are designed to be consumed by:
- OCS protocol layers
- KickGuard (consent + coherence gates)
- KickFlow (pipeline construction from PTAS)
- EmbodiedPipe (anchor + somatic signals)
- Any state machine using the discriminated `PlaybookEventType` union.

Example spec snippet (simple GA form):
```kick
⫻ga:experiment
id: EvolveTASForMetaPlaybook
genome: vector
fitness: tas_coherence
vector_length: 8
tas_keys: [coherence_target, anchor_stability, consent_weight, resequence_tendency, ...]
generations: 45
```

### New Meta-Playbook Examples (in kickga/examples/)

The directory now contains full KickLang Meta-Playbook modules (v2.1) that wrap GA evolution:

- `tas_coherence_meta_playbook.kick` — Complete 3-agent pipeline: KickForge TAS extraction → KickFlow delegates to kickga GA (using `tas_coherence_fitness`) → KickGuard coherence gate + Anchor + emission of all 16 `PlaybookEvent` types + final `⫻playbook:cycle`. Directly compatible with `kickga.playbook_schema` and the TS `UnifiedPlaybookSchema`.
- `meta_playbook_humor_dna_evolution.kick` — Elevates the classic HumorDNA GA into a full Meta-Playbook with role consolidation, ethics on laugh coherence, optional playbook event emission, and backward-compatible embedded `⫻ga:experiment`.
- `playbook_cycle_after_ga.kick` — Focused post-GA stage: reconstructs TAS/PTAS/Anchor from any evolved vector, emits the canonical 16-event stream, and seals a `⫻playbook:cycle`. Can be chained after any kickga run.

These files follow the guidelines from the `/kicklang-meta-playbook` skill and can be used as:
- Human-readable ritual/affirmation specs
- Input to future full KickLang compilers or OCS orchestrators
- Documentation of how the Python kickga library maps to typed playbook artifacts

Load the embedded `⫻ga:experiment` blocks with the existing `create_ga_from_kick()` for immediate execution. The richer `module<...>` structure is ready for higher-level orchestration.

---

**This is t450 agentic experimentation at its best:** using the symbolic language of co-agency (KickLang) as both the *object* being evolved and the *medium* that describes the evolutionary experiment.
