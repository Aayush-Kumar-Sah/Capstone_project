"""
Clustering and node election mechanisms for VANET P2P network.
Implements clustering based on relative mobility and weighted metrics for node election.
"""

import numpy as np
from typing import List, Dict, Set, Tuple
from dataclasses import dataclass
import networkx as nx
from .vehicle_node import VehicleNode

@dataclass
class ClusterMetrics:
    relative_speed: float
    direction_similarity: float
    connectivity_degree: int
    signal_strength: float
    battery_level: float  # For electric vehicles or device power
    stability_time: float  # How long the node has been in the network

class ClusterManager:
    def __init__(self, max_cluster_radius: float = 300.0):  # 300 meters default cluster radius
        self.max_cluster_radius = max_cluster_radius
        self.clusters: Dict[str, Set[str]] = {}  # cluster_head_id -> set of member_ids
        self.cluster_heads: Set[str] = set()
        self.relay_nodes: Set[str] = set()
        self.boundary_nodes: Set[str] = set()
        self.node_metrics: Dict[str, ClusterMetrics] = {}

    def calculate_relative_mobility(self, node1: VehicleNode, node2: VehicleNode) -> float:
        """
        Calculate relative mobility between two vehicles based on:
        - Speed difference
        - Direction difference
        - Position difference
        """
        speed_diff = abs(node1.speed - node2.speed)
        
        # Calculate direction difference (0-180 degrees)
        dir_diff = abs(node1.direction - node2.direction)
        if dir_diff > 180:
            dir_diff = 360 - dir_diff
            
        # Calculate position difference
        pos_diff = np.sqrt(
            (node1.location[0] - node2.location[0])**2 +
            (node1.location[1] - node2.location[1])**2
        )
        
        # Normalize and combine metrics
        norm_speed_diff = speed_diff / 30.0  # Assuming max speed diff of 30 m/s
        norm_dir_diff = dir_diff / 180.0
        norm_pos_diff = min(pos_diff / self.max_cluster_radius, 1.0)
        
        return (0.4 * norm_speed_diff + 0.3 * norm_dir_diff + 0.3 * norm_pos_diff)

    def calculate_node_weight(self, node: VehicleNode, metrics: ClusterMetrics) -> float:
        """
        Calculate node weight for cluster head election based on multiple factors:
        - Connectivity degree (number of neighbors)
        - Relative mobility (stability)
        - Signal strength
        - Battery level
        - Historical stability
        """
        weights = {
            'connectivity': 0.25,
            'mobility': 0.25,
            'signal': 0.2,
            'battery': 0.15,
            'stability': 0.15
        }
        
        # Normalize metrics
        norm_connectivity = min(metrics.connectivity_degree / 10, 1.0)  # Assume max 10 connections
        norm_signal = metrics.signal_strength / 100.0  # Assume signal strength 0-100
        
        return (
            weights['connectivity'] * norm_connectivity +
            weights['mobility'] * (1 - metrics.relative_speed) +  # Lower relative speed is better
            weights['signal'] * norm_signal +
            weights['battery'] * metrics.battery_level +
            weights['stability'] * min(metrics.stability_time / 300, 1.0)  # 5 minutes max
        )

    def form_clusters(self, nodes: List[VehicleNode]) -> Dict[str, Set[str]]:
        """
        Form clusters using a weighted clustering algorithm.
        Returns a dictionary mapping cluster heads to their member nodes.
        """
        # Reset current clustering
        self.clusters.clear()
        self.cluster_heads.clear()
        
        # Calculate metrics for all nodes
        for node in nodes:
            metrics = ClusterMetrics(
                relative_speed=0.0,  # Will be updated
                direction_similarity=0.0,  # Will be updated
                connectivity_degree=len(node.connections),
                signal_strength=1.0,  # Should be obtained from actual measurements
                battery_level=1.0,  # Should be obtained from vehicle
                stability_time=0.0  # Should be tracked over time
            )
            
            # Calculate average relative mobility with neighbors
            rel_speeds = []
            for neighbor_id in node.connections:
                neighbor = next((n for n in nodes if n.node_id == neighbor_id), None)
                if neighbor:
                    rel_speeds.append(self.calculate_relative_mobility(node, neighbor))
            
            metrics.relative_speed = np.mean(rel_speeds) if rel_speeds else 1.0
            self.node_metrics[node.node_id] = metrics

        # Calculate node weights and sort by weight
        node_weights = {
            node.node_id: self.calculate_node_weight(node, self.node_metrics[node.node_id])
            for node in nodes
        }
        
        sorted_nodes = sorted(
            nodes,
            key=lambda x: node_weights[x.node_id],
            reverse=True
        )

        # Form clusters
        unclustered_nodes = set(node.node_id for node in nodes)
        
        for node in sorted_nodes:
            if node.node_id not in unclustered_nodes:
                continue
                
            # This node becomes a cluster head
            self.cluster_heads.add(node.node_id)
            self.clusters[node.node_id] = {node.node_id}
            unclustered_nodes.remove(node.node_id)
            
            # Add neighboring nodes to cluster
            for neighbor_id in node.connections:
                if neighbor_id in unclustered_nodes:
                    neighbor = next((n for n in nodes if n.node_id == neighbor_id), None)
                    if neighbor and self.calculate_relative_mobility(node, neighbor) < 0.7:
                        self.clusters[node.node_id].add(neighbor_id)
                        unclustered_nodes.remove(neighbor_id)

        return self.clusters

    def select_relay_nodes(self, nodes: List[VehicleNode]) -> Set[str]:
        """
        Select relay nodes for inter-cluster communication.
        Relay nodes are typically boundary nodes with good connectivity to multiple clusters.
        """
        self.relay_nodes.clear()
        self.boundary_nodes.clear()
        
        # Identify boundary nodes (nodes with neighbors in different clusters)
        for node in nodes:
            node_cluster = None
            for head_id, members in self.clusters.items():
                if node.node_id in members:
                    node_cluster = head_id
                    break
                    
            if node_cluster is None:
                continue
                
            # Check if node has neighbors in different clusters
            has_external_neighbor = False
            for neighbor_id in node.connections:
                neighbor_cluster = None
                for head_id, members in self.clusters.items():
                    if neighbor_id in members:
                        neighbor_cluster = head_id
                        break
                        
                if neighbor_cluster and neighbor_cluster != node_cluster:
                    has_external_neighbor = True
                    break
                    
            if has_external_neighbor:
                self.boundary_nodes.add(node.node_id)

        # Select relay nodes from boundary nodes based on connectivity and stability
        for node_id in self.boundary_nodes:
            node = next((n for n in nodes if n.node_id == node_id), None)
            if not node:
                continue
                
            metrics = self.node_metrics[node_id]
            if (metrics.connectivity_degree >= 3 and  # At least 3 connections
                metrics.relative_speed < 0.5 and     # Relatively stable
                metrics.signal_strength > 0.7):      # Good signal strength
                self.relay_nodes.add(node_id)

        return self.relay_nodes

    def update_cluster_status(self, nodes: List[VehicleNode]):
        """
        Periodically update cluster structure based on node mobility and network changes.
        """
        # Update metrics
        for node in nodes:
            if node.node_id in self.node_metrics:
                metrics = self.node_metrics[node.node_id]
                metrics.stability_time += 1  # Increment stability time
                
        # Check if re-clustering is needed
        need_reclustering = False
        
        # Check cluster head stability
        for head_id in list(self.cluster_heads):
            head = next((n for n in nodes if n.node_id == head_id), None)
            if not head:
                need_reclustering = True
                break
                
            head_metrics = self.node_metrics[head_id]
            if head_metrics.relative_speed > 0.8:  # Head became too unstable
                need_reclustering = True
                break

        if need_reclustering:
            self.form_clusters(nodes)
            self.select_relay_nodes(nodes)