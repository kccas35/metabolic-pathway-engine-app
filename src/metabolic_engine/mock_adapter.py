"""Deterministic sandbox adapter for public demonstration, local development, and CI."""

from __future__ import annotations

import os
from .contracts import (
    AnalysisRequest,
    AnalysisResult,
    GraphEdge,
    GraphNode,
    MarkerState,
    MetabolicEngineProtocol,
    NodeCategory,
    TriageLevel,
)


class SandboxPathwayEngine:
    """Synthetic implementation of MetabolicEngineProtocol with zero proprietary IP exposure."""

    _PROFILES = {
        "Demo Profile A (Moderate Focus)": {
            "score": 96.4,
            "triage": TriageLevel.MODERATE_FOCUS,
            "total_markers": 28,
            "weighted_load": 1.0,
            "bottleneck": ("ENZYME_M1", "Cofactor Synthesis Unit M1"),
        },
        "Demo Profile B (High Priority)": {
            "score": 92.8,
            "triage": TriageLevel.HIGH_PRIORITY,
            "total_markers": 32,
            "weighted_load": 2.3,
            "bottleneck": ("ENZYME_R4", "Redox & Methylation Node R4"),
        },
    }

    def list_profiles(self) -> list[str]:
        return list(self._PROFILES.keys())

    def analyze(self, request: AnalysisRequest) -> AnalysisResult:
        profile = self._PROFILES.get(
            request.profile_id,
            self._PROFILES["Demo Profile A (Moderate Focus)"],
        )
        bottleneck_id, bottleneck_label = profile["bottleneck"]

        hub_card = (
            "<h4 style='color: #38bdf8; margin: 0 0 6px 0;'>🌐 Core Energy & Methylation Cascade</h4>"
            "<span style='font-size: 12px; color: #94a3b8;'>Synthetic Demo Module</span>"
            "<div style='margin-top: 12px; padding: 10px; background: rgba(56, 189, 248, 0.12); "
            "border-left: 3px solid #38bdf8; border-radius: 6px; font-size: 13px; line-height: 1.45; color: #f1f5f9;'>"
            "<b style='color: #38bdf8;'>✨ Pathway Support Overview:</b><br>"
            "Prioritize micronutrient-dense whole foods, natural folates, and steady aerobic movement."
            "</div>"
        )

        bottleneck_card = (
            f"<h4 style='color: #ff4b4b; margin: 0 0 6px 0;'>🧬 Marker Spotlight: {bottleneck_id}</h4>"
            f"<div style='font-size: 13px; color: #e2e8f0; margin-bottom: 4px;'>"
            f"<b>Linked Domain:</b> {bottleneck_label}<br>"
            f"<b>Cascade:</b> Core Energy & Methylation"
            f"</div>"
            f"<div style='margin: 10px 0; padding: 10px; background: rgba(34, 197, 94, 0.12); "
            f"border-left: 3px solid #4ade80; border-radius: 6px; font-size: 13px; line-height: 1.45; color: #f8fafc;'>"
            f"<b style='color: #4ade80;'>💡 Daily Action Plan (Demo):</b><br>"
            f"Pair dark leafy greens, legumes, and omega-3 rich foods with consistent sleep and hydration."
            f"</div>"
            f"<details style='margin-top: 8px; font-size: 12px; color: #94a3b8; cursor: pointer;'>"
            f"<summary style='font-weight: bold; color: #cbd5e1;'>🔬 View Synthetic Telemetry</summary>"
            f"<div style='margin-top: 6px; padding-top: 6px; border-top: 1px solid #334155; line-height: 1.5;'>"
            f"<b>Mode:</b> Public Sandbox Adapter<br>"
            f"<b>Normalized Impact Weight:</b> {profile['weighted_load']:.2f}"
            f"</div>"
            f"</details>"
        )

        optimal_card = (
            "<h4 style='color: #4ade80; margin: 0 0 6px 0;'>✅ ENZYME_OPT_01 — Operating Smoothly</h4>"
            "<span style='font-size: 13px; color: #e2e8f0;'>"
            "No bottleneck flags detected on this synthetic node.</span>"
        )

        nodes = [
            GraphNode(
                id="HUB_CORE_01",
                label="Core Energy Cascade",
                category=NodeCategory.PATHWAY_HUB,
                state=MarkerState.OPTIMAL,
                card_html=hub_card,
            ),
            GraphNode(
                id=bottleneck_id,
                label=bottleneck_id,
                category=NodeCategory.MARKER,
                state=MarkerState.BOTTLENECK,
                impact_weight=profile["weighted_load"],
                card_html=bottleneck_card,
            ),
            GraphNode(
                id="ENZYME_OPT_01",
                label="ENZYME_OPT_01",
                category=NodeCategory.MARKER,
                state=MarkerState.OPTIMAL,
                card_html=optimal_card,
            ),
            GraphNode(
                id="ENZYME_OPT_02",
                label="ENZYME_OPT_02",
                category=NodeCategory.MARKER,
                state=MarkerState.OPTIMAL,
                card_html=optimal_card,
            ),
        ][: request.max_markers]

        valid_ids = {n.id for n in nodes}
        raw_edges = [
            GraphEdge(source=bottleneck_id, target="ENZYME_OPT_01"),
            GraphEdge(source="ENZYME_OPT_01", target="HUB_CORE_01"),
            GraphEdge(source="ENZYME_OPT_02", target="HUB_CORE_01"),
            GraphEdge(source=bottleneck_id, target="HUB_CORE_01"),
        ]
        edges = [e for e in raw_edges if e.source in valid_ids and e.target in valid_ids]

        return AnalysisResult(
            profile_id=request.profile_id,
            efficiency_score=profile["score"],
            triage_level=profile["triage"],
            total_markers=profile["total_markers"],
            bottleneck_markers=[bottleneck_id],
            weighted_load=profile["weighted_load"],
            nodes=nodes,
            edges=edges,
        )


def resolve_engine() -> MetabolicEngineProtocol:
    """Loads the private production engine if installed, otherwise returns the public sandbox."""
    if os.getenv("USE_PRIVATE_CORE", "false").lower() == "true":
        from metabolic_private_core import ProductionMetabolicEngine  # type: ignore[import-not-found]

        return ProductionMetabolicEngine()
    return SandboxPathwayEngine()