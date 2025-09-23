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
from .cluster_manager import ClusterManager, ClusterState, ClusterMetrics
from .message_processor import (
    MessageProcessor, VANETMessage, MessageType, 
    JoinResponseCode, MergeResponseCode
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
        self.cluster_manager = ClusterManager(self.clustering_engine)
        self.message_processor = MessageProcessor()
        
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
            'head_elections': 0
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
    
    def receive_message(self, message_data: Dict[str, Any]):
        """Receive and process incoming message"""
        try:
            # Convert dictionary to VANETMessage
            message = VANETMessage.from_dict(message_data)
            
            self.logger.debug(f"Received {message.message_type} message from {message.source_id}")
            
            # Process message
            result = self.message_processor.process_message(message, self.current_time)
            
            # Handle processing result
            self._handle_message_processing_result(message, result)
            
            self.statistics['messages_received'] += 1
            
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
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending message: {e}")
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
        self.receive_message(message_data)
    
    def _should_deliver_message(self, message: VANETMessage) -> bool:
        """Determine if message should be delivered (improved routing)"""
        # Check message age (small delay for network transmission)
        message_age = self.current_time - message.timestamp
        if message_age < 0.05:  # 50ms minimum transmission delay
            return False
        
        # For clustering demo, deliver messages to nearby vehicles
        if message.message_type in ['BEACON', 'CLUSTER_JOIN_REQUEST', 'CLUSTER_HEAD_ANNOUNCEMENT']:
            # Always deliver clustering messages after delay
            return True
        
        # For other messages, check if there are target vehicles
        if hasattr(message, 'target_id') and message.target_id:
            # Targeted message - deliver if target exists
            return message.target_id in self.vehicle_nodes
        
        # Broadcast messages - deliver to all vehicles after delay
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
                'head_elections': self.statistics['head_elections']
            },
            'clustering': clustering_stats,
            'cluster_management': cluster_stats,
            'message_processing': message_stats,
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