"""
Test configuration for the VANET Capstone project
"""

import os
import sys
import pytest

# Add project root to Python path 
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Configure asyncio test mode
@pytest.fixture(autouse=True)
def event_loop_policy():
    if sys.platform.startswith('win'):
        import asyncio
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Common fixtures that may be needed across multiple test files
@pytest.fixture
def sumo_home():
    """Ensure SUMO_HOME is set for tests"""
    return "/home/vboxuser/sumo"

@pytest.fixture 
def test_config():
    """Test configuration values"""
    return {
        "max_cluster_radius": 300.0,
        "beacon_interval": 1.0,
        "heartbeat_interval": 5.0,
        "consensus_relay_ratio": 0.2,
        "simulation_duration": 1000
    }

def pytest_sessionstart(session):
    """Set up any test environment requirements"""
    os.environ["SUMO_HOME"] = "/home/vboxuser/sumo"