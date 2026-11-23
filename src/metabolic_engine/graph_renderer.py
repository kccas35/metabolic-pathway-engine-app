"""Zero-rerun interactive dark-mode graph renderer powered by NetworkX, PyVis, and JS injection."""

from __future__ import annotations

import networkx as nx
from pyvis.network import Network

from .contracts import AnalysisResult, MarkerState, NodeCategory


class PyVisGraphRenderer:
    """Converts a validated AnalysisResult into a self-contained interactive HTML canvas."""

    def __init__(self, height: str = "650px") -> None:
        self.height = height

    def to_networkx(self, result: AnalysisResult) -> nx.DiGraph:
        """Builds a styled directed graph from validated engine nodes and edges."""
        graph = nx.DiGraph()

        for node in result.nodes:
            if node.category == NodeCategory.PATHWAY_HUB:
                graph.add_node(
                    node.id,
                    label=node.label,
                    color="#38bdf8",
                    size=32,
                    font={"size": 15, "color": "#f8fafc", "face": "sans-serif", "bold": True},
                    info_html=node.card_html,
                )
            elif node.state == MarkerState.BOTTLENECK:
                graph.add_node(
                    node.id,
                    label=node.label,
                    color="#ff4b4b",
                    size=26,
                    borderWidth=3,
                    font={"size": 15, "color": "#ffffff", "face": "sans-serif", "bold": True},
                    info_html=node.card_html,
                )
            else:
                graph.add_node(
                    node.id,
                    label=node.label,
                    color="rgba(46, 160, 67, 0.55)",
                    size=7,
                    font={"size": 0},
                    info_html=node.card_html,
                )

        for edge in result.edges:
            if edge.source in graph and edge.target in graph:
                graph.add_edge(edge.source, edge.target)

        return graph

    def render_html(self, result: AnalysisResult) -> str:
        """Generates self-contained HTML with injected client-side DOM click handlers."""
        graph = self.to_networkx(result)

        net = Network(
            height=self.height,
            width="100%",
            directed=True,
            bgcolor="#0e1117",
            font_color="#e2e8f0",
            cdn_resources="in_line",
        )
        net.from_nx(graph)

        net.set_options("""
        {
          "interaction": {
            "hover": true,
            "zoomView": true,
            "dragView": true,
            "navigationButtons": false
          },
          "edges": {
            "color": { "color": "rgba(148, 163, 184, 0.22)", "highlight": "#38bdf8" },
            "smooth": { "type": "continuous" },
            "arrows": { "to": { "enabled": true, "scaleFactor": 0.45 } }
          },
          "physics": {
            "barnesHut": {
              "gravitationalConstant": -3200,
              "centralGravity": 0.45,
              "springLength": 75,
              "springConstant": 0.05,
              "damping": 0.15,
              "avoidOverlap": 0.35
            },
            "stabilization": {
              "enabled": true,
              "iterations": 250
            }
          }
        }
        """)

        html_string = net.generate_html()
        html_string = html_string.replace(
            "<body>",
            "<body style='margin: 0; padding: 0; background-color: #0e1117; overflow: hidden;'>",
        )
        html_string = html_string.replace(
            "border: 1px solid lightgray;",
            "border: 1px solid #1e293b; border-radius: 8px;",
        )

        custom_overlay = """
        <button onclick="network.fit({animation: {duration: 400}})" style="position: absolute; top: 16px; left: 16px; padding: 7px 12px; background: rgba(15, 23, 42, 0.92); border: 1px solid #334155; color: #e2e8f0; border-radius: 6px; cursor: pointer; font-family: sans-serif; font-size: 12px; font-weight: 600; z-index: 9998;">
            🎯 Center Map
        </button>

        <div id="info-panel" style="position: absolute; top: 16px; right: 16px; width: 350px; background: rgba(15, 23, 42, 0.97); border: 1px solid #38bdf8; padding: 18px; border-radius: 10px; box-shadow: 0 10px 28px rgba(0,0,0,0.65); display: none; font-family: sans-serif; z-index: 9999; color: #f8fafc;">
            <div id="info-content"></div>
            <button onclick="document.getElementById('info-panel').style.display='none'" style="margin-top: 12px; width: 100%; padding: 8px; border: 1px solid #334155; background: #1e293b; color: #f8fafc; border-radius: 6px; cursor: pointer; font-weight: bold;">Close</button>
        </div>

        <script type="text/javascript">
            network.once("stabilizationIterationsDone", function() {
                network.fit({ animation: false });
            });

            network.on("click", function (params) {
                if (params.nodes.length > 0) {
                    var nodeId = params.nodes[0];
                    var node = nodes.get(nodeId);
                    if (node.info_html) {
                        document.getElementById("info-content").innerHTML = node.info_html;
                        document.getElementById("info-panel").style.display = "block";
                    }
                } else {
                    document.getElementById("info-panel").style.display = "none";
                }
            });
        </script>
        </body>
        """

        return html_string.replace("</body>", custom_overlay)