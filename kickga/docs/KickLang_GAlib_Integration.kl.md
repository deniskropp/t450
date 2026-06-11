⫻kicklang:module
id: GAlib-KickLang-Integration
version: 0.1
path: kickga/
language: KickLang + Python GA
intent: population-based evolution of symbolic co-agency artifacts

⫻ga:experiment
id: GAlibKickLangBridge
genome_types: [vector, list, block]
primary_fitness: humor_dna (self-referential laugh/coherence scoring)
emit_targets:
  - ⫻humor:dna:block
  - ⫻data/var (weights)
  - ⫻plan/team fragments
  - evolution_history + signature lists
operators_mirrored:
  - GASimpleGA (generational, elitism)
  - GA1DArrayGenome → KickVectorGenome (gaussian + bounds)
  - List/Order crossover + swap for symbolic sequences
  - Roulette + Tournament selection
  - Sigma truncation scaling (stub)

⫻usage:python
from kickga import create_ga_from_kick, emit_kick_dna_block
ga = create_ga_from_kick(open("spec.kick").read(), seed=seed_dna)
ga.evolve(50)
print(emit_kick_dna_block(ga.best()))

⫻usage:kick
⫻ga:experiment
id: EvolveMyDNA
genome: vector
pop_size: 40
generations: 60
p_crossover: 0.87
p_mutation: 0.02
fitness: humor_dna

⫻output:contract
- Always produce at least one valid ⫻* block (humor:dna, ga:result, or data/var)
- Preserve evolution_history when emitting lists
- Score must be attached when known (laugh_score or score:)
- Never mutate immutable affirmation/ritual blocks directly

⫻relation:existing
- kicklang-evolution-predictor (forecast) complements kickga (search)
- HumorForge DNA scoring = canonical fitness oracle
- OCS TAS flow consumes the evolved weights / lists / blocks
- UnifiedPlaybookSchema (TAS/PTAS/Anchor + 16 events) now directly drives kickga genomes + emission
- t20 compiler + Single_Kick parser remain source of truth for syntax; kickga is consumer/producer

⫻future
- First-class ⫻ga:PLAN stage in compiler
- Multi-population island model for swarm co-agency
- Real GAlib native bridge (see native/README.md)
- Online micro-GA inside running KickLang interpreter loop
- Full round-trip: evolve TAS params in kickga → emit ⫻playbook:cycle → feed OCS-meta-playbook-controller / KickGuard state machine
- Python <-> TS schema validation (generate JSON Schema from playbook_schema.py and compare to the TS discriminated union)
