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
- Single_Kick parser + t20 compiler → can be extended later with first-class `⫻ga:*` productions or a GA stage in the planner.

## Next Steps (Ideas)

- Evolve entire `⫻role:*` capability lists or PLAN nesting depth.
- Multi-objective (coherence + laugh + consent) with NSGA-style or weighted sum.
- Online GA inside a running KickLang swarm (micro-populations between sessions).
- Persist populations as `⫻state:ga_population` blocks.
- Wire into MCP skill so `⫻cmd/exec kickga-evolve` becomes a first-class OCS action.

---

**This is t450 agentic experimentation at its best:** using the symbolic language of co-agency (KickLang) as both the *object* being evolved and the *medium* that describes the evolutionary experiment.
