"""Boundary validation, immutability, and protocol compliance tests for domain contracts."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from metabolic_engine import (
    AnalysisRequest,
    AnalysisResult,
    GraphEdge,
    GraphNode,
    MarkerState,
    MetabolicEngineProtocol,
    NodeCategory,
    SandboxPathwayEngine,
    TriageLevel,
)


def test_analysis_request_is_immutable() -> None:
    req = AnalysisRequest(profile_id="Demo Profile A", max_markers=25)
    with pytest.raises(ValidationError):
        req.profile_id = "Modified Profile"  # type: ignore[misc]


@pytest.mark.parametrize(
    ("profile_id", "max_markers"),
    [
        ("", 10),           # Empty profile_id
        ("a" * 65, 10),     # Exceeds max_length=64
        ("valid_id", 0),    # Below ge=1
        ("valid_id", 201),  # Exceeds le=200
    ],
)
def test_analysis_request_rejects_invalid_boundaries(profile_id: str, max_markers: int) -> None:
    with pytest.raises(ValidationError):
        AnalysisRequest(profile_id=profile_id, max_markers=max_markers)


@pytest.mark.parametrize("invalid_score", [-0.1, 100.5])
def test_analysis_result_enforces_percentage_bounds(invalid_score: float) -> None:
    with pytest.raises(ValidationError):
        AnalysisResult(
            profile_id="Demo Profile",
            efficiency_score=invalid_score,
            triage_level=TriageLevel.OPTIMAL_BASELINE,
            total_markers=10,
            weighted_load=0.0,
            nodes=[],
            edges=[],
        )


def test_graph_node_rejects_negative_impact_weight() -> None:
    with pytest.raises(ValidationError):
        GraphNode(
            id="NODE_1",
            label="Node 1",
            category=NodeCategory.MARKER,
            state=MarkerState.BOTTLENECK,
            impact_weight=-1.0,
        )


def test_sandbox_engine_satisfies_runtime_protocol() -> None:
    engine = SandboxPathwayEngine()
    assert isinstance(engine, MetabolicEngineProtocol)

    result = engine.analyze(AnalysisRequest(profile_id="Demo Profile A (Moderate Focus)"))
    payload = result.model_dump()
    reconstructed = AnalysisResult.model_validate(payload)

    assert reconstructed == result
    assert all(isinstance(edge, GraphEdge) for edge in reconstructed.edges)