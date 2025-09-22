"""
Test cases for consensus implementation
"""

import pytest
import networkx as nx
from src.consensus import ConsensusManager
from src.vehicle_node import VehicleNode

@pytest.fixture
def consensus_manager():
    return ConsensusManager()

@pytest.fixture
def test_nodes():
    nodes = []
    # Create a test network of nodes
    for i in range(5):
        node = VehicleNode(
            node_id=f"node_{i}",
            location=(100.0 * i, 100.0 * i),
            speed=30.0,
            direction=45.0,
            connections=[f"node_{j}" for j in range(i)]  # Create connections
        )
        nodes.append(node)
    return nodes

def test_consensus_manager_initialization(consensus_manager):
    """Test consensus manager initialization"""
    assert isinstance(consensus_manager.network_graph, nx.Graph)
    assert len(consensus_manager.authority_nodes) == 0

def test_network_graph_update(consensus_manager, test_nodes):
    """Test network graph update with node connections"""
    consensus_manager.update_network_graph(test_nodes)
    
    # Verify graph properties
    assert consensus_manager.network_graph.number_of_nodes() == len(test_nodes)
    
    # Check connections
    for node in test_nodes:
        assert node.node_id in consensus_manager.network_graph
        for peer_id in node.connections:
            assert consensus_manager.network_graph.has_edge(node.node_id, peer_id)

def test_node_centrality_calculation(consensus_manager, test_nodes):
    """Test centrality calculation for nodes"""
    consensus_manager.update_network_graph(test_nodes)
    centrality_scores = consensus_manager.calculate_node_centrality()
    
    # Verify centrality properties
    assert len(centrality_scores) == len(test_nodes)
    for score in centrality_scores.values():
        assert 0 <= score <= 1  # Centrality should be normalized

def test_relay_node_selection(consensus_manager, test_nodes):
    """Test relay node selection process"""
    # Set up some initial authority scores
    for node in test_nodes:
        consensus_manager.authority_nodes[node.node_id] = 0.5
    
    relay_nodes = consensus_manager.select_relay_nodes(test_nodes, relay_ratio=0.4)
    
    # Verify relay node selection properties
    assert len(relay_nodes) == max(1, int(len(test_nodes) * 0.4))
    assert all(node_id in [n.node_id for n in test_nodes] for node_id in relay_nodes)

def test_authority_score_update(consensus_manager):
    """Test authority score updates"""
    node_id = "test_node"
    
    # Initial update
    consensus_manager.update_authority_score(node_id, 0.8)
    assert node_id in consensus_manager.authority_nodes
    assert 0 <= consensus_manager.authority_nodes[node_id] <= 1
    
    # Multiple updates should maintain score bounds
    for _ in range(5):
        consensus_manager.update_authority_score(node_id, 0.9)
    assert 0 <= consensus_manager.authority_nodes[node_id] <= 1