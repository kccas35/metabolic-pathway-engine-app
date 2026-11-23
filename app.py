"""Streamlit presentation layer decoupled via MetabolicEngineProtocol."""

from __future__ import annotations

import streamlit as st
import streamlit.components.v1 as components

from metabolic_engine import (
    AnalysisRequest,
    PyVisGraphRenderer,
    TriageLevel,
    resolve_engine,
)


@st.cache_resource
def get_engine():
    return resolve_engine()


@st.cache_data(show_spinner=False)
def run_cached_pipeline(profile_id: str) -> tuple[dict, str]:
    engine = get_engine()
    renderer = PyVisGraphRenderer(height="650px")

    result = engine.analyze(AnalysisRequest(profile_id=profile_id))
    html_canvas = renderer.render_html(result)
    return result.model_dump(), html_canvas


def main() -> None:
    st.set_page_config(page_title="Metabolic Performance App", page_icon="🧬", layout="wide")
    st.title("🧬 Metabolic Performance App")
    st.caption("Interactive pathway mapping & actionable daily nutrition insights.")

    engine = get_engine()
    profiles = engine.list_profiles()

    selected_profile = st.selectbox("Choose a Demonstration Profile:", profiles)

    if st.button("Analyze My Metabolism"):
        with st.spinner("Synthesizing metabolic network..."):
            result_data, html_canvas = run_cached_pipeline(selected_profile)

            col1, col2 = st.columns([1, 2])
            with col1:
                st.metric(
                    label="Metabolic Efficiency Score",
                    value=f"{result_data['efficiency_score']:.2f}%",
                )
                st.write(
                    f"**Summary:** {len(result_data['bottleneck_markers'])} priority markers "
                    f"across {result_data['total_markers']} mapped pathway nodes."
                )
                st.write(f"**Weighted Load:** -{result_data['weighted_load']:.1f} impact points.")

            with col2:
                triage = result_data["triage_level"]
                if triage == TriageLevel.HIGH_PRIORITY:
                    st.error(
                        "🚨 HIGH PRIORITY: Key metabolic bottlenecks detected. Click any red node "
                        "below to inspect targeted nutrition and lifestyle guidance."
                    )
                elif triage == TriageLevel.MODERATE_FOCUS:
                    st.warning(
                        "⚠️ MODERATE FOCUS: Select metabolic routes can benefit from targeted daily "
                        "nutrition adjustments. Click any red node below for details."
                    )
                else:
                    st.success(
                        "✅ GREAT BASELINE: Mapped metabolic pathways are operating smoothly."
                    )

            st.markdown("### Interactive Metabolic Map")
            markers = result_data["bottleneck_markers"]
            markers_str = ", ".join([f"`{m}`" for m in markers]) if markers else "None"
            st.markdown(
                f"🔵 **Metabolic Pathway Hub** &nbsp;|&nbsp; "
                f"🔴 **Focus Marker (Click for action plan):** {markers_str} &nbsp;|&nbsp; "
                f"🟢 **Optimal Node**"
            )
            components.html(html_canvas, height=660, scrolling=False)


if __name__ == "__main__":
    main()