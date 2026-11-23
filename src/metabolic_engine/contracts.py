"""Strict domain contracts and abstract engine protocol for the Metabolic Pathway SDK."""

from __future__ import annotations

from enum import Enum
from typing import Protocol, runtime_checkable
from pydantic import BaseModel, ConfigDict, Field


class NodeCategory(str, Enum):
    PATHWAY_HUB = "pathway_hub"
    MARKER = "marker"


class MarkerState(str, Enum):
    OPTIMAL = "optimal"
    BOTTLENECK = "bottleneck"


class TriageLevel(str, Enum):
    HIGH_PRIORITY = "high_priority"
    MODERATE_FOCUS = "moderate_focus"
    OPTIMAL_BASELINE = "optimal_baseline"


class AnalysisRequest(BaseModel):
    """Validated input payload required by any engine implementation."""

    model_config = ConfigDict(frozen=True)

    profile_id: str = Field(..., min_length=1, max_length=64)
    max_markers: int = Field(default=50, ge=1, le=200)


class GraphNode(BaseModel):
    """Serialized node representation consumed by the interactive graph renderer."""

    id: str
    label: str
    category: NodeCategory
    state: MarkerState
    impact_weight: float = Field(default=0.0, ge=0.0)
    card_html: str = ""


class GraphEdge(BaseModel):
    """Directed biochemical relationship between two network nodes."""

    source: str
    target: str


class AnalysisResult(BaseModel):
    """Deterministic output contract returned by the core engine."""

    profile_id: str
    efficiency_score: float = Field(..., ge=0.0, le=100.0)
    triage_level: TriageLevel
    total_markers: int = Field(..., ge=0)
    bottleneck_markers: list[str] = Field(default_factory=list)
    weighted_load: float = Field(..., ge=0.0)
    nodes: list[GraphNode]
    edges: list[GraphEdge]


@runtime_checkable
class MetabolicEngineProtocol(Protocol):
    """Interface boundary separating public UI/SDK from the private core engine."""

    def list_profiles(self) -> list[str]:
        """Returns available anonymized demonstration profile identifiers."""
        ...

    def analyze(self, request: AnalysisRequest) -> AnalysisResult:
        """Executes pathway synthesis and returns a validated network payload."""
        ...