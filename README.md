# t450

t450 — Meta-infrastructure and agentic experimentation workspace.

Part of Denis Oliver Kropp’s t-series of personal repositories exploring MetaForge, KickLang, TAS, MCP skills, and symbiotic co-agency.

## Current Experiments

- **GAlib + KickLang integration** (`kickga/`)
  - GAlib-inspired GA engine in Python (GASimpleGA, KickVectorGenome, etc.)
  - Direct support for evolving HumorDNA vectors, symbolic lists, and declarative blocks
  - KickLang-native spec loading (`⫻ga:experiment`) + emission of evolved `⫻humor:dna:block` artifacts
  - Self-referential demo: improve the same DNA structures used by Iterative Laugh Team / HumorForge

Run the demo:

```bash
cd kickga
python examples/evolve_humor_dna.py
# or
python -m kickga.examples.evolve_humor_dna
```

See `kickga/docs/KickLang_GAlib_Integration.md` and the `.kl.md` companion.

