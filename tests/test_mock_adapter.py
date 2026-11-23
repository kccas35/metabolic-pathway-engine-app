"""Tests for the public sandbox engine adapter and factory resolution."""

from __future__ import annotations

import sys
import types
import pytest

from metabolic_engine import (
    AnalysisRequest,
    SandboxPathwayEngine,
    TriageLevel,
    resolve_engine,
)


def test_sandbox_engine_generates_valid_graphs_for_all_demo_profiles() -> None:
    engine = SandboxPathwayEngine()
    profiles = engine.list_profiles()

    assert len(profiles) >= 2

    for profile_id in profiles:
        result = engine.analyze(AnalysisRequest(profile_id=profile_id))
        node_ids = {node.id for node in result.nodes}

        assert result.profile_id == profile_id
        assert 0.0 <= result.efficiency_score <= 100.0
        assert len(result.nodes) > 0
        # Every edge must connect two existing nodes
        assert all(e.source in node_ids and e.target in node_ids for e in result.edges)


def test_sandbox_engine_respects_max_markers_without_orphaned_edges() -> None:
    engine = SandboxPathwayEngine()
    result = engine.analyze(
        AnalysisRequest(profile_id="Demo Profile A (Moderate Focus)", max_markers=2)
    )

    assert len(result.nodes) == 2
    node_ids = {node.id for node in result.nodes}
    assert all(e.source in node_ids and e.target in node_ids for e in result.edges)


def test_sandbox_engine_falls_back_gracefully_on_unknown_profile() -> None:
    engine = SandboxPathwayEngine()
    result = engine.analyze(AnalysisRequest(profile_id="NonExistentProfile"))

    assert result.triage_level == TriageLevel.MODERATE_FOCUS
    assert len(result.nodes) > 0


def test_resolve_engine_defaults_to_sandbox(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("USE_PRIVATE_CORE", raising=False)
    engine = resolve_engine()
    assert isinstance(engine, SandboxPathwayEngine)


def test_resolve_engine_loads_private_core_when_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_module = types.ModuleType("metabolic_private_core")

    class FakePrivateEngine(SandboxPathwayEngine):
        pass

    fake_module.ProductionMetabolicEngine = FakePrivateEngine  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "metabolic_private_core", fake_module)
    monkeypatch.setenv("USE_PRIVATE_CORE", "true")

    engine = resolve_engine()
    assert isinstance(engine, FakePrivateEngine)