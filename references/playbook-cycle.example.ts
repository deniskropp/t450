/**
 * t450/references/playbook-cycle.example.ts
 *
 * Local consumer example for the Unified Playbook Schema in this workspace.
 * 
 * Full authoritative example lives at:
 *   ~/.grok/skills/unified-playbook-schema/examples/full-cycle.example.ts
 *
 * Usage (type check):
 *   npx tsc --noEmit --strict references/playbook-cycle.example.ts references/UnifiedPlaybookSchema.ts
 */

import type {
  TAS,
  PTAS,
  Anchor,
  CreatePlaybookEvent,
  AnyPlaybookEvent,
  PlaybookEventType,
} from "./UnifiedPlaybookSchema";

// Example: construct a minimal TAS_EXTRACTED event with perfect type safety
const exampleTasExtracted: CreatePlaybookEvent<"TAS_EXTRACTED"> = {
  event_id: "evt_demo_001",
  event_type: "TAS_EXTRACTED",
  timestamp: new Date().toISOString(),
  source: "KickForge",
  payload: {
    tas_id: "tas_demo_42",
    raw_input: "Evolve the HumorDNA GA inside kickga using real TAS blocks from living objectives.",
    grounded_context: "t450 + kickga project. User wants the GA to optimize TAS-related parameters inside humor evolution loops.",
    atomic_intent: "Close the loop between GA genomes and canonical TAS/PTAS structures for self-improving meta-infra.",
    signals: {
      cognitive: "Direct mapping from GA fitness to coherence + TAS completion metrics",
      emotional: "Joy at seeing the meta-infrastructure become self-referential",
      somatic: "Hands on keyboard after a walk; strong forward momentum",
    },
  },
};

console.log("Successfully created typed event:", exampleTasExtracted.event_type);

// You can now feed AnyPlaybookEvent[] streams into state machines, 
// OCS protocol layers, KickLang emitters, or future TypeScript orchestrators in t450.

export const demoEvent = exampleTasExtracted;
