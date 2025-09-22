"""
Test cases for clustering implementation
"""

import pytest
import numpy as np
from src.clustering import ClusterManager, ClusterMetrics
from src.vehicle_node import VehicleNode

@pytest.fixture
def cluster_manager():
    return ClusterManager(max_cluster_radius=300.0)

@pytest.fixture
def test_nodes():
    nodes = []
    # Create a test cluster of vehicles
    for i in range(5):
        node = VehicleNode(
            node_id=f"vehicle_{i}",
            location=(100.0 * i, 100.0 * i),
            speed=30.0,
            direction=45.0,
            connections=[f"peer_{j}" for j in range(i)]
        )
        nodes.append(node)
    return nodes

def test_cluster_manager_initialization(cluster_manager):
    """Test cluster manager initialization"""
    assert cluster_manager.max_cluster_radius == 300.0
    assert len(cluster_manager.clusters) == 0
    assert len(cluster_manager.cluster_heads) == 0
    assert len(cluster_manager.relay_nodes) == 0
    assert len(cluster_manager.boundary_nodes) == 0
    assert len(cluster_manager.node_metrics) == 0

def test_relative_mobility_calculation(cluster_manager):
    """Test relative mobility calculation between vehicles"""
    node1 = VehicleNode(
        node_id="v1",
        location=(0.0, 0.0),
        speed=30.0,
        direction=0.0
    )
    node2 = VehicleNode(
        node_id="v2",
        location=(100.0, 100.0),
        speed=40.0,
        direction=45.0
    )
    
    mobility = cluster_manager.calculate_relative_mobility(node1, node2)
    assert 0 <= mobility <= 1  # Normalized value
    
    # Same position, speed, direction should give minimum mobility
    node3 = VehicleNode(
        node_id="v3",
        location=(0.0, 0.0),
        speed=30.0,
        direction=0.0
    )
    min_mobility = cluster_manager.calculate_relative_mobility(node1, node3)
    assert min_mobility == 0.0

def test_node_weight_calculation(cluster_manager):
    """Test node weight calculation for cluster head election"""
    metrics = ClusterMetrics(
        relative_speed=0.2,
        direction_similarity=0.9,
        connectivity_degree=5,
        signal_strength=80.0,
        battery_level=0.9,
        stability_time=150.0
    )
    
    node = VehicleNode(
        node_id="test_node",
        location=(0.0, 0.0),
        speed=30.0,
        direction=45.0,
        connections=["peer1", "peer2", "peer3", "peer4", "peer5"]
    )
    
    weight = cluster_manager.calculate_node_weight(node, metrics)
    assert 0 <= weight <= 1  # Should be normalized

def test_cluster_formation(cluster_manager, test_nodes):
    """Test cluster formation with multiple nodes"""
    clusters = cluster_manager.form_clusters(test_nodes)
    
    # Check basic cluster properties
    assert len(clusters) > 0  # At least one cluster should be formed
    
    # All nodes should be assigned to a cluster
    all_members = set()
    for members in clusters.values():
        all_members.update(members)
    assert len(all_members) == len(test_nodes)
    
    # Each cluster should have exactly one cluster head
    for head_id, members in clusters.items():
        assert head_id in members  # Cluster head should be in its own cluster