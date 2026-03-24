"""
Crawl Visualization.
Mirrors Screaming Frog's site visualization features:
- Force-directed crawl diagram
- Directory tree visualization
- Internal link structure graph
"""
import logging
import json
from typing import Optional
from collections import defaultdict
from urllib.parse import urlparse

from seo_spider.core.models import CrawlResult, PageData

logger = logging.getLogger("seo_spider.visualization")


class CrawlVisualizer:
    """Generate visualization data for crawl results."""

    def generate_link_graph(self, result: CrawlResult) -> dict:
        """
        Generate a force-directed graph data structure.
        Output format compatible with D3.js / NetworkX.
        """
        nodes = []
        links = []
        node_ids = {}

        for i, page in enumerate(result.pages):
            node_id = page.url
            node_ids[node_id] = i

            # Determine node color based on status
            if page.status_code == 200:
                color = "#4CAF50"  # Green
            elif 300 <= page.status_code < 400:
                color = "#FF9800"  # Orange
            elif page.status_code == 404:
                color = "#F44336"  # Red
            elif page.status_code >= 500:
                color = "#9C27B0"  # Purple
            else:
                color = "#9E9E9E"  # Gray

            nodes.append({
                "id": node_id,
                "label": urlparse(page.url).path or '/',
                "status_code": page.status_code,
                "depth": page.crawl_depth,
                "inlinks": page.inlinks_count,
                "outlinks": page.outlinks_count,
                "color": color,
                "size": max(3, min(20, page.inlinks_count + 2)),
            })

        # Build links
        seen_links = set()
        for page in result.pages:
            source = page.url
            if source not in node_ids:
                continue
            for link in page.internal_links:
                target = link.target_url
                if target in node_ids:
                    link_key = f"{source}->{target}"
                    if link_key not in seen_links:
                        seen_links.add(link_key)
                        links.append({
                            "source": source,
                            "target": target,
                            "type": "follow" if link.is_follow else "nofollow",
                        })

        return {
            "nodes": nodes,
            "links": links,
            "stats": {
                "total_nodes": len(nodes),
                "total_links": len(links),
            }
        }

    def generate_directory_tree(self, result: CrawlResult) -> dict:
        """
        Generate a directory tree structure from crawled URLs.
        """
        tree = {"name": result.domain, "children": {}, "pages": []}

        for page in result.pages:
            parsed = urlparse(page.url)
            path = parsed.path.strip('/')
            segments = path.split('/') if path else []

            current = tree
            for segment in segments[:-1]:
                if segment not in current["children"]:
                    current["children"][segment] = {
                        "name": segment,
                        "children": {},
                        "pages": [],
                    }
                current = current["children"][segment]

            # Add the page to the deepest directory
            page_name = segments[-1] if segments else "index"
            current["pages"].append({
                "name": page_name,
                "url": page.url,
                "status_code": page.status_code,
                "title": page.title[:50],
            })

        return self._convert_tree(tree)

    def _convert_tree(self, node: dict) -> dict:
        """Convert the tree structure to a list-based format."""
        result = {
            "name": node["name"],
            "children": [],
            "page_count": len(node["pages"]),
        }

        for child_name, child_node in sorted(node["children"].items()):
            result["children"].append(self._convert_tree(child_node))

        for page in node["pages"]:
            result["children"].append({
                "name": page["name"],
                "url": page["url"],
                "status_code": page["status_code"],
                "is_leaf": True,
            })

        return result

    def generate_depth_report(self, result: CrawlResult) -> dict:
        """Generate a report showing URL distribution by crawl depth."""
        depth_counts = defaultdict(int)
        depth_urls = defaultdict(list)

        for page in result.pages:
            depth_counts[page.crawl_depth] += 1
            depth_urls[page.crawl_depth].append(page.url)

        return {
            "depths": {
                depth: {
                    "count": count,
                    "urls": urls[:10],  # Sample URLs
                }
                for depth, count, urls in [
                    (d, depth_counts[d], depth_urls[d])
                    for d in sorted(depth_counts.keys())
                ]
            },
            "max_depth": max(depth_counts.keys()) if depth_counts else 0,
            "avg_depth": (
                sum(d * c for d, c in depth_counts.items()) / sum(depth_counts.values())
                if depth_counts else 0
            ),
        }

    def export_html_visualization(self, result: CrawlResult, output_path: str):
        """Export an interactive HTML visualization using D3.js."""
        graph_data = self.generate_link_graph(result)

        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>SEO Spider - Site Visualization</title>
    <meta charset="utf-8">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/d3/7.8.5/d3.min.js"></script>
    <style>
        body {{ margin: 0; font-family: Arial, sans-serif; background: #1a1a2e; color: #eee; }}
        svg {{ width: 100vw; height: 100vh; }}
        .node circle {{ stroke: #fff; stroke-width: 1.5px; cursor: pointer; }}
        .link {{ stroke: #555; stroke-opacity: 0.6; }}
        .node text {{ font-size: 10px; fill: #ccc; pointer-events: none; }}
        #info {{ position: fixed; top: 10px; right: 10px; background: #16213e; padding: 15px; border-radius: 8px; max-width: 300px; }}
        h3 {{ margin-top: 0; color: #e94560; }}
    </style>
</head>
<body>
    <div id="info">
        <h3>Site Visualization</h3>
        <p>Domain: {result.domain}</p>
        <p>Pages: {graph_data['stats']['total_nodes']}</p>
        <p>Links: {graph_data['stats']['total_links']}</p>
        <p id="selected"></p>
    </div>
    <svg></svg>
    <script>
        const data = {json.dumps(graph_data)};

        const svg = d3.select("svg");
        const width = window.innerWidth;
        const height = window.innerHeight;

        const simulation = d3.forceSimulation(data.nodes)
            .force("link", d3.forceLink(data.links).id(d => d.id).distance(50))
            .force("charge", d3.forceManyBody().strength(-100))
            .force("center", d3.forceCenter(width / 2, height / 2))
            .force("collision", d3.forceCollide().radius(d => d.size + 2));

        const link = svg.append("g")
            .selectAll("line")
            .data(data.links)
            .join("line")
            .attr("class", "link")
            .attr("stroke-width", 1);

        const node = svg.append("g")
            .selectAll("g")
            .data(data.nodes)
            .join("g")
            .attr("class", "node")
            .call(d3.drag()
                .on("start", dragstarted)
                .on("drag", dragged)
                .on("end", dragended));

        node.append("circle")
            .attr("r", d => d.size)
            .attr("fill", d => d.color)
            .on("click", (e, d) => {{
                document.getElementById("selected").innerHTML =
                    `<b>${{d.label}}</b><br>Status: ${{d.status_code}}<br>Depth: ${{d.depth}}<br>Inlinks: ${{d.inlinks}}`;
            }});

        node.append("text")
            .attr("dx", 12)
            .attr("dy", 4)
            .text(d => d.label.length > 20 ? d.label.substr(0, 20) + '...' : d.label);

        simulation.on("tick", () => {{
            link.attr("x1", d => d.source.x).attr("y1", d => d.source.y)
                .attr("x2", d => d.target.x).attr("y2", d => d.target.y);
            node.attr("transform", d => `translate(${{d.x}},${{d.y}})`);
        }});

        function dragstarted(event) {{ if (!event.active) simulation.alphaTarget(0.3).restart(); event.subject.fx = event.subject.x; event.subject.fy = event.subject.y; }}
        function dragged(event) {{ event.subject.fx = event.x; event.subject.fy = event.y; }}
        function dragended(event) {{ if (!event.active) simulation.alphaTarget(0); event.subject.fx = null; event.subject.fy = null; }}
    </script>
</body>
</html>"""

        with open(output_path, 'w') as f:
            f.write(html)
        logger.info(f"Visualization exported to {output_path}")
