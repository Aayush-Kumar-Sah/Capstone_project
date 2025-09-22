"""
Test cases for vehicle node implementation
"""

import pytest
from src.vehicle_node import VehicleNode

def test_vehicle_node_creation():
    """Test basic vehicle node creation and attributes"""
    node = VehicleNode(
        node_id="test_vehicle_1",
        location=(0.0, 0.0),
        speed=0.0,
        direction=0.0
    )
    assert node.node_id == "test_vehicle_1"
    assert node.location == (0.0, 0.0)
    assert node.speed == 0.0
    assert node.direction == 0.0
    assert not node.is_relay
    assert node.connections == []
    assert node.trust_score == 1.0

def test_vehicle_node_update():
    """Test vehicle node state updates"""
    node = VehicleNode(
        node_id="test_vehicle_1", 
        location=(0.0, 0.0),
        speed=0.0, 
        direction=0.0
    )
    
    # Update location
    node.update_location(1.0, 2.0)
    assert node.location == (1.0, 2.0)
    
    # Update status
    node.update_status(30.0, 45.0)
    assert node.speed == 30.0
    assert node.direction == 45.0

def test_relay_score_calculation():
    """Test relay score calculation"""
    node = VehicleNode(
        node_id="test_vehicle_1",
        location=(0.0, 0.0),
        speed=0.0,
        direction=0.0,
        connections=["peer1", "peer2"]
    )
    
    score = node.calculate_relay_score()
    expected_score = (0.2 + 1.0) / 2  # (2 connections/10 + trust_score) / 2
    assert score == expected_score