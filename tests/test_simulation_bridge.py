"""
Test cases for VANET simulation bridge
"""

import pytest
import os
import traci
from src.simulation_bridge import VANETSimulation

@pytest.fixture
def simulation():
    # Set up environment variables
    os.environ["SUMO_HOME"] = "/home/vboxuser/sumo"
    return VANETSimulation()

def test_simulation_initialization(simulation):
    """Test simulation initialization with configs"""
    assert simulation.sumo_config == "config.sumo.cfg"
    assert simulation.omnet_config == "omnetpp.ini"
    assert simulation.veins_manager is None

def test_simulation_environment(simulation):
    """Test environment variable setup"""
    assert "SUMO_HOME" in os.environ
    assert os.path.exists(os.environ["SUMO_HOME"])
    sumo_tools = os.path.join(os.environ["SUMO_HOME"], "tools")
    assert sumo_tools in sys.path

@pytest.mark.skip(reason="Requires full SUMO installation")
def test_sumo_connection(simulation):
    """Test SUMO connection and basic commands"""
    try:
        # Start SUMO
        sumo_cmd = ["sumo", "-c", simulation.sumo_config]
        traci.start(sumo_cmd)
        
        # Verify connection
        assert traci.isLoaded()
        
        # Test basic SUMO commands
        assert isinstance(traci.simulation.getTime(), float)
        
    finally:
        if traci.isLoaded():
            traci.close()

@pytest.mark.skip(reason="Requires OMNeT++ installation")
def test_omnet_initialization(simulation):
    """Test OMNeT++ initialization"""
    try:
        simulation.initialize_simulation()
        assert simulation.veins_manager is not None
    finally:
        simulation.cleanup()

def test_vehicle_state_updates(simulation):
    """Test vehicle state update mechanism"""
    # Create mock vehicle data
    vehicle_data = {
        "test_vehicle": {
            "position": (100.0, 100.0),
            "speed": 30.0,
            "angle": 45.0
        }
    }
    
    # Test update logic
    node = simulation.find_node_by_id("test_vehicle")
    if node:
        data = vehicle_data["test_vehicle"]
        simulation.update_node_position(
            node,
            data["position"][0],
            data["position"][1],
            data["speed"],
            data["angle"]
        )