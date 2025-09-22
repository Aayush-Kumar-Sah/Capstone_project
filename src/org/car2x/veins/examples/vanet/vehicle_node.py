"""
Vehicle Node implementation for VANET

Represents a single vehicle in the VANET network.
"""

from typing import List, Tuple

class VehicleNode:
    def __init__(self, node_id: str, location: Tuple[float, float], 
                 speed: float, direction: float, connections: List[str] = None):
        """Initialize a vehicle node"""
        self.node_id = node_id
        self.location = location
        self.speed = speed
        self.direction = direction
        self.is_relay = False
        self.connections = connections or []
        self.trust_score = 1.0  # Initial trust score

    def update_location(self, x: float, y: float) -> None:
        """Update vehicle location"""
        self.location = (x, y)

    def update_status(self, speed: float, direction: float) -> None:
        """Update vehicle status"""
        self.speed = speed
        self.direction = direction

    def calculate_relay_score(self) -> float:
        """Calculate score for relay selection"""
        # Simple scoring based on number of connections and trust score
        connection_weight = min(len(self.connections) / 10, 1.0)  # Cap at 1.0
        return (connection_weight + self.trust_score) / 2  # Average of both factors