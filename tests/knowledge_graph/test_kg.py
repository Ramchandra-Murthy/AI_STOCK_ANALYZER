from __future__ import annotations

import pytest
from services.knowledge_graph.models import GraphNode, GraphEdge
from services.knowledge_graph.graph import InstitutionalKnowledgeGraph

def test_knowledge_graph_nodes_and_edges() -> None:
    kg = InstitutionalKnowledgeGraph()

    reliance = GraphNode(node_id="RELIANCE.NS", node_type="Company", label="Reliance Industries")
    energy = GraphNode(node_id="SECTOR-ENERGY", node_type="Sector", label="Energy Sector")
    crude = GraphNode(node_id="COMM-CRUDE", node_type="Commodity", label="Crude Oil")

    kg.add_node(reliance)
    kg.add_node(energy)
    kg.add_node(crude)

    kg.add_edge(GraphEdge(source="RELIANCE.NS", target="SECTOR-ENERGY", relationship="belongs_to", weight=1.0))
    kg.add_edge(GraphEdge(source="RELIANCE.NS", target="COMM-CRUDE", relationship="affected_by", weight=0.85))

    neighbors = kg.get_neighbors("RELIANCE.NS", relationship="belongs_to")
    assert len(neighbors) == 1
    assert neighbors[0].node_id == "SECTOR-ENERGY"

    path = kg.find_path("COMM-CRUDE", "SECTOR-ENERGY")
    # CRUDE <- affected_by -> RELIANCE.NS -> belongs_to -> SECTOR-ENERGY
    assert len(path) == 3
    assert path[0] == "COMM-CRUDE"
    assert path[1] == "RELIANCE.NS"
    assert path[2] == "SECTOR-ENERGY"
