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
    # Playbook / TAS emitters (task 4)
    emit_tas_block,
    emit_ptas_block,
    emit_anchor_block,
    emit_playbook_event_block,
    emit_full_playbook_cycle,
)
from .fitness import (
    FitnessFunction,
    make_vector_target_fitness,
    make_humor_dna_fitness,
    humor_dna_fitness,
    make_tas_coherence_fitness,
    tas_coherence_fitness,
    simulate_playbook_cycle_from_vector,
)

from .playbook_schema import (
    Role, ConsentStatus, EthicalAlignment, CoherenceStatus,
    TAS, PTAS, Anchor,
    PlaybookEvent, create_playbook_event,
    tas_from_genome_vector, ptas_from_tas, anchor_from_ptas,
    # All 16 payload types for direct construction when needed
    TasExtractedPayload, ConsentGrantedPayload, ConsentDeniedPayload,
    AnchorCreatedPayload, PipelineReadyPayload,
    ResonanceHighPayload, ResonanceLowPayload,
    SignalTransmittedPayload, ArtifactCreatedPayload,
    CoherenceHighPayload, CoherenceLowPayload,
    ResequenceToAnchorPayload, ResequenceToPipelinePayload, ResequenceToDecisionPayload,
    NoResequenceNeededPayload, CycleSealedPayload,
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
    "emit_tas_block",
    "emit_ptas_block",
    "emit_anchor_block",
    "emit_playbook_event_block",
    "emit_full_playbook_cycle",
    "FitnessFunction",
    "make_vector_target_fitness",
    "make_humor_dna_fitness",
    "humor_dna_fitness",
    "make_tas_coherence_fitness",
    "tas_coherence_fitness",
    "simulate_playbook_cycle_from_vector",
    # Playbook schema (UnifiedPlaybookSchema Python mirror)
    "Role", "ConsentStatus", "EthicalAlignment", "CoherenceStatus",
    "TAS", "PTAS", "Anchor",
    "PlaybookEvent", "create_playbook_event",
    "tas_from_genome_vector", "ptas_from_tas", "anchor_from_ptas",
    "TasExtractedPayload", "ConsentGrantedPayload", "ConsentDeniedPayload",
    "AnchorCreatedPayload", "PipelineReadyPayload",
    "ResonanceHighPayload", "ResonanceLowPayload",
    "SignalTransmittedPayload", "ArtifactCreatedPayload",
    "CoherenceHighPayload", "CoherenceLowPayload",
    "ResequenceToAnchorPayload", "ResequenceToPipelinePayload", "ResequenceToDecisionPayload",
    "NoResequenceNeededPayload", "CycleSealedPayload",
]
