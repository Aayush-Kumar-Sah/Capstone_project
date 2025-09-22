"""
Test cases for custom VANET application
"""

import pytest
from src.custom_vanet_appl import CustomVANETApplication, MessageType
import traci

@pytest.fixture
def app():
    return CustomVANETApplication()

def test_application_initialization(app):
    """Test application initialization"""
    assert app.beacon_interval == 1.0
    assert app.cluster_update_interval == 5.0
    assert app.last_beacon_time == 0
    assert app.last_cluster_update == 0
    assert len(app.vehicle_nodes) == 0

def test_message_type_enum():
    """Test message type enumeration"""
    assert MessageType.BEACON.value == 1
    assert MessageType.CLUSTER_HEAD_ANNOUNCEMENT.value == 2
    assert MessageType.JOIN_REQUEST.value == 3
    assert MessageType.JOIN_RESPONSE.value == 4
    assert MessageType.RELAY_ANNOUNCEMENT.value == 5
    assert MessageType.BOUNDARY_UPDATE.value == 6

@pytest.mark.skip(reason="Requires SUMO connection")
def test_vehicle_state_updates(app):
    """Test vehicle state updates from SUMO"""
    try:
        # Initialize SUMO
        app.initialize()
        
        # Add test vehicles to SUMO
        traci.vehicle.add("test_vehicle_1", "route_0")
        traci.vehicle.add("test_vehicle_2", "route_0")
        
        # Update vehicle states
        app._update_vehicle_states()
        
        # Verify vehicle nodes were created
        assert "test_vehicle_1" in app.vehicle_nodes
        assert "test_vehicle_2" in app.vehicle_nodes
        
    finally:
        if traci.isLoaded():
            traci.close()

def test_beacon_timing(app):
    """Test beacon sending timing"""
    # Initialize with some vehicles
    app.vehicle_nodes = {
        "test_vehicle_1": {
            "location": (0, 0),
            "speed": 30,
            "direction": 45
        }
    }
    
    # Verify beacon timing
    current_step = 0
    app.last_beacon_time = current_step
    app.handle_timeStep(current_step + 0.5)  # Too early for beacon
    
    # Should send beacon
    app.handle_timeStep(current_step + 1.0)
    assert app.last_beacon_time > current_step

def test_cluster_update_timing(app):
    """Test cluster update timing"""
    current_step = 0
    app.last_cluster_update = current_step
    
    # Too early for update
    app.handle_timeStep(current_step + 2.0)
    assert app.last_cluster_update == current_step
    
    # Should trigger update
    app.handle_timeStep(current_step + 5.0)
    assert app.last_cluster_update > current_step

def test_message_queue_management(app):
    """Test message queue handling"""
    # Add test message
    message_id = "test_msg_1"
    app.message_queue[message_id] = {
        "timestamp": 100,
        "source": "vehicle_1",
        "destination": "vehicle_2"
    }
    
    assert message_id in app.message_queue
    assert app.message_queue[message_id]["source"] == "vehicle_1"
    assert app.message_queue[message_id]["destination"] == "vehicle_2"