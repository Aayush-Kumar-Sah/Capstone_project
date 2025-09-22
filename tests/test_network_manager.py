"""
Test cases for network manager implementation
"""

import pytest
from src.network_manager import NetworkManager
from src.vehicle_node import VehicleNode

@pytest.fixture
def network_manager():
    return NetworkManager()

@pytest.fixture
def test_nodes():
    nodes = []
    for i in range(5):
        node = VehicleNode(
            node_id=f"node_{i}",
            location=(100.0 * i, 100.0 * i),
            speed=30.0,
            direction=45.0,
            connections=[f"node_{j}" for j in range(i)]
        )
        nodes.append(node)
    return nodes

@pytest.mark.asyncio
async def test_network_manager_initialization(network_manager):
    """Test network manager initialization"""
    assert len(network_manager.active_nodes) == 0
    assert len(network_manager.relay_nodes) == 0
    assert network_manager.heartbeat_interval == 5

@pytest.mark.asyncio
async def test_node_addition(network_manager):
    """Test adding nodes to the network"""
    node = VehicleNode(
        node_id="test_node",
        location=(0.0, 0.0),
        speed=30.0,
        direction=45.0
    )
    
    await network_manager.add_node(node)
    assert "test_node" in network_manager.active_nodes
    assert network_manager.active_nodes["test_node"] == node

@pytest.mark.asyncio
async def test_node_removal(network_manager):
    """Test removing nodes from the network"""
    # Add a node first
    node = VehicleNode(
        node_id="test_node",
        location=(0.0, 0.0),
        speed=30.0,
        direction=45.0
    )
    await network_manager.add_node(node)
    
    # Remove the node
    await network_manager.remove_node("test_node")
    assert "test_node" not in network_manager.active_nodes
    assert "test_node" not in network_manager.relay_nodes

@pytest.mark.asyncio
async def test_relay_node_updates(network_manager, test_nodes):
    """Test relay node selection and updates"""
    # Add all test nodes
    for node in test_nodes:
        await network_manager.add_node(node)
    
    # Verify that relay nodes are selected
    assert len(network_manager.relay_nodes) > 0
    
    # Verify relay node properties
    for relay_id in network_manager.relay_nodes:
        assert relay_id in network_manager.active_nodes
        assert network_manager.active_nodes[relay_id].is_relay

@pytest.mark.asyncio
async def test_network_statistics(network_manager, test_nodes):
    """Test network statistics calculation"""
    # Add nodes
    for node in test_nodes:
        await network_manager.add_node(node)
    
    stats = network_manager.get_network_statistics()
    assert stats["total_nodes"] == len(test_nodes)
    assert "relay_nodes" in stats
    assert "network_density" in stats