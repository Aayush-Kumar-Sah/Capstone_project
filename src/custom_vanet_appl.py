"""
Custom VANET Application with Clustering Integration

This module implements the main VANET application that coordinates clustering
algorithms, message processing, and vehicle communication management.
"""

import time
import logging
import math
from typing import Dict, List, Optional, Set, Any, Tuple
from dataclasses import dataclass
from enum import Enum

# Import our clustering modules
from .clustering import Vehicle, Cluster, VehicleClustering, ClusteringAlgorithm
from .cluster_manager import ClusterManager, ClusterState, ClusterMetrics, ClusterHeadElectionMethod
from .trust_aware_cluster_manager import TrustAwareClusterManager
from .message_processor import (
    MessageProcessor, VANETMessage, MessageType, 
    JoinResponseCode, MergeResponseCode
)
from .consensus_engine import (
    ConsensusEngine, TrustMetrics, TrustLevel, MaliciousActivity,
    ConsensusMessage, ConsensusMessageType
)

class MessageType(Enum):
    """Message types for backward compatibility with tests"""
    BEACON = 1
    CLUSTER_HEAD_ANNOUNCEMENT = 2
    JOIN_REQUEST = 3
    JOIN_RESPONSE = 4
    RELAY_ANNOUNCEMENT = 5
    BOUNDARY_UPDATE = 6

@dataclass
class VehicleNode:
    """Represents a vehicle node in the network"""
    vehicle_id: str
    location: Tuple[float, float]
    speed: float
    direction: float
    lane_id: str = ""
    acceleration: float = 0.0
    vehicle_type: str = "passenger"
    last_update: float = 0.0
    
    # Communication properties
    transmission_range: float = 300.0
    neighbors: Set[str] = None
    message_buffer: List[VANETMessage] = None
    
    # Clustering properties
    cluster_id: str = ""
    
    # Trust and Security properties
    trust_score: float = 1.0
    trust_level: TrustLevel = TrustLevel.UNKNOWN
    is_malicious: bool = False
    message_authenticity_score: float = 1.0
    behavior_consistency_score: float = 1.0
    location_verification_score: float = 1.0
    last_trust_update: float = 0.0
    malicious_activity_count: int = 0
    is_cluster_head: bool = False
    cluster_join_attempts: int = 0
    last_cluster_update: float = 0.0
    
    def __post_init__(self):
        if self.neighbors is None:
            self.neighbors = set()
        if self.message_buffer is None:
            self.message_buffer = []
        if self.last_update == 0.0:
            self.last_update = time.time()
    
    def to_vehicle(self) -> Vehicle:
        """Convert to Vehicle object for clustering algorithms"""
        return Vehicle(
            id=self.vehicle_id,
            x=self.location[0],
            y=self.location[1],
            speed=self.speed,
            direction=self.direction,
            lane_id=self.lane_id,
            timestamp=self.last_update
        )

class CustomVANETApplication:
    """Main VANET application with clustering support"""
    
    def __init__(self, clustering_algorithm: ClusteringAlgorithm = ClusteringAlgorithm.MOBILITY_BASED):
        # Basic application properties
        self.beacon_interval = 1.0  # seconds
        self.cluster_update_interval = 5.0  # seconds
        self.last_beacon_time = 0.0
        self.last_cluster_update = 0.0
        
        # Vehicle management
        self.vehicle_nodes: Dict[str, VehicleNode] = {}
        self.message_queue: Dict[str, Dict] = {}
        
        # Clustering components
        self.clustering_engine = VehicleClustering(clustering_algorithm)
        
        # Wire trust evaluation into clustering engine
        self.clustering_engine.set_trust_provider(self._get_vehicle_trust_score)
        self.clustering_engine.set_malicious_checker(self._is_vehicle_malicious)
        self.clustering_engine.min_trust_for_clustering = 0.3  # Allow low trust vehicles to participate
        
        # Use trust-aware cluster manager for enhanced security
        self.cluster_manager = TrustAwareClusterManager(self.clustering_engine)
        self.cluster_manager.head_election_method = ClusterHeadElectionMethod.WEIGHTED_COMPOSITE
        self.cluster_manager.min_trust_threshold = 0.6  # Minimum trust for cluster heads
        self.cluster_manager.trust_weight = 0.4  # Weight of trust in head selection
        self.cluster_manager.exclude_malicious = True  # Exclude malicious nodes
        
        # Wire trust evaluation callbacks into cluster manager
        self.cluster_manager.set_trust_provider(self._get_vehicle_trust_score)
        self.cluster_manager.set_malicious_checker(self._is_vehicle_malicious)
        
        self.message_processor = MessageProcessor()
        
        # Consensus and Security components
        self.consensus_engine: Optional[ConsensusEngine] = None
        self.trust_enabled = True
        self.consensus_type = "hybrid"  # "raft", "poa", or "hybrid"
        self.authority_nodes: Set[str] = set()
        self.trust_update_interval = 10.0  # seconds
        self.last_trust_update = 0.0
        
        # Security thresholds
        self.trusted_threshold = 0.7
        self.malicious_threshold = 0.3
        self.trust_decay_rate = 0.05  # Trust decay per hour without interaction
        
        # Application state
        self.current_time = 0.0
        self.simulation_step = 0
        self.is_initialized = False
        
        # Performance metrics
        self.statistics = {
            'messages_sent': 0,
            'messages_received': 0,
            'clusters_formed': 0,
            'cluster_joins': 0,
            'cluster_leaves': 0,
            'head_elections': 0,
            'trust_evaluations': 0,
            'malicious_nodes_detected': 0,
            'consensus_messages': 0,
            'trust_updates': 0
        }
        
        # Configuration
        self.config = {
            'enable_clustering': True,
            'enable_emergency_handling': True,
            'max_message_buffer_size': 100,
            'neighbor_timeout': 10.0,
            'cluster_announcement_interval': 3.0,
            'heartbeat_interval': 2.0
        }
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("CustomVANETApplication initialized")
    
    def initialize(self):
        """Initialize the VANET application"""
        self.current_time = 0.0  # Use simulation time, not Unix time
        self.last_beacon_time = 0.0
        self.last_cluster_update = 0.0
        self.is_initialized = True
        self.logger.info("VANET application initialized")
    
    def initialize_consensus(self, node_id: str, consensus_type: str = "hybrid", 
                           authority_nodes: List[str] = None):
        """Initialize consensus engine for trust evaluation"""
        self.consensus_type = consensus_type
        self.consensus_engine = ConsensusEngine(node_id, consensus_type)
        
        if authority_nodes:
            self.authority_nodes = set(authority_nodes)
            
        # Initialize consensus algorithms based on type
        if consensus_type in ["raft", "hybrid"]:
            # Initialize Raft with all known nodes (will be updated as nodes join)
            cluster_nodes = list(self.vehicle_nodes.keys()) if self.vehicle_nodes else [node_id]
            self.consensus_engine.initialize_raft(cluster_nodes)
            
        if consensus_type in ["poa", "hybrid"]:
            # Initialize PoA with authority nodes
            authorities = list(self.authority_nodes) if self.authority_nodes else [node_id]
            self.consensus_engine.initialize_poa(authorities)
        
        self.consensus_engine.start()
        self.logger.info(f"Consensus engine initialized: {consensus_type} with {len(self.authority_nodes)} authorities")
    
    def add_authority_node(self, node_id: str):
        """Add a node as a trusted authority"""
        self.authority_nodes.add(node_id)
        if self.consensus_engine and self.consensus_engine.poa:
            self.consensus_engine.poa.authorities.add(node_id)
            self.consensus_engine.poa.authority_scores[node_id] = 0.8  # Initial high score
        self.logger.info(f"Added authority node: {node_id}")
    
    def remove_authority_node(self, node_id: str):
        """Remove authority status from a node"""
        self.authority_nodes.discard(node_id)
        if self.consensus_engine and self.consensus_engine.poa:
            self.consensus_engine.poa.authorities.discard(node_id)
            self.consensus_engine.poa.authority_scores.pop(node_id, None)
        self.logger.info(f"Removed authority node: {node_id}")
    
    def handle_timeStep(self, simulation_time: float):
        """Handle simulation time step"""
        self.current_time = simulation_time
        self.simulation_step += 1
        
        if not self.is_initialized:
            self.initialize()
        
        # Update vehicle states (would integrate with SUMO/TraCI)
        self._update_vehicle_states()
        
        # Process message queue
        self._process_message_queue()
        
        # Handle periodic operations
        if self._should_send_beacons():
            self._send_beacons()
            self.last_beacon_time = self.current_time
        
        if self._should_update_clusters():
            self._update_clustering()
            self.last_cluster_update = self.current_time
        
        # Update trust evaluations
        if self.trust_enabled and self._should_update_trust():
            self.update_trust_scores()
            self.apply_trust_decay()
        
        # Clean up old data
        self._cleanup_old_data()
    
    def add_vehicle(self, vehicle_id: str, x: float, y: float, speed: float, 
                   direction: float, lane_id: str = ""):
        """Add a new vehicle to the network"""
        node = VehicleNode(
            vehicle_id=vehicle_id,
            location=(x, y),
            speed=speed,
            direction=direction,
            lane_id=lane_id,
            last_update=self.current_time
        )
        
        self.vehicle_nodes[vehicle_id] = node
        self.logger.debug(f"Added vehicle {vehicle_id} at ({x}, {y})")
        
        # Send immediate beacon to announce presence
        self._send_beacon(node)
    
    def update_vehicle(self, vehicle_id: str, x: float, y: float, speed: float, 
                      direction: float, lane_id: str = ""):
        """Update vehicle state"""
        if vehicle_id in self.vehicle_nodes:
            node = self.vehicle_nodes[vehicle_id]
            node.location = (x, y)
            node.speed = speed
            node.direction = direction
            node.lane_id = lane_id
            node.last_update = self.current_time
        else:
            # Vehicle not tracked yet, add it
            self.add_vehicle(vehicle_id, x, y, speed, direction, lane_id)
    
    def remove_vehicle(self, vehicle_id: str):
        """Remove vehicle from network"""
        if vehicle_id in self.vehicle_nodes:
            node = self.vehicle_nodes[vehicle_id]
            
            # If vehicle is cluster head, trigger handover
            if node.is_cluster_head and node.cluster_id:
                self._handle_cluster_head_departure(vehicle_id)
            
            # If vehicle is cluster member, send leave notification
            elif node.cluster_id:
                self._send_cluster_leave_notification(node)
            
            del self.vehicle_nodes[vehicle_id]
            self.logger.info(f"Removed vehicle {vehicle_id}")
    
    def evaluate_node_trust(self, node_id: str, behavior_data: Dict[str, Any] = None) -> float:
        """Evaluate trust score for a node"""
        if not self.trust_enabled or not self.consensus_engine:
            return 1.0
        
        if node_id not in self.vehicle_nodes:
            return 0.0
            
        node = self.vehicle_nodes[node_id]
        current_time = time.time()
        
        # Create trust metrics from available data
        trust_metrics = TrustMetrics(
            node_id=node_id,
            message_authenticity=node.message_authenticity_score,
            behavior_consistency=node.behavior_consistency_score,
            network_participation=self._calculate_network_participation(node_id),
            response_reliability=self._calculate_response_reliability(node_id),
            location_verification=node.location_verification_score,
            timestamp=current_time
        )
        
        # Evaluate trust using consensus engine
        trust_score = self.consensus_engine.evaluate_node_trust(node_id, trust_metrics)
        
        # Update node trust information
        node.trust_score = trust_score
        node.trust_level = self.consensus_engine.get_trust_level(node_id)
        node.last_trust_update = current_time
        
        # Check for malicious behavior if behavior data provided
        if behavior_data:
            malicious_activity = self.consensus_engine.trust_engine.detect_malicious_behavior(
                node_id, behavior_data
            )
            if malicious_activity:
                node.is_malicious = True
                node.malicious_activity_count += 1
                self._handle_malicious_node_detected(node_id, malicious_activity)
        
        self.statistics['trust_evaluations'] += 1
        return trust_score
    
    def report_malicious_activity(self, reporter_id: str, target_id: str, 
                                 activity_type: str, evidence: Dict[str, Any], 
                                 severity: float) -> bool:
        """Report malicious activity to the consensus network"""
        if not self.consensus_engine or reporter_id not in self.vehicle_nodes:
            return False
        
        # Create malicious activity report
        report_message = self.consensus_engine.report_malicious_activity(
            target_id, activity_type, evidence, severity
        )
        
        # Broadcast to authorities
        self._broadcast_consensus_message(report_message)
        
        self.logger.warning(f"Malicious activity reported: {target_id} by {reporter_id}")
        return True
    
    def update_trust_scores(self):
        """Update trust scores for all nodes"""
        if not self.trust_enabled or not self.consensus_engine:
            return
        
        current_time = self.current_time
        
        for node_id, node in self.vehicle_nodes.items():
            # Skip recent updates
            if current_time - node.last_trust_update < self.trust_update_interval:
                continue
            
            # Collect behavior data
            behavior_data = self._collect_behavior_data(node_id)
            
            # Evaluate trust
            self.evaluate_node_trust(node_id, behavior_data)
            
            # Apply trust decay for inactive nodes
            if current_time - node.last_update > 3600:  # 1 hour
                node.trust_score *= (1 - self.trust_decay_rate)
                node.trust_score = max(0.0, node.trust_score)
        
        self.last_trust_update = current_time
        self.statistics['trust_updates'] += 1
    
    def is_node_trusted(self, node_id: str) -> bool:
        """Check if a node is trusted"""
        if not self.trust_enabled or node_id not in self.vehicle_nodes:
            return True  # Default to trusted if no trust system
        
        node = self.vehicle_nodes[node_id]
        return node.trust_score >= self.trusted_threshold and not node.is_malicious
    
    def is_node_malicious(self, node_id: str) -> bool:
        """Check if a node is considered malicious"""
        if not self.trust_enabled or node_id not in self.vehicle_nodes:
            return False
        
        node = self.vehicle_nodes[node_id]
        return node.is_malicious or node.trust_score <= self.malicious_threshold
    
    def _get_vehicle_trust_score(self, vehicle_id: str) -> float:
        """Internal callback for cluster manager to get trust scores"""
        if vehicle_id not in self.vehicle_nodes:
            return 0.5  # Default neutral trust for unknown vehicles
        return self.vehicle_nodes[vehicle_id].trust_score
    
    def _is_vehicle_malicious(self, vehicle_id: str) -> bool:
        """Internal callback for cluster manager to check malicious status"""
        return self.is_node_malicious(vehicle_id)
    
    def update_trust_on_message_delivery(self, sender_id: str, success: bool):
        """Update trust score based on message delivery success"""
        if not self.trust_enabled or sender_id not in self.vehicle_nodes:
            return
        
        node = self.vehicle_nodes[sender_id]
        
        if success:
            # Reward successful message delivery
            node.message_authenticity_score = min(1.0, node.message_authenticity_score + 0.01)
            node.behavior_consistency_score = min(1.0, node.behavior_consistency_score + 0.005)
            node.trust_score = min(1.0, node.trust_score + 0.002)
        else:
            # Penalize failed delivery (could be intentional dropping)
            node.message_authenticity_score = max(0.0, node.message_authenticity_score - 0.02)
            node.trust_score = max(0.0, node.trust_score - 0.005)
        
        self.logger.debug(f"Trust updated for {sender_id} after message delivery: {node.trust_score:.3f}")
    
    def update_trust_on_cooperation(self, vehicle_id: str, cooperation_score: float):
        """Update trust score based on cooperative behavior"""
        if not self.trust_enabled or vehicle_id not in self.vehicle_nodes:
            return
        
        node = self.vehicle_nodes[vehicle_id]
        
        # Update behavior consistency based on cooperation
        delta = (cooperation_score - 0.5) * 0.02  # Range: -0.01 to +0.01
        node.behavior_consistency_score = max(0.0, min(1.0, node.behavior_consistency_score + delta))
        node.trust_score = max(0.0, min(1.0, node.trust_score + delta * 0.5))
        
        self.logger.debug(f"Trust updated for {vehicle_id} based on cooperation: {node.trust_score:.3f}")
    
    def update_trust_on_cluster_behavior(self, vehicle_id: str, is_head: bool, stability_contribution: float):
        """Update trust based on cluster behavior"""
        if not self.trust_enabled or vehicle_id not in self.vehicle_nodes:
            return
        
        node = self.vehicle_nodes[vehicle_id]
        
        # Reward stable cluster participation
        if stability_contribution > 0.7:
            bonus = 0.003 if is_head else 0.001
            node.trust_score = min(1.0, node.trust_score + bonus)
            node.behavior_consistency_score = min(1.0, node.behavior_consistency_score + bonus)
        
        # Penalize unstable behavior
        elif stability_contribution < 0.3:
            penalty = 0.002 if is_head else 0.001
            node.trust_score = max(0.0, node.trust_score - penalty)
            node.behavior_consistency_score = max(0.0, node.behavior_consistency_score - penalty)
        
        self.logger.debug(f"Trust updated for {vehicle_id} based on cluster behavior: {node.trust_score:.3f}")
    
    def penalize_malicious_behavior(self, vehicle_id: str, severity: float):
        """Apply trust penalty for detected malicious behavior"""
        if not self.trust_enabled or vehicle_id not in self.vehicle_nodes:
            return
        
        node = self.vehicle_nodes[vehicle_id]
        
        # Significant trust penalty
        penalty = 0.1 * severity  # Up to 0.1 penalty for severe misbehavior
        node.trust_score = max(0.0, node.trust_score - penalty)
        node.message_authenticity_score = max(0.0, node.message_authenticity_score - penalty * 1.5)
        node.behavior_consistency_score = max(0.0, node.behavior_consistency_score - penalty * 1.2)
        
        # Mark as malicious if trust drops too low
        if node.trust_score < self.malicious_threshold:
            node.is_malicious = True
            node.malicious_activity_count += 1
        
        self.logger.warning(f"Trust penalized for {vehicle_id} (malicious behavior): {node.trust_score:.3f}")
    
    def apply_trust_decay(self):
        """Apply time-based trust decay for all vehicles"""
        if not self.trust_enabled:
            return
        
        current_time = self.current_time
        decay_applied = 0
        
        for vehicle_id, node in self.vehicle_nodes.items():
            # Calculate time since last update
            inactive_time = current_time - node.last_update
            
            # Apply decay for inactive nodes (more than 5 minutes)
            if inactive_time > 300:
                hours_inactive = inactive_time / 3600.0
                decay_factor = (1 - self.trust_decay_rate) ** hours_inactive
                
                node.trust_score *= decay_factor
                node.message_authenticity_score *= decay_factor
                node.behavior_consistency_score *= decay_factor
                
                decay_applied += 1
        
        if decay_applied > 0:
            self.logger.debug(f"Applied trust decay to {decay_applied} inactive vehicles")
    
    def receive_message(self, message_data: Dict[str, Any]):
        """Receive and process incoming message (external interface)"""
        try:
            # Convert dictionary to VANETMessage
            message = VANETMessage.from_dict(message_data)
            
            self.logger.debug(f"Received {message.message_type} message from {message.source_id}")
            
            # Process message
            result = self.message_processor.process_message(message, self.current_time)
            
            # Handle processing result
            self._handle_message_processing_result(message, result)
            
            # Note: messages_received counter is now incremented in _deliver_message_to_vehicle()
            # to properly count deliveries to each vehicle
            
        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
    
    def send_data(self, source_id: str, data: str, data_type: str = "general",
                 priority: int = 0, is_emergency: bool = False) -> bool:
        """Send data through the VANET"""
        if source_id not in self.vehicle_nodes:
            return False
        
        source_node = self.vehicle_nodes[source_id]
        vehicle = source_node.to_vehicle()
        
        # Create data message
        message = self.message_processor.create_data_message(
            vehicle=vehicle,
            data=data,
            data_type=data_type,
            cluster_id=source_node.cluster_id,
            is_inter_cluster=False,
            priority=priority,
            is_emergency=is_emergency
        )
        
        # Send message
        return self._send_message(message)
    
    def send_emergency(self, source_id: str, emergency_data: str) -> bool:
        """Send emergency message"""
        if source_id not in self.vehicle_nodes:
            return False
        
        source_node = self.vehicle_nodes[source_id]
        vehicle = source_node.to_vehicle()
        
        # Create emergency message
        message = self.message_processor.create_emergency_message(
            vehicle=vehicle,
            emergency_data=emergency_data,
            cluster_id=source_node.cluster_id
        )
        
        # Send with highest priority
        return self._send_message(message)
    
    def _update_vehicle_states(self):
        """Update vehicle states (placeholder for SUMO/TraCI integration)"""
        # This would integrate with SUMO via TraCI to get real vehicle positions
        # For now, we'll just update timestamps
        for node in self.vehicle_nodes.values():
            if self.current_time - node.last_update > self.config['neighbor_timeout']:
                # Vehicle hasn't been updated recently, consider for removal
                pass
    
    def _should_send_beacons(self) -> bool:
        """Check if it's time to send beacons"""
        return (self.current_time - self.last_beacon_time) >= self.beacon_interval
    
    def _should_update_clusters(self) -> bool:
        """Check if it's time to update clusters"""
        should_update = (self.current_time - self.last_cluster_update) >= self.cluster_update_interval
        self.logger.debug(f"Should update clusters? current_time={self.current_time}, last_update={self.last_cluster_update}, interval={self.cluster_update_interval}, result={should_update}")
        return should_update
    
    def _should_update_trust(self) -> bool:
        """Check if it's time to update trust scores"""
        return (self.current_time - self.last_trust_update) >= self.trust_update_interval
    
    def _send_beacons(self):
        """Send beacon messages from all vehicles"""
        for node in self.vehicle_nodes.values():
            self._send_beacon(node)
    
    def _send_beacon(self, node: VehicleNode):
        """Send beacon message from a specific vehicle"""
        vehicle = node.to_vehicle()
        cluster = None
        
        if node.cluster_id:
            cluster = self.clustering_engine.clusters.get(node.cluster_id)
        
        message = self.message_processor.create_beacon_message(vehicle, cluster)
        # Set timestamp to simulation time (not real system time)
        message.timestamp = self.current_time
        self._send_message(message)
    
    def _update_clustering(self):
        """Update clustering for all vehicles"""
        self.logger.info("=== CLUSTERING UPDATE STARTED ===")
        if not self.config['enable_clustering']:
            self.logger.debug("Clustering disabled, skipping update")
            return
        
        # Convert vehicle nodes to Vehicle objects
        vehicles = [node.to_vehicle() for node in self.vehicle_nodes.values()]
        
        if not vehicles:
            self.logger.debug("No vehicles available for clustering")
            return
        
        self.logger.debug(f"Starting clustering update with {len(vehicles)} vehicles")
        
        # Update clustering
        management_result = self.cluster_manager.update_cluster_management(
            vehicles, self.current_time
        )
        
        clusters = management_result['clusters']
        management_actions = management_result['management_actions']
        
        self.logger.debug(f"Clustering update completed: {len(clusters)} clusters, {len(management_actions)} actions")
        
        # Update vehicle node cluster assignments
        self._update_vehicle_cluster_assignments(clusters)
        
        # Update trust scores based on cluster stability (if trust enabled)
        if self.trust_enabled:
            self._update_trust_from_cluster_stability(clusters)
        
        # Process management actions
        self._process_cluster_management_actions(management_actions)
        
        # Send cluster announcements for new heads
        self._send_cluster_announcements(clusters)
        
        self.logger.debug(f"Updated clustering: {len(clusters)} clusters active")
    
    def _update_vehicle_cluster_assignments(self, clusters: Dict[str, Cluster]):
        """Update vehicle nodes with cluster assignments and track joins/leaves"""
        # Track previous cluster assignments
        previous_assignments = {}
        for vehicle_id, node in self.vehicle_nodes.items():
            previous_assignments[vehicle_id] = node.cluster_id
        
        # Reset all cluster assignments
        for node in self.vehicle_nodes.values():
            node.cluster_id = ""
            node.is_cluster_head = False
        
        # Update with current assignments and send join messages
        for cluster_id, cluster in clusters.items():
            # Update cluster head
            if cluster.head_id in self.vehicle_nodes:
                head_node = self.vehicle_nodes[cluster.head_id]
                head_node.cluster_id = cluster_id
                head_node.is_cluster_head = True
                
                # Track cluster join/change for head
                previous_cluster = previous_assignments.get(cluster.head_id, "")
                if previous_cluster != cluster_id:
                    if previous_cluster:
                        self.statistics['cluster_leaves'] += 1
                        self.logger.debug(f"Head {cluster.head_id} left cluster {previous_cluster}")
                    if cluster_id:
                        self.statistics['cluster_joins'] += 1
                        self.logger.debug(f"Head {cluster.head_id} joined cluster {cluster_id}")
            
            # Update cluster members and send join requests
            for member_id in cluster.member_ids:
                if member_id in self.vehicle_nodes:
                    member_node = self.vehicle_nodes[member_id]
                    member_node.cluster_id = cluster_id
                    member_node.is_cluster_head = False
                    
                    # Track cluster join/change for member
                    previous_cluster = previous_assignments.get(member_id, "")
                    if previous_cluster != cluster_id:
                        if previous_cluster:
                            self.statistics['cluster_leaves'] += 1
                            self.logger.debug(f"Vehicle {member_id} left cluster {previous_cluster}")
                            # Send leave notification
                            vehicle = member_node.to_vehicle()
                            leave_message = self.message_processor.create_leave_notification(
                                vehicle, previous_cluster
                            )
                            self._send_message(leave_message)
                        
                        if cluster_id:
                            self.statistics['cluster_joins'] += 1
                            self.logger.debug(f"Vehicle {member_id} joined cluster {cluster_id}")
                            # Send join request
                            vehicle = member_node.to_vehicle()
                            # Find cluster head for target
                            target_head_id = cluster.head_id if cluster.head_id else cluster_id
                            join_message = self.message_processor.create_join_request(
                                vehicle, cluster_id, target_head_id
                            )
                            self._send_message(join_message)
    
    def _update_trust_from_cluster_stability(self, clusters: Dict[str, Cluster]):
        """Update trust scores based on cluster stability contributions"""
        for cluster_id, cluster in clusters.items():
            # Get cluster metrics if available
            metrics = self.cluster_manager.cluster_metrics.get(cluster_id)
            if not metrics:
                continue
            
            stability_score = metrics.stability_score
            
            # Update trust for cluster head
            if cluster.head_id in self.vehicle_nodes:
                self.update_trust_on_cluster_behavior(
                    cluster.head_id, 
                    is_head=True, 
                    stability_contribution=stability_score
                )
            
            # Update trust for cluster members
            for member_id in cluster.member_ids:
                if member_id in self.vehicle_nodes:
                    self.update_trust_on_cluster_behavior(
                        member_id, 
                        is_head=False, 
                        stability_contribution=stability_score
                    )
    
    def _process_cluster_management_actions(self, actions: Dict[str, Any]):
        """Process cluster management actions"""
        for cluster_id, action_info in actions.items():
            action = action_info['action']
            
            if action == 'head_change':
                self._handle_head_change(cluster_id, action_info)
            elif action == 'merge_candidates':
                self._handle_merge_candidates(cluster_id, action_info)
            elif action == 'split_plan':
                self._handle_split_plan(cluster_id, action_info)
    
    def _send_cluster_announcements(self, clusters: Dict[str, Cluster]):
        """Send cluster head announcements"""
        for cluster_id, cluster in clusters.items():
            if cluster.head_id in self.vehicle_nodes:
                head_node = self.vehicle_nodes[cluster.head_id]
                
                # Check if enough time has passed since last announcement
                if (self.current_time - head_node.last_cluster_update) >= \
                   self.config['cluster_announcement_interval']:
                    
                    vehicle = head_node.to_vehicle()
                    message = self.message_processor.create_cluster_head_announcement(
                        vehicle, cluster
                    )
                    self._send_message(message)
                    head_node.last_cluster_update = self.current_time
    
    def _handle_head_change(self, cluster_id: str, action_info: Dict[str, Any]):
        """Handle cluster head change"""
        old_head = action_info['old_head']
        new_head = action_info['new_head']
        
        if old_head in self.vehicle_nodes and new_head in self.vehicle_nodes:
            old_node = self.vehicle_nodes[old_head]
            new_node = self.vehicle_nodes[new_head]
            
            # Send handover message
            old_vehicle = old_node.to_vehicle()
            cluster = self.clustering_engine.clusters.get(cluster_id)
            
            if cluster:
                message = self.message_processor.create_handover_message(
                    old_vehicle, new_head, cluster
                )
                self._send_message(message)
                
                self.statistics['head_elections'] += 1
                self.logger.info(f"Cluster {cluster_id} head changed from {old_head} to {new_head}")
    
    def _handle_merge_candidates(self, cluster_id: str, action_info: Dict[str, Any]):
        """Handle cluster merge candidates"""
        candidates = action_info['candidates']
        
        if cluster_id in self.clustering_engine.clusters:
            source_cluster = self.clustering_engine.clusters[cluster_id]
            head_node = self.vehicle_nodes.get(source_cluster.head_id)
            
            if head_node:
                for candidate_id in candidates:
                    if candidate_id in self.clustering_engine.clusters:
                        target_cluster = self.clustering_engine.clusters[candidate_id]
                        head_vehicle = head_node.to_vehicle()
                        
                        message = self.message_processor.create_merge_request(
                            head_vehicle, source_cluster, candidate_id, target_cluster.head_id
                        )
                        self._send_message(message)
    
    def _handle_split_plan(self, cluster_id: str, action_info: Dict[str, Any]):
        """Handle cluster split plan"""
        plan = action_info['plan']
        
        if cluster_id in self.clustering_engine.clusters:
            cluster = self.clustering_engine.clusters[cluster_id]
            head_node = self.vehicle_nodes.get(cluster.head_id)
            
            if head_node:
                head_vehicle = head_node.to_vehicle()
                split_groups = [plan['group1'], plan['group2']]
                
                message = self.message_processor.create_split_notification(
                    head_vehicle, cluster_id, split_groups, plan['split_reason']
                )
                self._send_message(message)
    
    def _handle_cluster_head_departure(self, departing_head_id: str):
        """Handle cluster head departure"""
        departing_node = self.vehicle_nodes.get(departing_head_id)
        if not departing_node or not departing_node.cluster_id:
            return
        
        cluster_id = departing_node.cluster_id
        cluster = self.clustering_engine.clusters.get(cluster_id)
        
        if cluster and cluster.member_ids:
            # Find suitable replacement
            members = [self.vehicle_nodes[mid] for mid in cluster.member_ids 
                      if mid in self.vehicle_nodes]
            
            if members:
                # Simple selection - choose first member
                new_head_node = members[0]
                departing_vehicle = departing_node.to_vehicle()
                
                message = self.message_processor.create_handover_message(
                    departing_vehicle, new_head_node.vehicle_id, cluster
                )
                self._send_message(message)
                
                self.logger.info(f"Cluster {cluster_id} head handover from {departing_head_id} "
                               f"to {new_head_node.vehicle_id}")
    
    def _send_cluster_leave_notification(self, node: VehicleNode):
        """Send cluster leave notification"""
        vehicle = node.to_vehicle()
        message = self.message_processor.create_leave_notification(
            vehicle, node.cluster_id
        )
        self._send_message(message)
        self.statistics['cluster_leaves'] += 1
    
    def _handle_message_processing_result(self, message: VANETMessage, result: Dict[str, Any]):
        """Handle message processing result"""
        action = result.get('action')
        
        if action == 'join_request_received':
            self._handle_join_request(message, result)
        elif action == 'join_response_received':
            self._handle_join_response(message, result)
        elif action == 'merge_request_received':
            self._handle_merge_request(message, result)
        elif action == 'merge_response_received':
            self._handle_merge_response(message, result)
        elif action == 'emergency_received':
            self._handle_emergency_message(message, result)
        elif action == 'update_neighbor':
            self._update_neighbor_info(result)
    
    def _handle_join_request(self, message: VANETMessage, result: Dict[str, Any]):
        """Handle cluster join request"""
        requesting_vehicle = result['requesting_vehicle']
        target_cluster = result['target_cluster']
        
        # Check if we are the cluster head for the target cluster
        if target_cluster in self.clustering_engine.clusters:
            cluster = self.clustering_engine.clusters[target_cluster]
            
            if cluster.head_id in self.vehicle_nodes:
                head_node = self.vehicle_nodes[cluster.head_id]
                
                # Decide whether to accept the join request
                response_code = self._evaluate_join_request(message, cluster)
                reason = ""
                
                if response_code != JoinResponseCode.JOIN_ACCEPTED:
                    if response_code == JoinResponseCode.JOIN_REJECTED_FULL:
                        reason = "Cluster is full"
                    elif response_code == JoinResponseCode.JOIN_REJECTED_INCOMPATIBLE:
                        reason = "Vehicle incompatible with cluster"
                    elif response_code == JoinResponseCode.JOIN_REJECTED_DUPLICATE:
                        reason = "Vehicle already in cluster"
                
                # Send response
                head_vehicle = head_node.to_vehicle()
                response = self.message_processor.create_join_response(
                    head_vehicle, requesting_vehicle, response_code, cluster, reason
                )
                self._send_message(response)
                
                if response_code == JoinResponseCode.JOIN_ACCEPTED:
                    self.statistics['cluster_joins'] += 1
    
    def _evaluate_join_request(self, message: VANETMessage, cluster: Cluster) -> JoinResponseCode:
        """Evaluate whether to accept a join request"""
        # Check cluster size
        if cluster.size() >= self.clustering_engine.max_cluster_size:
            return JoinResponseCode.JOIN_REJECTED_FULL
        
        # Check if vehicle is already in cluster
        if message.source_id in cluster.member_ids or message.source_id == cluster.head_id:
            return JoinResponseCode.JOIN_REJECTED_DUPLICATE
        
        # Trust-based validation: Check if requesting vehicle is trustworthy
        if self.trust_enabled:
            # Reject malicious vehicles
            if self.is_node_malicious(message.source_id):
                self.logger.warning(f"Join request rejected: vehicle {message.source_id} is malicious")
                return JoinResponseCode.JOIN_REJECTED_INCOMPATIBLE
            
            # Check minimum trust threshold for cluster membership
            requester_trust = self._get_vehicle_trust_score(message.source_id)
            if requester_trust < 0.4:  # Minimum trust for joining (lower than head threshold)
                self.logger.info(f"Join request rejected: vehicle {message.source_id} trust score {requester_trust:.2f} too low")
                return JoinResponseCode.JOIN_REJECTED_INCOMPATIBLE
        
        # Check compatibility (simplified)
        speed_diff = abs(message.speed - cluster.avg_speed)
        direction_diff = abs(message.direction - cluster.avg_direction)
        
        if speed_diff > self.clustering_engine.speed_threshold:
            return JoinResponseCode.JOIN_REJECTED_INCOMPATIBLE
        
        if direction_diff > self.clustering_engine.direction_threshold:
            return JoinResponseCode.JOIN_REJECTED_INCOMPATIBLE
        
        return JoinResponseCode.JOIN_ACCEPTED
    
    def _handle_join_response(self, message: VANETMessage, result: Dict[str, Any]):
        """Handle cluster join response"""
        if result['accepted']:
            # Update vehicle cluster assignment
            if message.destination_id in self.vehicle_nodes:
                node = self.vehicle_nodes[message.destination_id]
                old_cluster = node.cluster_id
                node.cluster_id = message.cluster_id
                node.is_cluster_head = False
                
                # Track cluster join event
                self.statistics['cluster_joins'] += 1
                self.logger.info(f"Vehicle {message.destination_id} joined cluster {message.cluster_id}")
                
                # If vehicle was in another cluster, track leave event
                if old_cluster and old_cluster != message.cluster_id:
                    self.statistics['cluster_leaves'] += 1
                    self.logger.info(f"Vehicle {message.destination_id} left cluster {old_cluster}")
        else:
            self.logger.info(f"Vehicle {message.destination_id} join rejected: {result['reason']}")
    
    def _handle_merge_request(self, message: VANETMessage, result: Dict[str, Any]):
        """Handle cluster merge request"""
        source_cluster = result['source_cluster']
        target_cluster = result['target_cluster']
        
        # Evaluate merge request
        response_code = MergeResponseCode.MERGE_ACCEPTED  # Simplified logic
        
        # Send response
        if target_cluster in self.clustering_engine.clusters:
            cluster = self.clustering_engine.clusters[target_cluster]
            if cluster.head_id in self.vehicle_nodes:
                head_node = self.vehicle_nodes[cluster.head_id]
                head_vehicle = head_node.to_vehicle()
                
                response = self.message_processor.create_merge_response(
                    head_vehicle, source_cluster, message.source_id, response_code, cluster
                )
                self._send_message(response)
    
    def _handle_merge_response(self, message: VANETMessage, result: Dict[str, Any]):
        """Handle cluster merge response"""
        if result['accepted']:
            self.logger.info(f"Cluster merge accepted between {result['source_cluster']} "
                           f"and {result['target_cluster']}")
        else:
            self.logger.info(f"Cluster merge rejected")
    
    def _handle_emergency_message(self, message: VANETMessage, result: Dict[str, Any]):
        """Handle emergency message"""
        self.logger.warning(f"Emergency message from {result['source']}: {result['data']}")
        
        # Forward emergency message if needed
        if result.get('requires_forwarding'):
            # Implement emergency message forwarding logic
            pass
    
    def _update_neighbor_info(self, result: Dict[str, Any]):
        """Update neighbor information from beacon"""
        vehicle_id = result['vehicle_id']
        
        if vehicle_id in self.vehicle_nodes:
            node = self.vehicle_nodes[vehicle_id]
            node.location = result['position']
            node.speed = result['speed']
            node.direction = result['direction']
            node.last_update = self.current_time
            
            # Update cluster info
            cluster_info = result['cluster_info']
            if cluster_info['cluster_id']:
                node.cluster_id = cluster_info['cluster_id']
                node.is_cluster_head = cluster_info['is_head']
    
    def _send_message(self, message: VANETMessage) -> bool:
        """Send message through the network"""
        try:
            # Add to message queue (simulation of network transmission)
            message_id = f"{message.source_id}_{message.sequence_number}_{self.current_time}"
            self.message_queue[message_id] = message.to_dict()
            
            self.statistics['messages_sent'] += 1
            
            # Update trust for successful message creation
            if self.trust_enabled:
                self.update_trust_on_message_delivery(message.source_id, success=True)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending message: {e}")
            
            # Penalize trust for failed message sending
            if self.trust_enabled:
                self.update_trust_on_message_delivery(message.source_id, success=False)
            
            return False
    
    def _process_message_queue(self):
        """Process pending messages in queue"""
        messages_to_remove = []
        
        for message_id, message_data in self.message_queue.items():
            # Simulate message transmission delay and processing
            try:
                message = VANETMessage.from_dict(message_data)
                
                # Check if message should be delivered
                if self._should_deliver_message(message):
                    # Route message to appropriate vehicles
                    self._route_message_to_vehicles(message, message_data)
                    messages_to_remove.append(message_id)
                elif message.is_expired(self.current_time):
                    messages_to_remove.append(message_id)
                    
            except Exception as e:
                self.logger.error(f"Error processing queued message {message_id}: {e}")
                messages_to_remove.append(message_id)
        
        # Remove processed/expired messages
        for message_id in messages_to_remove:
            del self.message_queue[message_id]
    
    def _route_message_to_vehicles(self, message: VANETMessage, message_data: Dict[str, Any]):
        """Route message to appropriate vehicles based on type and proximity"""
        # Get sender location for proximity-based routing
        sender_node = self.vehicle_nodes.get(message.source_id)
        if not sender_node:
            return
        
        sender_x, sender_y = sender_node.location
        communication_range = 300.0  # meters
        
        # Determine target vehicles based on message type
        if message.message_type == 'BEACON':
            # Beacon messages go to nearby vehicles
            self._deliver_to_nearby_vehicles(message_data, sender_x, sender_y, communication_range)
        
        elif message.message_type in ['CLUSTER_JOIN_REQUEST', 'CLUSTER_HEAD_ANNOUNCEMENT', 
                                      'CLUSTER_HEARTBEAT', 'CLUSTER_ELECTION']:
            # Clustering messages go to cluster members or nearby vehicles
            if hasattr(message, 'cluster_id') and message.cluster_id:
                self._deliver_to_cluster_members(message_data, message.cluster_id)
            else:
                self._deliver_to_nearby_vehicles(message_data, sender_x, sender_y, communication_range)
        
        elif hasattr(message, 'target_id') and message.target_id:
            # Targeted message
            if message.target_id in self.vehicle_nodes:
                self.receive_message(message_data)
        
        else:
            # Broadcast message
            self._deliver_to_nearby_vehicles(message_data, sender_x, sender_y, communication_range)
    
    def _deliver_to_nearby_vehicles(self, message_data: Dict[str, Any], sender_x: float, 
                                   sender_y: float, range_meters: float):
        """Deliver message to vehicles within communication range"""
        message = VANETMessage.from_dict(message_data)
        delivered_count = 0
        
        for vehicle_id, node in self.vehicle_nodes.items():
            if vehicle_id == message.source_id:
                continue  # Don't deliver to sender
            
            # Calculate distance
            node_x, node_y = node.location
            distance = ((sender_x - node_x) ** 2 + (sender_y - node_y) ** 2) ** 0.5
            
            if distance <= range_meters:
                self._deliver_message_to_vehicle(message_data, vehicle_id)
                delivered_count += 1
        
        if delivered_count > 0:
            self.logger.debug(f"Delivered {message.message_type} message to {delivered_count} nearby vehicles")
        else:
            self.logger.debug(f"No vehicles in range for {message.message_type} message from {message.source_id}")
    
    def _deliver_to_cluster_members(self, message_data: Dict[str, Any], cluster_id: str):
        """Deliver message to all members of a specific cluster"""
        message = VANETMessage.from_dict(message_data)
        delivered_count = 0
        
        for vehicle_id, node in self.vehicle_nodes.items():
            if vehicle_id == message.source_id:
                continue  # Don't deliver to sender
            
            if node.cluster_id == cluster_id:
                self._deliver_message_to_vehicle(message_data, vehicle_id)
                delivered_count += 1
        
        if delivered_count > 0:
            self.logger.debug(f"Delivered {message.message_type} message to {delivered_count} cluster members")
    
    def _deliver_message_to_vehicle(self, message_data: Dict[str, Any], vehicle_id: str):
        """Deliver a message to a specific vehicle"""
        # In a real VANET system, each vehicle would have its own application instance
        # For simulation, we track deliveries to different vehicles
        self.logger.debug(f"Delivering message {message_data.get('message_type', 'UNKNOWN')} to vehicle {vehicle_id}")
        
        # Increment received message counter for this delivery
        self.statistics['messages_received'] += 1
        
        # Add message to vehicle's buffer
        if vehicle_id in self.vehicle_nodes:
            node = self.vehicle_nodes[vehicle_id]
            node.message_buffer.append(message_data)
            
            # Process the message for this vehicle
            self._process_received_message(message_data, vehicle_id)
    
    def _process_received_message(self, message_data: Dict[str, Any], receiver_id: str):
        """Process a message received by a specific vehicle"""
        try:
            message = VANETMessage.from_dict(message_data)
            
            # Update neighbor information from beacons
            if message.message_type == 'BEACON' and receiver_id in self.vehicle_nodes:
                receiver_node = self.vehicle_nodes[receiver_id]
                receiver_node.neighbors.add(message.source_id)
            
            # Handle cluster-specific messages
            elif message.message_type in ['CLUSTER_JOIN_REQUEST', 'CLUSTER_HEAD_ANNOUNCEMENT']:
                # Process clustering messages
                result = self.message_processor.process_message(message, self.current_time)
                if result:
                    self._handle_message_processing_result(message, result)
            
        except Exception as e:
            self.logger.error(f"Error processing received message for {receiver_id}: {e}")
    
    def _should_deliver_message(self, message: VANETMessage) -> bool:
        """Determine if message should be delivered (improved routing)"""
        # Check message age - messages sent in previous timesteps can be delivered
        # Since our simulation uses 0.5s timesteps, any message older than the current
        # timestep boundary can be delivered
        message_age = self.current_time - message.timestamp
        
        # Allow delivery after at least one simulation processing cycle
        # This prevents same-timestep delivery but allows next-step delivery
        if message_age <= 0:  # Same timestamp, not yet processed
            return False
        
        # Check if message is expired
        if message.is_expired(self.current_time):
            self.logger.debug(f"Message {message.message_type} from {message.source_id} expired")
            return False
        
        # For clustering messages, always deliver after delay
        if message.message_type in ['BEACON', 'CLUSTER_JOIN_REQUEST', 'CLUSTER_HEAD_ANNOUNCEMENT',
                                     'CLUSTER_HEARTBEAT', 'CLUSTER_ELECTION', 'CLUSTER_HANDOVER',
                                     'CLUSTER_MERGE_REQUEST', 'CLUSTER_SPLIT_NOTIFICATION',
                                     'CLUSTER_LEAVE_NOTIFICATION', 'CLUSTER_JOIN_RESPONSE']:
            return True
        
        # For targeted messages, check if target exists
        if hasattr(message, 'target_id') and message.target_id:
            return message.target_id in self.vehicle_nodes
        
        # For data and emergency messages, deliver to nearby vehicles
        if message.message_type in ['DATA', 'EMERGENCY']:
            return True
        
        # Broadcast messages - deliver after delay
        return True
    
    def _cleanup_old_data(self):
        """Clean up old data and expired elements"""
        current_time = self.current_time
        
        # Clean up old neighbor information
        vehicles_to_remove = []
        for vehicle_id, node in self.vehicle_nodes.items():
            if (current_time - node.last_update) > self.config['neighbor_timeout']:
                vehicles_to_remove.append(vehicle_id)
        
        for vehicle_id in vehicles_to_remove:
            self.remove_vehicle(vehicle_id)
        
        # Clean up message buffers
        for node in self.vehicle_nodes.values():
            if len(node.message_buffer) > self.config['max_message_buffer_size']:
                node.message_buffer = node.message_buffer[-self.config['max_message_buffer_size']:]
    
    def get_application_statistics(self) -> Dict[str, Any]:
        """Get comprehensive application statistics"""
        cluster_stats = self.cluster_manager.get_cluster_management_statistics()
        message_stats = self.message_processor.get_message_statistics()
        clustering_stats = self.clustering_engine.get_cluster_statistics()
        trust_stats = self.get_trust_statistics()
        
        return {
            'application': {
                'total_vehicles': len(self.vehicle_nodes),
                'simulation_time': self.current_time,
                'simulation_steps': self.simulation_step,
                'messages_sent': self.statistics['messages_sent'],
                'messages_received': self.statistics['messages_received'],
                'clusters_formed': self.statistics['clusters_formed'],
                'cluster_joins': self.statistics['cluster_joins'],
                'cluster_leaves': self.statistics['cluster_leaves'],
                'head_elections': self.statistics['head_elections'],
                'trust_evaluations': self.statistics['trust_evaluations'],
                'malicious_nodes_detected': self.statistics['malicious_nodes_detected'],
                'consensus_messages': self.statistics['consensus_messages'],
                'trust_updates': self.statistics['trust_updates']
            },
            'clustering': clustering_stats,
            'cluster_management': cluster_stats,
            'message_processing': message_stats,
            'trust_and_security': trust_stats,
            'configuration': self.config
        }
    
    def set_configuration(self, config_updates: Dict[str, Any]):
        """Update application configuration"""
        self.config.update(config_updates)
        self.logger.info(f"Configuration updated: {config_updates}")
    
    def get_cluster_info(self, vehicle_id: str) -> Optional[Dict[str, Any]]:
        """Get cluster information for a specific vehicle"""
        if vehicle_id not in self.vehicle_nodes:
            return None
        
        node = self.vehicle_nodes[vehicle_id]
        if not node.cluster_id:
            return {'clustered': False}
        
        cluster = self.clustering_engine.clusters.get(node.cluster_id)
        if not cluster:
            return {'clustered': False}
        
        return {
            'clustered': True,
            'cluster_id': cluster.id,
            'is_head': node.is_cluster_head,
            'head_id': cluster.head_id,
            'member_count': cluster.size(),
            'members': list(cluster.member_ids),
            'cluster_state': self.cluster_manager.cluster_states.get(cluster.id, ClusterState.FORMING).value
        }
    
    # Trust and Security Helper Methods
    
    def _calculate_network_participation(self, node_id: str) -> float:
        """Calculate network participation score for a node"""
        if node_id not in self.vehicle_nodes:
            return 0.0
        
        node = self.vehicle_nodes[node_id]
        
        # Base participation on message activity and cluster involvement
        message_activity = min(len(node.message_buffer) / 50.0, 1.0)  # Normalize to 0-1
        cluster_participation = 1.0 if node.cluster_id else 0.5
        neighbor_interaction = min(len(node.neighbors) / 10.0, 1.0)
        
        return (message_activity + cluster_participation + neighbor_interaction) / 3.0
    
    def _calculate_response_reliability(self, node_id: str) -> float:
        """Calculate response reliability score for a node"""
        if node_id not in self.vehicle_nodes:
            return 0.0
        
        # In a real implementation, this would track message response rates
        # For simulation, we'll use a baseline score with some variance
        node = self.vehicle_nodes[node_id]
        
        # Factor in how long the node has been active
        activity_duration = self.current_time - (node.last_update - 3600)  # Assume 1 hour max
        reliability_base = min(activity_duration / 3600.0, 1.0)
        
        # Factor in malicious activity count
        malicious_penalty = min(node.malicious_activity_count * 0.1, 0.5)
        
        return max(0.0, reliability_base - malicious_penalty)
    
    def _collect_behavior_data(self, node_id: str) -> Dict[str, Any]:
        """Collect behavior data for trust evaluation"""
        if node_id not in self.vehicle_nodes:
            return {}
        
        node = self.vehicle_nodes[node_id]
        current_time = time.time()
        
        # Simulate behavior data collection
        behavior_data = {
            'location': node.location,
            'previous_location': node.location,  # Would be tracked in real system
            'time_diff': 1.0,  # Simulated time difference
            'max_reasonable_speed': 200,  # km/h
            'message_integrity': node.message_authenticity_score,
            'response_times': [0.1, 0.15, 0.08, 0.12, 0.09],  # Simulated response times
            'activity_timestamp': current_time
        }
        
        return behavior_data
    
    def _handle_malicious_node_detected(self, node_id: str, malicious_activity: MaliciousActivity):
        """Handle detection of malicious node"""
        self.logger.warning(f"Malicious node detected: {node_id} - {malicious_activity.activity_type}")
        
        # Update statistics
        self.statistics['malicious_nodes_detected'] += 1
        
        # Mark node as malicious
        if node_id in self.vehicle_nodes:
            node = self.vehicle_nodes[node_id]
            node.is_malicious = True
            node.trust_score = min(node.trust_score, 0.2)  # Significantly reduce trust
        
        # If node is cluster head, trigger head change
        if node_id in self.vehicle_nodes and self.vehicle_nodes[node_id].is_cluster_head:
            self._handle_malicious_cluster_head(node_id)
        
        # Broadcast warning to other nodes
        self._broadcast_malicious_node_warning(node_id, malicious_activity)
    
    def _handle_malicious_cluster_head(self, head_id: str):
        """Handle malicious cluster head detection"""
        self.logger.warning(f"Malicious cluster head detected: {head_id}")
        
        # Force immediate head election in the cluster
        if head_id in self.vehicle_nodes:
            cluster_id = self.vehicle_nodes[head_id].cluster_id
            if cluster_id and cluster_id in self.clustering_engine.clusters:
                cluster = self.clustering_engine.clusters[cluster_id]
                
                # Remove malicious head
                cluster.member_ids.discard(head_id)
                if head_id == cluster.head_id:
                    # Trigger emergency head election
                    self._emergency_head_election(cluster)
    
    def _emergency_head_election(self, cluster: Cluster):
        """Perform emergency head election due to malicious head"""
        self.logger.info(f"Emergency head election for cluster {cluster.id}")
        
        if not cluster.member_ids:
            # No members left, dissolve cluster
            del self.clustering_engine.clusters[cluster.id]
            return
        
        # Select new head based on highest trust score
        best_candidate = None
        best_trust_score = 0.0
        
        for member_id in cluster.member_ids:
            if member_id in self.vehicle_nodes and not self.vehicle_nodes[member_id].is_malicious:
                trust_score = self.vehicle_nodes[member_id].trust_score
                if trust_score > best_trust_score:
                    best_trust_score = trust_score
                    best_candidate = member_id
        
        if best_candidate:
            # Update cluster head
            old_head = cluster.head_id
            cluster.head_id = best_candidate
            
            # Update node properties
            if old_head in self.vehicle_nodes:
                self.vehicle_nodes[old_head].is_cluster_head = False
            
            self.vehicle_nodes[best_candidate].is_cluster_head = True
            
            self.logger.info(f"New cluster head elected: {best_candidate} for cluster {cluster.id}")
            self.statistics['head_elections'] += 1
    
    def _broadcast_malicious_node_warning(self, node_id: str, malicious_activity: MaliciousActivity):
        """Broadcast warning about malicious node"""
        if not self.consensus_engine:
            return
        
        warning_message = ConsensusMessage(
            msg_type=ConsensusMessageType.MALICIOUS_NODE_REPORT,
            sender_id=self.consensus_engine.node_id if hasattr(self.consensus_engine, 'node_id') else "system",
            receiver_id="broadcast",
            term=0,
            data={
                'target_node': node_id,
                'activity_type': malicious_activity.activity_type,
                'severity': malicious_activity.severity,
                'evidence': malicious_activity.evidence,
                'timestamp': malicious_activity.timestamp
            }
        )
        
        self._broadcast_consensus_message(warning_message)
    
    def _broadcast_consensus_message(self, message: ConsensusMessage):
        """Broadcast consensus message to all nodes"""
        if not self.consensus_engine:
            return
        
        # In a real system, this would send to all reachable nodes
        # For simulation, we process locally and track the activity
        self.statistics['consensus_messages'] += 1
        
        # Process the message if we're an authority node
        response = self.consensus_engine.process_message(message)
        if response:
            self.logger.debug(f"Generated consensus response: {response.msg_type}")
    
    def get_trust_statistics(self) -> Dict[str, Any]:
        """Get trust and security statistics"""
        if not self.trust_enabled or not self.consensus_engine:
            return {'trust_enabled': False}
        
        trusted_nodes = sum(1 for node in self.vehicle_nodes.values() 
                          if node.trust_score >= self.trusted_threshold)
        malicious_nodes = sum(1 for node in self.vehicle_nodes.values() 
                            if node.is_malicious)
        
        trust_scores = [node.trust_score for node in self.vehicle_nodes.values()]
        avg_trust = sum(trust_scores) / len(trust_scores) if trust_scores else 0.0
        
        consensus_stats = self.consensus_engine.get_consensus_statistics()
        
        return {
            'trust_enabled': True,
            'total_nodes': len(self.vehicle_nodes),
            'trusted_nodes': trusted_nodes,
            'malicious_nodes': malicious_nodes,
            'average_trust_score': avg_trust,
            'trust_evaluations': self.statistics['trust_evaluations'],
            'malicious_detections': self.statistics['malicious_nodes_detected'],
            'trust_updates': self.statistics['trust_updates'],
            'consensus_messages': self.statistics['consensus_messages'],
            'authority_nodes': len(self.authority_nodes),
            'consensus_stats': consensus_stats
        }