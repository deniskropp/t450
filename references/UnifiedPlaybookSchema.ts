// Unified Playbook Meta-Schema (TypeScript)
// Canonical domain model bringing together TAS, PTAS, Anchor, 
// all 16 event payloads, the event envelope, cross-references, 
// enumerations, and type unions.
// This is the complete, strongly-typed schema for the entire playbook system.
//
// LOCAL COPY for t450 workspace (meta-infrastructure experimentation).
// Authoritative source: ~/.grok/skills/unified-playbook-schema/references/UnifiedPlaybookSchema.ts
// Activated by: /unified-playbook-schema
//
// Core resource for: OCS, KickLang, Meta-Playbook, Three-Agent-Core (KickForge / KickFlow / KickGuard),
// TAS extraction/purification, EmbodiedPipe anchoring, and FSM-driven agentic flows.
//
// See SKILL.md (in the unified-playbook-schema skill) for full context and recommended usage.

export type Role =
  | "roleDima"
  | "roleDenis"
  | "KickForge"
  | "KickFlow"
  | "KickGuard"
  | "EmbodiedPipe";

export type ConsentStatus = "granted" | "denied" | "pending";

export type EthicalAlignment = "aligned" | "blocked";

export type CoherenceStatus = "high" | "low";

// TAS - Task Atom Structure (core output of KickForge TAS extraction)
export interface TAS {
  id: string;
  raw_input: string;
  grounded_context: string;
  atomic_intent: string;
  signals: {
    cognitive: string;
    emotional: string;
    somatic: string;
  };
  extracted_by: "KickForge";
  timestamp: string;
}

// PTAS - Purified Task Atom Structure (post-consent / KickGuard alignment)
export interface PTAS {
  id: string;
  source_tas_id: string;
  purified_intent: string;
  constraints: string[];
  ethical_alignment: {
    status: EthicalAlignment;
    notes?: string;
  };
  consent_status: ConsentStatus;
  ready_for_pipeline: boolean;
  purified_by: "KickForge";
  timestamp: string;
}

// Anchor - EmbodiedPipe somatic/ritual grounding point
export interface Anchor {
  anchor_id: string;
  ptas_id: string;
  timestamp: string;
  somatic_context: {
    valence: string;
    intensity: number;
    notes?: string;
  };
  ritual_frame?: string;
  pipe_channel: string;
  stability_score: number;
  created_by: "EmbodiedPipe";
}

// Unified Event Envelope — the fundamental carrier for all playbook transitions
export interface PlaybookEvent<TPayload> {
  event_id: string;
  event_type: PlaybookEventType;
  timestamp: string;
  source: Role;
  payload: TPayload;
}

// ============================================
// Event Payload Types (exactly 16 core FSM transitions)
// ============================================

export interface TasExtractedPayload {
  tas_id: string;
  raw_input: string;
  grounded_context: string;
  atomic_intent: string;
  signals: {
    cognitive: string;
    emotional: string;
    somatic: string;
  };
}

export interface ConsentGrantedPayload {
  ptas_id: string;
  source_tas_id: string;
  purified_intent: string;
  ethical_alignment: "aligned";
  consent_status: "granted";
}

export interface ConsentDeniedPayload {
  ptas_id: string;
  reason: string;
  ethical_alignment: "blocked";
  consent_status: "denied";
}

export interface AnchorCreatedPayload {
  anchor_id: string;
  ptas_id: string;
  somatic_context: {
    valence: string;
    intensity: number;
    notes?: string;
  };
  ritual_frame?: string;
  pipe_channel: string;
  stability_score: number;
}

export interface PipelineReadyPayload {
  pipeline_id: string;
  steps: Array<{
    step_id: string;
    description: string;
    delegated_to: Role;
  }>;
}

export interface ResonanceHighPayload {
  resonance_score: number;
  context?: string;
  related_anchor_id?: string;
}

export interface ResonanceLowPayload {
  resonance_score: number;
  reason?: string;
  suggested_resequence?: string;
}

export interface SignalTransmittedPayload {
  signal_type: string;
  channel: string;
  payload_summary: string;
  timestamp: string;
}

export interface ArtifactCreatedPayload {
  artifact_id: string;
  artifact_type: string;
  location: string;
  metadata?: Record<string, unknown>;
}

export interface CoherenceHighPayload {
  coherence_status: "high";
  metrics?: Record<string, number>;
  anchor_id?: string;
}

export interface CoherenceLowPayload {
  coherence_status: "low";
  drift_detected: boolean;
  recommended_action: "resequence_to_anchor" | "resequence_to_pipeline" | "halt_for_decision";
}

export interface ResequenceToAnchorPayload {
  reason: string;
  target_ptas_id: string;
  target_anchor_id?: string;
}

export interface ResequenceToPipelinePayload {
  reason: string;
  target_pipeline_id?: string;
  current_step?: string;
}

export interface ResequenceToDecisionPayload {
  decision_context: string;
  available_options: string[];
  current_ptas_id: string;
}

export interface NoResequenceNeededPayload {
  confirmation: string;
  stability_confirmed: boolean;
  current_coherence: CoherenceStatus;
}

export interface CycleSealedPayload {
  cycle_id: string;
  summary: string;
  final_coherence: CoherenceStatus;
  sealed_at: string;
  key_artifacts?: string[];
};

// ============================================
// Event Type Union (canonical for the system — 16 values)
// ============================================

export type PlaybookEventType =
  | "TAS_EXTRACTED"
  | "CONSENT_GRANT"
  | "CONSENT_DENIED"
  | "ANCHOR_CREATED"
  | "PIPELINE_READY"
  | "RESONANCE_HIGH"
  | "RESONANCE_LOW"
  | "SIGNAL_TRANSMITTED"
  | "ARTIFACT_CREATED"
  | "COHERENCE_HIGH"
  | "COHERENCE_LOW"
  | "RESEQUENCE_TO_ANCHOR"
  | "RESEQUENCE_TO_PIPELINE"
  | "RESEQUENCE_TO_DECISION"
  | "NO_RESEQUENCE_NEEDED"
  | "CYCLE_SEALED";

// ============================================
// Unified Discriminated Event Payload Union
// ============================================

export type PlaybookEventPayload =
  | TasExtractedPayload
  | ConsentGrantedPayload
  | ConsentDeniedPayload
  | AnchorCreatedPayload
  | PipelineReadyPayload
  | ResonanceHighPayload
  | ResonanceLowPayload
  | SignalTransmittedPayload
  | ArtifactCreatedPayload
  | CoherenceHighPayload
  | CoherenceLowPayload
  | ResequenceToAnchorPayload
  | ResequenceToPipelinePayload
  | ResequenceToDecisionPayload
  | NoResequenceNeededPayload
  | CycleSealedPayload;

// ============================================
// Utility Types
// ============================================

/** Type-safe event creator helper (maps event_type to precise payload) */
export type CreatePlaybookEvent<T extends PlaybookEventType> = 
  PlaybookEvent<
    T extends "TAS_EXTRACTED" ? TasExtractedPayload :
    T extends "CONSENT_GRANT" ? ConsentGrantedPayload :
    T extends "CONSENT_DENIED" ? ConsentDeniedPayload :
    T extends "ANCHOR_CREATED" ? AnchorCreatedPayload :
    T extends "PIPELINE_READY" ? PipelineReadyPayload :
    T extends "RESONANCE_HIGH" ? ResonanceHighPayload :
    T extends "RESONANCE_LOW" ? ResonanceLowPayload :
    T extends "SIGNAL_TRANSMITTED" ? SignalTransmittedPayload :
    T extends "ARTIFACT_CREATED" ? ArtifactCreatedPayload :
    T extends "COHERENCE_HIGH" ? CoherenceHighPayload :
    T extends "COHERENCE_LOW" ? CoherenceLowPayload :
    T extends "RESEQUENCE_TO_ANCHOR" ? ResequenceToAnchorPayload :
    T extends "RESEQUENCE_TO_PIPELINE" ? ResequenceToPipelinePayload :
    T extends "RESEQUENCE_TO_DECISION" ? ResequenceToDecisionPayload :
    T extends "NO_RESEQUENCE_NEEDED" ? NoResequenceNeededPayload :
    T extends "CYCLE_SEALED" ? CycleSealedPayload :
    never
  >;

/** Example exhaustive event handler. Extend for production state machines. */
export function handlePlaybookEvent(event: PlaybookEvent<PlaybookEventPayload>): void {
  switch (event.event_type) {
    case "TAS_EXTRACTED":
      // handle TasExtractedPayload (typically from KickForge)
      break;
    case "CONSENT_GRANT":
      // handle ConsentGrantedPayload (KickGuard + consent gate passed)
      break;
    case "CONSENT_DENIED":
      // handle ConsentDeniedPayload
      break;
    case "ANCHOR_CREATED":
      // handle AnchorCreatedPayload (EmbodiedPipe)
      break;
    case "PIPELINE_READY":
      // handle PipelineReadyPayload (KickFlow orchestration)
      break;
    case "RESONANCE_HIGH":
      // handle ResonanceHighPayload
      break;
    case "RESONANCE_LOW":
      // handle ResonanceLowPayload — may trigger resequence
      break;
    case "SIGNAL_TRANSMITTED":
      // handle SignalTransmittedPayload (EmbodiedPipe / cross-agent)
      break;
    case "ARTIFACT_CREATED":
      // handle ArtifactCreatedPayload
      break;
    case "COHERENCE_HIGH":
      // handle CoherenceHighPayload (KickGuard integrity)
      break;
    case "COHERENCE_LOW":
      // handle CoherenceLowPayload — drift handling
      break;
    case "RESEQUENCE_TO_ANCHOR":
      // handle ResequenceToAnchorPayload
      break;
    case "RESEQUENCE_TO_PIPELINE":
      // handle ResequenceToPipelinePayload
      break;
    case "RESEQUENCE_TO_DECISION":
      // handle ResequenceToDecisionPayload
      break;
    case "NO_RESEQUENCE_NEEDED":
      // handle NoResequenceNeededPayload
      break;
    case "CYCLE_SEALED":
      // handle CycleSealedPayload — terminal happy path
      break;
    default:
      // Exhaustiveness check — TypeScript will error if a new PlaybookEventType is added without a case
      const _exhaustive: never = event.event_type;
      break;
  }
}

// ============================================
// Convenience
// ============================================

export type AnyPlaybookEvent = PlaybookEvent<PlaybookEventPayload>;

export default {
  Role,
  ConsentStatus,
  EthicalAlignment,
  CoherenceStatus,
  PlaybookEventType,
  PlaybookEventPayload,
  CreatePlaybookEvent,
  handlePlaybookEvent,
};
