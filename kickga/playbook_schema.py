"""
Python mirror of the canonical Unified Playbook TypeScript Schema.

Source of truth: ~/.grok/skills/unified-playbook-schema/references/UnifiedPlaybookSchema.ts
(and the local t450/references/UnifiedPlaybookSchema.ts copy)

This module provides:
- Enums / literals for Role, ConsentStatus, EthicalAlignment, CoherenceStatus
- Dataclasses: TAS, PTAS, Anchor
- All 16 event payload dataclasses
- PlaybookEvent[T] generic envelope (using typing overloads / runtime type field)
- to_dict / from_dict helpers for KickLang / JSON / OCS interop
- Small factory helpers aligned with CreatePlaybookEvent<T> spirit

Goal: Allow kickga genomes to evolve TAS parameters, emit coherent playbook events,
and feed directly into OCS / KickLang meta-playbook consumers.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Dict, List, Literal, Optional, TypeVar, Union, cast
import json
import uuid
from datetime import datetime


# --- Core Enumerations (match TS exactly) ---

class Role(str, Enum):
    ROLE_DIMA = "roleDima"
    ROLE_DENIS = "roleDenis"
    KICK_FORGE = "KickForge"
    KICK_FLOW = "KickFlow"
    KICK_GUARD = "KickGuard"
    EMBODIED_PIPE = "EmbodiedPipe"


class ConsentStatus(str, Enum):
    GRANTED = "granted"
    DENIED = "denied"
    PENDING = "pending"


class EthicalAlignment(str, Enum):
    ALIGNED = "aligned"
    BLOCKED = "blocked"


class CoherenceStatus(str, Enum):
    HIGH = "high"
    LOW = "low"


# --- Core Domain Objects ---

@dataclass
class TAS:
    id: str
    raw_input: str
    grounded_context: str
    atomic_intent: str
    signals: Dict[str, str]  # cognitive, emotional, somatic
    extracted_by: Literal["KickForge"] = "KickForge"
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "TAS":
        return cls(
            id=d["id"],
            raw_input=d["raw_input"],
            grounded_context=d["grounded_context"],
            atomic_intent=d["atomic_intent"],
            signals=d.get("signals", {}),
            extracted_by=d.get("extracted_by", "KickForge"),
            timestamp=d.get("timestamp", datetime.utcnow().isoformat() + "Z"),
        )


@dataclass
class PTAS:
    id: str
    source_tas_id: str
    purified_intent: str
    constraints: List[str]
    ethical_alignment: Dict[str, Any]  # {"status": "aligned"|"blocked", "notes": ...}
    consent_status: ConsentStatus | str
    ready_for_pipeline: bool
    purified_by: Literal["KickForge"] = "KickForge"
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        if isinstance(self.consent_status, ConsentStatus):
            d["consent_status"] = self.consent_status.value
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "PTAS":
        cs = d.get("consent_status")
        if isinstance(cs, str):
            try:
                cs = ConsentStatus(cs)
            except ValueError:
                pass
        return cls(
            id=d["id"],
            source_tas_id=d["source_tas_id"],
            purified_intent=d["purified_intent"],
            constraints=d.get("constraints", []),
            ethical_alignment=d.get("ethical_alignment", {"status": "aligned"}),
            consent_status=cs,
            ready_for_pipeline=bool(d.get("ready_for_pipeline", False)),
            purified_by=d.get("purified_by", "KickForge"),
            timestamp=d.get("timestamp", datetime.utcnow().isoformat() + "Z"),
        )


@dataclass
class Anchor:
    anchor_id: str
    ptas_id: str
    timestamp: str
    somatic_context: Dict[str, Any]  # valence, intensity, notes
    ritual_frame: Optional[str] = None
    pipe_channel: str = "primary-somatic-consent"
    stability_score: float = 0.8
    created_by: Literal["EmbodiedPipe"] = "EmbodiedPipe"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Anchor":
        return cls(
            anchor_id=d["anchor_id"],
            ptas_id=d["ptas_id"],
            timestamp=d.get("timestamp", datetime.utcnow().isoformat() + "Z"),
            somatic_context=d.get("somatic_context", {}),
            ritual_frame=d.get("ritual_frame"),
            pipe_channel=d.get("pipe_channel", "primary-somatic-consent"),
            stability_score=float(d.get("stability_score", 0.8)),
            created_by=d.get("created_by", "EmbodiedPipe"),
        )


# --- Event Payloads (all 16) ---

@dataclass
class TasExtractedPayload:
    tas_id: str
    raw_input: str
    grounded_context: str
    atomic_intent: str
    signals: Dict[str, str]


@dataclass
class ConsentGrantedPayload:
    ptas_id: str
    source_tas_id: str
    purified_intent: str
    ethical_alignment: Literal["aligned"]
    consent_status: Literal["granted"]


@dataclass
class ConsentDeniedPayload:
    ptas_id: str
    reason: str
    ethical_alignment: Literal["blocked"]
    consent_status: Literal["denied"]


@dataclass
class AnchorCreatedPayload:
    anchor_id: str
    ptas_id: str
    somatic_context: Dict[str, Any]
    ritual_frame: Optional[str] = None
    pipe_channel: str = "primary-somatic-consent"
    stability_score: float = 0.8


@dataclass
class PipelineReadyPayload:
    pipeline_id: str
    steps: List[Dict[str, Any]]  # [{step_id, description, delegated_to: Role str}]


@dataclass
class ResonanceHighPayload:
    resonance_score: float
    context: Optional[str] = None
    related_anchor_id: Optional[str] = None


@dataclass
class ResonanceLowPayload:
    resonance_score: float
    reason: Optional[str] = None
    suggested_resequence: Optional[str] = None


@dataclass
class SignalTransmittedPayload:
    signal_type: str
    channel: str
    payload_summary: str
    timestamp: str


@dataclass
class ArtifactCreatedPayload:
    artifact_id: str
    artifact_type: str
    location: str
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class CoherenceHighPayload:
    coherence_status: Literal["high"]
    metrics: Optional[Dict[str, float]] = None
    anchor_id: Optional[str] = None


@dataclass
class CoherenceLowPayload:
    coherence_status: Literal["low"]
    drift_detected: bool
    recommended_action: Literal[
        "resequence_to_anchor", "resequence_to_pipeline", "halt_for_decision"
    ]


@dataclass
class ResequenceToAnchorPayload:
    reason: str
    target_ptas_id: str
    target_anchor_id: Optional[str] = None


@dataclass
class ResequenceToPipelinePayload:
    reason: str
    target_pipeline_id: Optional[str] = None
    current_step: Optional[str] = None


@dataclass
class ResequenceToDecisionPayload:
    decision_context: str
    available_options: List[str]
    current_ptas_id: str


@dataclass
class NoResequenceNeededPayload:
    confirmation: str
    stability_confirmed: bool
    current_coherence: CoherenceStatus | str


@dataclass
class CycleSealedPayload:
    cycle_id: str
    summary: str
    final_coherence: CoherenceStatus | str
    sealed_at: str
    key_artifacts: Optional[List[str]] = None


# Union of all payload types (for typing)
PlaybookEventPayload = Union[
    TasExtractedPayload,
    ConsentGrantedPayload,
    ConsentDeniedPayload,
    AnchorCreatedPayload,
    PipelineReadyPayload,
    ResonanceHighPayload,
    ResonanceLowPayload,
    SignalTransmittedPayload,
    ArtifactCreatedPayload,
    CoherenceHighPayload,
    CoherenceLowPayload,
    ResequenceToAnchorPayload,
    ResequenceToPipelinePayload,
    ResequenceToDecisionPayload,
    NoResequenceNeededPayload,
    CycleSealedPayload,
]


# Event type literals (the 16 canonical ones)
PlaybookEventType = Literal[
    "TAS_EXTRACTED",
    "CONSENT_GRANT",
    "CONSENT_DENIED",
    "ANCHOR_CREATED",
    "PIPELINE_READY",
    "RESONANCE_HIGH",
    "RESONANCE_LOW",
    "SIGNAL_TRANSMITTED",
    "ARTIFACT_CREATED",
    "COHERENCE_HIGH",
    "COHERENCE_LOW",
    "RESEQUENCE_TO_ANCHOR",
    "RESEQUENCE_TO_PIPELINE",
    "RESEQUENCE_TO_DECISION",
    "NO_RESEQUENCE_NEEDED",
    "CYCLE_SEALED",
]


@dataclass
class PlaybookEvent:
    """Generic envelope (mirrors TS PlaybookEvent<TPayload>)."""
    event_id: str
    event_type: PlaybookEventType
    timestamp: str
    source: Role | str
    payload: Dict[str, Any]  # raw dict form for maximum KickLang/JSON compatibility

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        if isinstance(self.source, Role):
            d["source"] = self.source.value
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "PlaybookEvent":
        src = d.get("source")
        if isinstance(src, str):
            try:
                src = Role(src)
            except ValueError:
                pass
        return cls(
            event_id=d["event_id"],
            event_type=cast(PlaybookEventType, d["event_type"]),
            timestamp=d.get("timestamp", datetime.utcnow().isoformat() + "Z"),
            source=src,
            payload=d.get("payload", {}),
        )


# --- Factories (CreatePlaybookEvent<T> spirit + convenience) ---

def new_event_id() -> str:
    return f"evt_{uuid.uuid4().hex[:12]}"


def create_playbook_event(
    event_type: PlaybookEventType,
    source: Role | str,
    payload: PlaybookEventPayload | Dict[str, Any],
) -> PlaybookEvent:
    """Typed-ish event factory. Payload can be dataclass or plain dict."""
    if hasattr(payload, "to_dict"):
        payload_dict = payload.to_dict()  # type: ignore[attr-defined]
    elif isinstance(payload, dict):
        payload_dict = payload
    else:
        payload_dict = asdict(payload) if hasattr(payload, "__dataclass_fields__") else dict(payload)

    return PlaybookEvent(
        event_id=new_event_id(),
        event_type=event_type,
        timestamp=datetime.utcnow().isoformat() + "Z",
        source=source if isinstance(source, (Role, str)) else str(source),
        payload=payload_dict,
    )


# --- TAS/PTAS/Anchor helpers for GA consumption ---

def tas_from_genome_vector(
    vector: List[float],
    keys: Optional[List[str]] = None,
    raw_input: str = "Evolved TAS parameters from kickga",
) -> TAS:
    """Utility: turn a KickVectorGenome vector into a minimal TAS for playbook flows."""
    k = keys or [
        "coherence_target", "anchor_stability", "consent_weight", "resequence_tendency",
        "ethical_threshold", "somatic_valence", "pipeline_efficiency", "drift_tolerance"
    ]
    # Map first N values (pad if needed)
    vals = list(vector)[:len(k)] + [0.7] * max(0, len(k) - len(vector))
    signals = {
        "cognitive": f"evolved:{round(vals[0],3)}",
        "emotional": f"evolved:{round(vals[1] if len(vals)>1 else 0.6,3)}",
        "somatic": f"evolved:{round(vals[2] if len(vals)>2 else 0.75,3)}",
    }
    return TAS(
        id=f"tas_ga_{uuid.uuid4().hex[:8]}",
        raw_input=raw_input,
        grounded_context="kickga + UnifiedPlaybookSchema evolution",
        atomic_intent="Optimize TAS parameters for higher coherence and lower resequence rate in OCS flows.",
        signals=signals,
    )


def ptas_from_tas(tas: TAS, consent: ConsentStatus = ConsentStatus.GRANTED) -> PTAS:
    """Simple purification step (KickGuard simulation)."""
    return PTAS(
        id=f"ptas_{tas.id}",
        source_tas_id=tas.id,
        purified_intent=tas.atomic_intent + " [purified via ga-evolved constraints]",
        constraints=["coherence >= 0.75", "stability >= 0.65", "consent explicit"],
        ethical_alignment={"status": EthicalAlignment.ALIGNED.value, "notes": "ga-optimized"},
        consent_status=consent,
        ready_for_pipeline=True,
    )


def anchor_from_ptas(ptas: PTAS, stability: float = 0.87) -> Anchor:
    return Anchor(
        anchor_id=f"anchor_{ptas.id}",
        ptas_id=ptas.id,
        timestamp=datetime.utcnow().isoformat() + "Z",
        somatic_context={
            "valence": "focused+grounded",
            "intensity": round(stability * 0.9, 2),
            "notes": "evolved via kickga TAS fitness",
        },
        stability_score=stability,
    )


# --- Serialization helpers ---

def to_json(obj: Any) -> str:
    if hasattr(obj, "to_dict"):
        return json.dumps(obj.to_dict(), indent=2, default=str)
    return json.dumps(obj, indent=2, default=str)


# Public surface for the module
__all__ = [
    "Role", "ConsentStatus", "EthicalAlignment", "CoherenceStatus",
    "TAS", "PTAS", "Anchor",
    "TasExtractedPayload", "ConsentGrantedPayload", "ConsentDeniedPayload",
    "AnchorCreatedPayload", "PipelineReadyPayload",
    "ResonanceHighPayload", "ResonanceLowPayload",
    "SignalTransmittedPayload", "ArtifactCreatedPayload",
    "CoherenceHighPayload", "CoherenceLowPayload",
    "ResequenceToAnchorPayload", "ResequenceToPipelinePayload", "ResequenceToDecisionPayload",
    "NoResequenceNeededPayload", "CycleSealedPayload",
    "PlaybookEvent", "PlaybookEventType", "PlaybookEventPayload",
    "create_playbook_event",
    "tas_from_genome_vector", "ptas_from_tas", "anchor_from_ptas",
    "to_json",
]
