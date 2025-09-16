"""
Core implementation of the P2P VANET node.
This module handles the basic functionality of a vehicle node in the network.
"""

from typing import List, Dict, Optional
import asyncio
from libp2p import new_host
from libp2p.peer.peerinfo import info_from_p2p_addr
from pydantic import BaseModel

class VehicleNode(BaseModel):
    """
    Represents a vehicle node in the P2P VANET network.
    """
    node_id: str
    location: tuple  # (latitude, longitude)
    speed: float
    direction: float  # in degrees
    is_relay: bool = False
    connections: List[str] = []  # List of peer IDs
    trust_score: float = 1.0

    async def start(self):
        """Initialize the P2P node and start listening for connections."""
        self.host = await new_host()
        await self.host.get_network().listen()
        print(f"Node {self.node_id} listening on: {self.host.get_addrs()}")

    async def connect_to_peer(self, peer_addr: str):
        """Connect to another peer in the network."""
        peer_info = info_from_p2p_addr(peer_addr)
        await self.host.connect(peer_info)
        self.connections.append(str(peer_info.peer_id))

    def update_location(self, lat: float, lon: float):
        """Update the vehicle's current location."""
        self.location = (lat, lon)

    def update_status(self, speed: float, direction: float):
        """Update the vehicle's current status."""
        self.speed = speed
        self.direction = direction

    def calculate_relay_score(self) -> float:
        """
        Calculate the node's suitability as a relay based on:
        - Number of connections
        - Trust score
        - Stability (speed variance)
        """
        connection_score = len(self.connections) / 10  # Normalize by expected max connections
        return (connection_score + self.trust_score) / 2