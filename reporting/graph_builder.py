import os
import json
from datetime import datetime

class GraphBuilder:
    def __init__(self, target, session_id: str):
        self.target = target
        self.session_id = session_id

    def build(self, output_dir: str) -> str:
        os.makedirs(output_dir, exist_ok=True)

        name = getattr(
            self.target, "domain",
            getattr(self.target, "name", "target")
        ).replace(" ", "_")

        path = os.path.join(
            output_dir,
            f"kronos_graph_{name}_{self.session_id}.html"
        )

        nodes, edges = self._build_graph()
        html = self._render_html(nodes, edges, name)

        with open(path, "w", encoding="utf-8") as f:
            f.write(html)

        return path

    def _build_graph(self):
        nodes = []
        edges = []
        node_ids = set()

        target_name = getattr(
            self.target, "domain",
            getattr(self.target, "name", "TARGET")
        )
        nodes.append({
            "id": "target",
            "label": target_name,
            "color": "#00bcd4",
            "size": 30,
            "shape": "star"
        })
        node_ids.add("target")

        # Emails
        for email in getattr(self.target, "emails_found", []):
            nid = f"email_{email}"
            if nid not in node_ids:
                nodes.append({"id": nid, "label": email, "color": "#4caf50", "size": 15})
                node_ids.add(nid)
            edges.append({"from": "target", "to": nid, "label": "email"})

        # Profils sociaux
        for platform, url in getattr(self.target, "social_profiles", {}).items():
            nid = f"social_{platform}"
            if nid not in node_ids:
                nodes.append({"id": nid, "label": platform, "color": "#9c27b0", "size": 15})
                node_ids.add(nid)
            edges.append({"from": "target", "to": nid, "label": "social"})

        # Sous-domaines
        for sub in getattr(self.target, "subdomains", [])[:20]:
            nid = f"sub_{sub}"
            if nid not in node_ids:
                nodes.append({"id": nid, "label": sub, "color": "#ff9800", "size": 12})
                node_ids.add(nid)
            edges.append({"from": "target", "to": nid, "label": "subdomain"})

        # Connexions
        for conn in getattr(self.target, "connections", [])[:15]:
            username = conn.get("username", "")
            if not username:
                continue
            nid = f"conn_{username}"
            if nid not in node_ids:
                nodes.append({"id": nid, "label": username, "color": "#f44336", "size": 12})
                node_ids.add(nid)
            edges.append({
                "from": "target", "to": nid,
                "label": conn.get("type", "connection")
            })

        return nodes, edges

    def _render_html(self, nodes, edges, title):
        nodes_json = json.dumps(nodes)
        edges_json = json.dumps(edges)

        return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>KRONOS — {title}</title>
<script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
<style>
  body {{ background: #0a0a0a; margin: 0; font-family: monospace; color: #00bcd4; }}
  #header {{ padding: 16px 24px; background: #111; border-bottom: 1px solid #00bcd4; }}
  #header h1 {{ margin: 0; font-size: 18px; letter-spacing: 4px; }}
  #network {{ height: calc(100vh - 60px); }}
</style>
</head>
<body>
<div id="header">
  <h1>◆ KRONOS — OSINT GRAPH — {title.upper()}</h1>
</div>
<div id="network"></div>
<script>
const nodes = new vis.DataSet({nodes_json});
const edges = new vis.DataSet({edges_json});
const container = document.getElementById('network');
const options = {{
  background: {{ color: '#0a0a0a' }},
  nodes: {{
    font: {{ color: '#e0e0e0', size: 12, face: 'monospace' }},
    borderWidth: 2,
    borderWidthSelected: 3
  }},
  edges: {{
    color: {{ color: '#004d5a', highlight: '#00bcd4' }},
    font: {{ color: '#666', size: 10, face: 'monospace' }},
    smooth: {{ type: 'curvedCW', roundness: 0.2 }}
  }},
  physics: {{
    stabilization: {{ iterations: 200 }},
    barnesHut: {{ gravitationalConstant: -8000, springLength: 120 }}
  }},
  interaction: {{ hover: true, tooltipDelay: 100 }}
}};
new vis.Network(container, {{ nodes, edges }}, options);
</script>
</body>
</html>"""
