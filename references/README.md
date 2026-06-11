# t450 / references

Canonical domain models and type definitions for meta-infrastructure work.

## UnifiedPlaybookSchema.ts
The complete, strongly-typed canonical meta-schema (TAS / PTAS / Anchor + all 16 PlaybookEvent payloads + discriminated unions + `CreatePlaybookEvent<T>` + exhaustive handler).

- Delivered by activating `/unified-playbook-schema`
- Synchronized from `~/.grok/skills/unified-playbook-schema/references/UnifiedPlaybookSchema.ts`
- Recommended for: building FSMs, deriving Zod/JSON Schema validators, KickForge/KickFlow/KickGuard delegation typing, OCS protocol payloads, EmbodiedPipe anchor flows.

## playbook-cycle.example.ts
Minimal local consumer demonstrating typed event construction using `CreatePlaybookEvent`.

For the rich end-to-end happy-path cycle (TAS extraction → consent → anchor → pipeline → resonance → artifacts → coherence → seal), see:

`~/.grok/skills/unified-playbook-schema/examples/full-cycle.example.ts`

## playbook_schema.py
Python dataclass mirror of the full canonical schema (TAS, PTAS, Anchor + all 16 PlaybookEvent payloads + factories).
- Used by kickga for TAS-param evolution and playbook-cycle emission.
- Importable as `from kickga.playbook_schema import TAS, PTAS, create_playbook_event, ...`
- Or directly: `from references.playbook_schema import ...` (re-exports the kickga version).
- The kickga GA can now evolve parameters that directly correspond to these types (see `tas_coherence_fitness` and `emit_full_playbook_cycle`).

## Future
- Python equivalents (TypedDict / Pydantic) can be generated from this source.
- Integration points with kickga genomes (TAS var weighting, coherence-as-fitness).
- Consumption by ocs-protocol-export, ocs-meta-playbook-controller, and other OCS skills.
