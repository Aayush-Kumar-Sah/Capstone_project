"""
Network Manager implementation for VANET

Manages network topology and node relationships in the VANET system.
"""

import asyncio
from typing import Dict, List, Set
from .vehicle_node import VehicleNode

class NetworkManager:
    def __init__(self):
        """Initialize the network manager"""
        self.active_nodes: Dict[str, VehicleNode] = {}
        self.relay_nodes: Set[str] = set()
        self.heartbeat_interval = 5

    async def add_node(self, node: VehicleNode) -> None:
        """Add a node to the network"""
        self.active_nodes[node.node_id] = node
        await self._update_relay_nodes()

    async def remove_node(self, node_id: str) -> None:
        """Remove a node from the network"""
        if node_id in self.active_nodes:
            del self.active_nodes[node_id]
            self.relay_nodes.discard(node_id)
            await self._update_relay_nodes()

    async def _update_relay_nodes(self) -> None:
        """Update relay node selection based on network topology"""
        # Simple relay selection strategy - nodes with most connections
        self.relay_nodes.clear()
        sorted_nodes = sorted(
            self.active_nodes.values(),
            key=lambda x: len(x.connections),
            reverse=True
        )
        
        # Select top 20% as relay nodes
        relay_count = max(1, len(sorted_nodes) // 5)
        for node in sorted_nodes[:relay_count]:
            self.relay_nodes.add(node.node_id)
            node.is_relay = True

    def get_network_statistics(self) -> Dict:
        """Get current network statistics"""
        total_nodes = len(self.active_nodes)
        return {
            "total_nodes": total_nodes,
            "relay_nodes": len(self.relay_nodes),
            "network_density": len(self.relay_nodes) / total_nodes if total_nodes else 0
        }