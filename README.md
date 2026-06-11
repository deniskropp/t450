# t450

t450 — Meta-infrastructure and agentic experimentation workspace.

Part of Denis Oliver Kropp’s t-series of personal repositories exploring MetaForge, KickLang, TAS, MCP skills, and symbiotic co-agency.

## Current Experiments

- **GAlib + KickLang integration** (`kickga/`)
  - GAlib-inspired GA engine in Python (GASimpleGA, KickVectorGenome, etc.)
  - Direct support for evolving HumorDNA vectors, symbolic lists, and declarative blocks
  - KickLang-native spec loading (`⫻ga:experiment`) + emission of evolved `⫻humor:dna:block` artifacts
  - **TAS / Playbook Schema wiring** (via `/unified-playbook-schema`): evolve coherence, anchor stability, consent/ethical weights, resequence tendency etc. as first-class fitness dimensions. Emit full `⫻playbook:cycle` (TAS/PTAS/Anchor + 16 typed events) ready for OCS meta-playbook / KickGuard.
  - Self-referential demo: improve the same DNA structures used by Iterative Laugh Team / HumorForge

Run the demo:

```bash
cd kickga
python examples/evolve_humor_dna.py
# or
python -m kickga.examples.evolve_humor_dna
```

See `kickga/docs/KickLang_GAlib_Integration.md` and the `.kl.md` companion.

## Canonical Schemas (delivered)

- **Unified Playbook Schema** (`references/UnifiedPlaybookSchema.ts`)
  - Complete TypeScript domain model for TAS, PTAS, Anchor, and the 16 core `PlaybookEvent` types (TAS_EXTRACTED → CYCLE_SEALED).
  - Activated via `/unified-playbook-schema`.
  - Authoritative copy lives in `~/.grok/skills/unified-playbook-schema/references/`.
  - See also `references/playbook-cycle.example.ts` (local) and the full executable example in the skill.
  - Use for future TypeScript state machines, validation layers, KickLang/OCS bridges, or when evolving kickga to consume typed TAS/PTAS payloads.

