"""Tests for NetworkX graph styling, dangling-edge safety, and zero-rerun HTML/JS rendering."""

from __future__ import annotations

from metabolic_engine import (
    AnalysisResult,
    GraphEdge,
    GraphNode,
    MarkerState,
    NodeCategory,
    PyVisGraphRenderer,
    TriageLevel,
)


def _sample_result() -> AnalysisResult:
    return AnalysisResult(
        profile_id="Test Profile",
        efficiency_score=95.5,
        triage_level=TriageLevel.MODERATE_FOCUS,
        total_markers=3,
        bottleneck_markers=["M_BOTTLENECK"],
        weighted_load=1.2,
        nodes=[
            GraphNode(
                id="HUB_1",
                label="Energy Hub",
                category=NodeCategory.PATHWAY_HUB,
                state=MarkerState.OPTIMAL,
                card_html="<h4>Hub Card</h4>",
            ),
            GraphNode(
                id="M_BOTTLENECK",
                label="Bottleneck Marker",
                category=NodeCategory.MARKER,
                state=MarkerState.BOTTLENECK,
                impact_weight=1.2,
                card_html="<h4>Action Plan Card</h4>",
            ),
            GraphNode(
                id="M_OPTIMAL",
                label="Optimal Marker",
                category=NodeCategory.MARKER,
                state=MarkerState.OPTIMAL,
                card_html="<h4>Optimal Card</h4>",
            ),
        ],
        edges=[
            GraphEdge(source="M_BOTTLENECK", target="HUB_1"),
            GraphEdge(source="M_OPTIMAL", target="HUB_1"),
            # Dangling edge referencing a non-existent node; must be ignored safely
            GraphEdge(source="GHOST_NODE", target="HUB_1"),
        ],
    )


def test_to_networkx_applies_visual_styles_and_prunes_dangling_edges() -> None:
    renderer = PyVisGraphRenderer()
    graph = renderer.to_networkx(_sample_result())

    assert set(graph.nodes) == {"HUB_1", "M_BOTTLENECK", "M_OPTIMAL"}
    assert graph.nodes["HUB_1"]["color"] == "#38bdf8"
    assert graph.nodes["M_BOTTLENECK"]["color"] == "#ff4b4b"
    assert graph.nodes["M_OPTIMAL"]["font"]["size"] == 0

    assert ("M_BOTTLENECK", "HUB_1") in graph.edges
    assert ("GHOST_NODE", "HUB_1") not in graph.edges


def test_render_html_injects_zero_rerun_client_side_overlay() -> None:
    renderer = PyVisGraphRenderer(height="500px")
    html = renderer.render_html(_sample_result())

    assert "id=\"info-panel\"" in html
    assert "Center Map" in html
    assert 'network.on("click"' in html
    assert "Action Plan Card" in html