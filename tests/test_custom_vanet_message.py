"""
Test cases for VANET custom messages
"""

import pytest
from src.messages.CustomVANETMessage_m import CustomVANETMessage

@pytest.fixture
def message():
    return CustomVANETMessage()

def test_message_creation(message):
    """Test basic message creation and properties"""
    message.setMessageType(1)  # BEACON
    message.setSourceId("vehicle_1")
    message.setDestinationId("vehicle_2")
    message.setHopCount(0)
    message.setTimestamp(100.0)
    
    assert message.getMessageType() == 1
    assert message.getSourceId() == "vehicle_1"
    assert message.getDestinationId() == "vehicle_2"
    assert message.getHopCount() == 0
    assert message.getTimestamp() == 100.0

def test_message_payload():
    """Test message payload handling"""
    message = CustomVANETMessage()
    
    # Test location payload
    message.setLocation(10.5, 20.5)
    assert message.getLocationX() == 10.5
    assert message.getLocationY() == 20.5
    
    # Test vehicle data payload
    message.setSpeed(30.0)
    message.setDirection(45.0)
    assert message.getSpeed() == 30.0
    assert message.getDirection() == 45.0

def test_message_forwarding():
    """Test message forwarding functionality"""
    original = CustomVANETMessage()
    original.setSourceId("vehicle_1")
    original.setDestinationId("vehicle_3")
    original.setHopCount(0)
    
    # Simulate message forwarding
    forwarded = CustomVANETMessage()
    forwarded.setSourceId(original.getSourceId())
    forwarded.setDestinationId(original.getDestinationId())
    forwarded.setHopCount(original.getHopCount() + 1)
    
    assert forwarded.getSourceId() == "vehicle_1"
    assert forwarded.getDestinationId() == "vehicle_3"
    assert forwarded.getHopCount() == 1

def test_cluster_announcement_message():
    """Test cluster head announcement message"""
    message = CustomVANETMessage()
    message.setMessageType(2)  # CLUSTER_HEAD_ANNOUNCEMENT
    message.setSourceId("vehicle_1")
    message.setClusterId("cluster_1")
    message.setClusterRadius(100.0)
    
    assert message.getMessageType() == 2
    assert message.getSourceId() == "vehicle_1"
    assert message.getClusterId() == "cluster_1"
    assert message.getClusterRadius() == 100.0

def test_join_request_message():
    """Test cluster join request message"""
    message = CustomVANETMessage()
    message.setMessageType(3)  # JOIN_REQUEST
    message.setSourceId("vehicle_2")
    message.setDestinationId("cluster_head_1")
    message.setLocation(15.0, 25.0)
    message.setSpeed(35.0)
    
    assert message.getMessageType() == 3
    assert message.getSourceId() == "vehicle_2"
    assert message.getDestinationId() == "cluster_head_1"
    assert message.getLocationX() == 15.0
    assert message.getLocationY() == 25.0
    assert message.getSpeed() == 35.0