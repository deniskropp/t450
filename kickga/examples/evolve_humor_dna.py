#!/usr/bin/env python3
"""
Demo: Evolve a HumorDNA vector using kickga (GAlib-inspired) to maximize "laugh score".

This is the canonical self-referential integration example:
- KickLang ecosystem already has evolving HumorDNA (humor_dna-0.9.2.kick, HumorForge, Iterative Laugh Team Gen2)
- We treat the numeric preference vector as a GA genome (exactly like GA1DArrayGenome in GAlib)
- Fitness is derived from the same heuristics that score jokes in the HumorForge logic
- Result can be emitted as a fresh ⫻humor:dna:block ready to drop into a .kick file

Also demonstrates (Path C):
- Evolving TAS parameters using the Python mirror of UnifiedPlaybookSchema
- Fitness based on coherence, anchor stability, consent/ethics, low resequence/drift
- Full emission of TAS/PTAS/Anchor + 16-event playbook cycle (⫻playbook:cycle)
- Direct bridge from GA search → OCS / meta-playbook / KickGuard consumers

Run:
    python -m kickga.examples.evolve_humor_dna
    # or after PYTHONPATH=.
    python kickga/examples/evolve_humor_dna.py
"""

import sys
from pathlib import Path

# Make package importable when run directly from the worktree
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from kickga import (
    KickVectorGenome,
    GASimpleGA,
    make_humor_dna_fitness,
    make_tas_coherence_fitness,
    emit_kick_dna_block,
    emit_full_playbook_cycle,
    load_kick_ga_spec,
    create_ga_from_kick,
)


# A seed DNA very close to the real artifacts in the user's projects (t321, t314 humor_dna)
SEED_DNA = {
    "version": "0.9.2",
    "core_preferences": {
        "meta_ai_irony_literal_roasts": 9,
        "kicklang_command_wordplay": 10,
        "multi_agent_deadlock": 9,
        "short_setups": 10,
        "tight_punchlines": 10,
        "direct_kicklang_command_usage": 10,
        "logic_loop_recursion": 12,
        "animal_swarm_logic_loops": 13,
        "monkey_typewriter_banana_chaos": 14,
        "iterative_laugh_team_deadlock": 13,
        "deutsche_query_ironie": 12,
        "animal_puns": 8,
        "tech_fails": 7,
        "self_deprecating": 9,
    },
    "evolution_history": [
        "v0.1: baseline meta-AI irony",
        "v0.9.2: deutsche KI-Ironie + swarm recursion (pre-GA)",
    ],
    "top_theme": "Auffassung-Annahme-Auslegung Absurdität in animal-swarm KickLang",
}


def main():
    print("=== kickga + KickLang : Evolving Humor DNA ===\n")

    # --- 1. Pure Python path (explicit) ---
    print("--- Path A: Explicit Python GA construction ---")
    fitness = make_humor_dna_fitness()

    # Build initial pop biased around the seed
    keys = list(SEED_DNA["core_preferences"].keys())
    base_vec = [float(SEED_DNA["core_preferences"][k]) for k in keys]
    bounds = [(0.0, 16.0)] * len(base_vec)

    initial_pop = []
    for i in range(36):
        v = [round(b[0] + (b[1]-b[0]) * (0.3 + 0.7*__import__('random').random()), 3) for b in bounds]
        # inject seed bias into ~1/4 of pop
        if i < 9:
            for j in range(len(base_vec)):
                v[j] = round(0.65 * base_vec[j] + 0.35 * v[j], 3)
        g = KickVectorGenome(vector=v, bounds=bounds, name=f"humor_dna_{i}")
        initial_pop.append(g)

    ga = GASimpleGA(initial_pop, fitness_fn=fitness, maximize=True)
    ga.populationSize(36)
    ga.pCrossover = 0.88
    ga.pMutation = 0.018
    ga.nGenerations = 55

    stats = ga.evolve()

    best = ga.best()
    print(f"Generations run: {ga.generation}")
    print(f"Best laugh_score: {best.score:.3f}" if best and best.score else "no best")
    print(f"Avg at end: {stats.avg_score:.2f}")

    if best:
        print("\nEvolved DNA vector (first 8 loci):")
        print("  ", best.vector[:8])

        kick_block = emit_kick_dna_block(best, version="ga-1.0")
        print("\n--- Emitted KickLang block (paste into .kick or dna file) ---")
        print(kick_block[:1200] + "\n...")

    # --- 2. KickLang declarative spec path ---
    print("\n--- Path B: Load from KickLang-style spec string ---")
    spec = """
# ⫻ga:experiment — evolve humor DNA for higher swarm laughter
⫻ga:experiment
id: EvolveHumorDNA_KickGA_v1
genome: vector
pop_size: 32
generations: 40
p_crossover: 0.9
p_mutation: 0.02
fitness: humor_dna
vector_length: 14
# bounds_low: [0,0,...]  (optional)
"""

    ga2 = create_ga_from_kick(spec, seed=SEED_DNA)
    ga2.evolve(35)
    best2 = ga2.best()
    print(f"Spec-driven best laugh_score: {best2.score:.3f}" if best2 and best2.score else "n/a")

    if best2:
        print("\nSpec-driven evolved KickLang block:")
        print(emit_kick_dna_block(best2, version="ga-spec-1.0")[:900])

    print("\n=== Integration complete. Use the emitted blocks in your KickLang codex / humor modules. ===")
    print("Next ideas: evolve whole ⫻plan/team lists, evolve OCS weight vectors, evolve pipeline stage order.")

    # --- 3. TAS / UnifiedPlaybookSchema path (new in task 4) ---
    print("\n--- Path C: Evolve TAS parameters (coherence, anchor stability, resequence tendency...) ---")
    print("Fitness rewards high-coherence, stable anchors, strong consent/ethics, low resequence/drift.")
    print("This directly wires kickga genomes to the canonical playbook schema (TAS/PTAS/Anchor + 16 events).")

    tas_fitness = make_tas_coherence_fitness()
    tas_length = 8
    tas_bounds = [(0.35, 0.98)] * tas_length   # sensible normalized ranges for most params

    initial_tas_pop = []
    for i in range(28):
        v = [round(0.55 + __import__('random').random() * 0.38, 3) for _ in range(tas_length)]
        g = KickVectorGenome(vector=v, bounds=tas_bounds, name=f"tas_params_{i}")
        initial_tas_pop.append(g)

    ga_tas = GASimpleGA(initial_tas_pop, fitness_fn=tas_fitness, maximize=True)
    ga_tas.populationSize(28)
    ga_tas.pCrossover = 0.86
    ga_tas.pMutation = 0.022
    ga_tas.nGenerations = 48
    # Make nGenerations effective: disable the plateau-based early stop.
    # The TAS fitness surface can stabilize the best score relatively quickly
    # (elitism + smooth params), so without this the GA would exit after ~10-15 gens
    # even though we asked for 48. This demonstrates control over termination.
    ga_tas.terminate_on_convergence = False

    stats_tas = ga_tas.evolve()
    best_tas = ga_tas.best()

    print(f"TAS GA generations: {ga_tas.generation}")
    print(f"Best TAS/playbook score: {best_tas.score:.3f}" if best_tas and best_tas.score else "n/a")

    if best_tas:
        print("\nEvolved TAS vector (coherence, stability, consent, reseq, ethical, somatic, pipeline, drift):")
        print("  ", [round(x, 3) for x in best_tas.vector])

        # Emit rich playbook cycle (the key integration artifact)
        cycle_block = emit_full_playbook_cycle(best_tas, version="ga-tas-playbook-1.0")
        print("\n--- Emitted ⫻playbook:cycle (TAS/PTAS/Anchor + full event stream) ---")
        print(cycle_block[:1800] + "\n... (truncated)")

        # Also show the pure Python simulation dict for consumers that want objects
        try:
            from kickga.fitness import simulate_playbook_cycle_from_vector
            sim = simulate_playbook_cycle_from_vector(best_tas.vector)
            print(f"\nSimulated cycle contains {len(sim.get('events', []))} events. Final coherence: high")
        except Exception as ex:
            print(f"(simulation detail skipped: {ex})")

    print("\n=== TAS wiring complete. Evolved parameters are now ready for OCS meta-playbook, KickGuard, EmbodiedPipe. ===")


if __name__ == "__main__":
    main()
