"""
kickga — GAlib-inspired Genetic Algorithms for KickLang.

Integrates classic GA components (in the spirit of Matthew Wall's GAlib)
with KickLang symbolic structures, DNA vectors (HumorDNA, role prefs,
TAS parameters), and co-agency evolution loops.

Usage:
    from kickga import KickVectorGenome, GASimpleGA
    ...
"""

__version__ = "0.1.0"
__galib_inspired__ = "GAlib 2.4 / 3.x concepts (genomes, GASimpleGA, scaling, selection)"

from .genome import (
    GAGenome,
    KickVectorGenome,
    KickListGenome,
    KickBlockGenome,
)
from .ga import GASimpleGA, GAStatistics, Selectors, Scaling
from .operators import (
    gaussian_mutate,
    uniform_crossover,
    list_swap_mutate,
    list_order_crossover,
)
from .kick_bridge import (
    load_kick_ga_spec,
    emit_kick_dna_block,
    KickGAConfig,
    create_ga_from_kick,
    build_initial_population,
    emit_evolution_history_entry,
)
from .fitness import (
    FitnessFunction,
    make_vector_target_fitness,
    make_humor_dna_fitness,
    humor_dna_fitness,
)

__all__ = [
    "GAGenome",
    "KickVectorGenome",
    "KickListGenome",
    "KickBlockGenome",
    "GASimpleGA",
    "GAStatistics",
    "Selectors",
    "Scaling",
    "gaussian_mutate",
    "uniform_crossover",
    "list_swap_mutate",
    "list_order_crossover",
    "load_kick_ga_spec",
    "emit_kick_dna_block",
    "KickGAConfig",
    "create_ga_from_kick",
    "build_initial_population",
    "emit_evolution_history_entry",
    "FitnessFunction",
    "make_vector_target_fitness",
    "make_humor_dna_fitness",
    "humor_dna_fitness",
]
