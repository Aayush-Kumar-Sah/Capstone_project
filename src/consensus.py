"""
Implementation of the Proof of Authority (PoA) consensus mechanism for relay node selection.
"""

from typing import List, Dict
import networkx as nx
from .vehicle_node import VehicleNode

class ConsensusManager:
    """
    Manages the consensus mechanism for relay node selection in the VANET network.
    """
    def __init__(self):
        self.authority_nodes: Dict[str, float] = {}  # node_id -> authority score
        self.network_graph = nx.Graph()
        
    def update_network_graph(self, nodes: List[VehicleNode]):
        """Update the network graph based on current node connections."""
        self.network_graph.clear()
        for node in nodes:
            self.network_graph.add_node(node.node_id)
            for peer_id in node.connections:
                self.network_graph.add_edge(node.node_id, peer_id)

    def calculate_node_centrality(self) -> Dict[str, float]:
        """Calculate degree centrality for all nodes in the network."""
        return nx.degree_centrality(self.network_graph)

    def select_relay_nodes(self, nodes: List[VehicleNode], relay_ratio: float = 0.2) -> List[str]:
        """
        Select relay nodes based on:
        1. Node's authority score
        2. Degree centrality in the network
        3. Node's trust score
        """
        self.update_network_graph(nodes)
        centrality_scores = self.calculate_node_centrality()
        
        # Calculate composite scores
        node_scores = {}
        for node in nodes:
            authority_score = self.authority_nodes.get(node.node_id, 0.5)
            centrality_score = centrality_scores.get(node.node_id, 0)
            trust_score = node.trust_score
            
            composite_score = (
                0.4 * authority_score +
                0.4 * centrality_score +
                0.2 * trust_score
            )
            node_scores[node.node_id] = composite_score
        
        # Select top nodes as relays
        num_relays = max(1, int(len(nodes) * relay_ratio))
        sorted_nodes = sorted(
            node_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return [node_id for node_id, _ in sorted_nodes[:num_relays]]

    def update_authority_score(self, node_id: str, performance_metric: float):
        """Update the authority score of a node based on its performance."""
        current_score = self.authority_nodes.get(node_id, 0.5)
        # Exponential moving average with α = 0.1
        new_score = 0.1 * performance_metric + 0.9 * current_score
        self.authority_nodes[node_id] = max(0, min(1, new_score))  # Clamp between 0 and 1