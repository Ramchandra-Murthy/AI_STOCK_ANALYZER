from __future__ import annotations

import logging

from services.knowledge_graph.models import GraphEdge, GraphNode

logger = logging.getLogger(__name__)


class InstitutionalKnowledgeGraph:
    """In-memory institutional knowledge graph managing entities, relationships, and traversal."""

    def __init__(self) -> None:
        self.nodes: dict[str, GraphNode] = {}
        self.edges: list[GraphEdge] = []

    def add_node(self, node: GraphNode) -> None:
        logger.info("Adding node %s (%s) to IKG", node.node_id, node.node_type)
        self.nodes[node.node_id] = node

    def add_edge(self, edge: GraphEdge) -> None:
        logger.info("Adding edge %s -> %s [%s] to IKG", edge.source, edge.target, edge.relationship)
        self.edges.append(edge)

    def get_neighbors(self, node_id: str, relationship: str | None = None) -> list[GraphNode]:
        logger.info(
            "Traversing neighbors for node %s with relationship filter: %s", node_id, relationship
        )
        neighbor_ids = set()
        for edge in self.edges:
            if edge.source == node_id:
                if relationship is None or edge.relationship == relationship:
                    neighbor_ids.add(edge.target)
            elif edge.target == node_id:
                if relationship is None or edge.relationship == relationship:
                    neighbor_ids.add(edge.source)
        return [self.nodes[nid] for nid in neighbor_ids if nid in self.nodes]

    def find_path(self, start_id: str, target_id: str) -> list[str]:
        """Simple breadth-first search traversal to find relationship paths between institutional entities."""
        if start_id not in self.nodes or target_id not in self.nodes:
            return []

        queue = [[start_id]]
        visited = {start_id}

        while queue:
            path = queue.pop(0)
            current = path[-1]

            if current == target_id:
                return path

            for neighbor in self.get_neighbors(current):
                if neighbor.node_id not in visited:
                    visited.add(neighbor.node_id)
                    queue.append(path + [neighbor.node_id])

        return []
