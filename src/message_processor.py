"""
VANET Clustering Message Processing

This module provides Python-side message processing and handling for clustering
operations, complementing the OMNeT++ message definitions.
"""

import time
import json
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, asdict
from enum import Enum
import logging

from .clustering import Vehicle, Cluster
from .cluster_manager import ClusterEvent, ClusterState

class MessageType(Enum):
    # Basic messages
    BEACON = 0
    DATA_BROADCAST = 1
    
    # Cluster formation messages
    CLUSTER_HEAD_ANNOUNCEMENT = 10
    CLUSTER_JOIN_REQUEST = 11
    CLUSTER_JOIN_RESPONSE = 12
    CLUSTER_LEAVE_NOTIFICATION = 13
    
    # Cluster maintenance messages
    CLUSTER_HEARTBEAT = 20
    CLUSTER_HEAD_ELECTION = 21
    CLUSTER_HEAD_HANDOVER = 22
    CLUSTER_MERGE_REQUEST = 23
    CLUSTER_MERGE_RESPONSE = 24
    CLUSTER_SPLIT_NOTIFICATION = 25
    
    # Cluster data dissemination
    INTRA_CLUSTER_DATA = 30
    INTER_CLUSTER_DATA = 31
    CLUSTER_GATEWAY_DATA = 32
    
    # Emergency and priority messages
    EMERGENCY_BROADCAST = 40
    CLUSTER_EMERGENCY = 41
    
    # Network management
    NEIGHBOR_DISCOVERY = 50
    LINK_STATE_UPDATE = 51
    ROUTE_REQUEST = 52
    ROUTE_RESPONSE = 53

class JoinResponseCode(Enum):
    JOIN_ACCEPTED = 0
    JOIN_REJECTED_FULL = 1
    JOIN_REJECTED_INCOMPATIBLE = 2
    JOIN_REJECTED_DUPLICATE = 3

class MergeResponseCode(Enum):
    MERGE_ACCEPTED = 0
    MERGE_REJECTED_SIZE = 1
    MERGE_REJECTED_INCOMPATIBLE = 2
    MERGE_REJECTED_BUSY = 3

@dataclass
class VANETMessage:
    """Python representation of VANET messages"""
    # Basic fields
    message_type: MessageType
    source_id: str
    destination_id: str = ""
    position: tuple = (0.0, 0.0)
    speed: float = 0.0
    direction: float = 0.0
    hop_count: int = 0
    timestamp: float = 0.0
    sequence_number: int = 0
    
    # Vehicle properties
    lane_id: str = ""
    acceleration: float = 0.0
    vehicle_type: str = "default"
    
    # Clustering fields
    is_cluster_head: bool = False
    cluster_id: str = ""
    cluster_head_id: str = ""
    cluster_radius: float = 0.0
    member_count: int = 0
    cluster_state: ClusterState = ClusterState.FORMING
    
    # Advanced clustering
    cluster_stability: float = 0.0
    cluster_quality: float = 0.0
    cluster_lifetime: float = 0.0
    member_list: List[str] = None
    neighbor_clusters: List[str] = None
    
    # Election fields
    connectivity_score: float = 0.0
    mobility_score: float = 0.0
    position_score: float = 0.0
    composite_score: float = 0.0
    election_round: int = 0
    
    # Join/Leave fields
    join_response_code: JoinResponseCode = JoinResponseCode.JOIN_ACCEPTED
    rejection_reason: str = ""
    compatibility_score: float = 0.0
    
    # Merge/Split fields
    merge_target_cluster: str = ""
    merge_response_code: MergeResponseCode = MergeResponseCode.MERGE_ACCEPTED
    split_groups: List[str] = None
    split_reason: str = ""
    
    # Data fields
    payload: str = ""
    priority: int = 0
    requires_ack: bool = False
    data_type: str = ""
    data_timestamp: float = 0.0
    is_emergency: bool = False
    
    # Network topology
    neighbor_ids: List[str] = None
    neighbor_distances: List[float] = None
    neighbor_signal_strengths: List[float] = None
    
    # QoS fields
    retry_count: int = 0
    expiry_time: float = 0.0
    is_reliable: bool = False
    original_source: str = ""
    
    # Geographic routing
    destination_position: tuple = (0.0, 0.0)
    max_hop_distance: float = 0.0
    routing_mode: str = "geographic"
    
    # Security
    is_signed: bool = False
    security_hash: str = ""
    certificate_expiry: float = 0.0
    
    def __post_init__(self):
        if self.member_list is None:
            self.member_list = []
        if self.neighbor_clusters is None:
            self.neighbor_clusters = []
        if self.split_groups is None:
            self.split_groups = []
        if self.neighbor_ids is None:
            self.neighbor_ids = []
        if self.neighbor_distances is None:
            self.neighbor_distances = []
        if self.neighbor_signal_strengths is None:
            self.neighbor_signal_strengths = []
        if self.timestamp == 0.0:
            self.timestamp = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary for serialization"""
        data = asdict(self)
        # Convert enums to their values
        data['message_type'] = self.message_type.value
        data['cluster_state'] = self.cluster_state.value
        data['join_response_code'] = self.join_response_code.value
        data['merge_response_code'] = self.merge_response_code.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VANETMessage':
        """Create message from dictionary"""
        # Convert enum values back to enums
        data['message_type'] = MessageType(data['message_type'])
        data['cluster_state'] = ClusterState(data['cluster_state'])
        data['join_response_code'] = JoinResponseCode(data['join_response_code'])
        data['merge_response_code'] = MergeResponseCode(data['merge_response_code'])
        return cls(**data)
    
    def is_clustering_message(self) -> bool:
        """Check if this is a clustering-related message"""
        clustering_types = {
            MessageType.CLUSTER_HEAD_ANNOUNCEMENT,
            MessageType.CLUSTER_JOIN_REQUEST,
            MessageType.CLUSTER_JOIN_RESPONSE,
            MessageType.CLUSTER_LEAVE_NOTIFICATION,
            MessageType.CLUSTER_HEARTBEAT,
            MessageType.CLUSTER_HEAD_ELECTION,
            MessageType.CLUSTER_HEAD_HANDOVER,
            MessageType.CLUSTER_MERGE_REQUEST,
            MessageType.CLUSTER_MERGE_RESPONSE,
            MessageType.CLUSTER_SPLIT_NOTIFICATION
        }
        return self.message_type in clustering_types
    
    def is_expired(self, current_time: float = None) -> bool:
        """Check if message has expired"""
        if self.expiry_time == 0.0:
            return False
        
        if current_time is None:
            current_time = time.time()
        
        return current_time > self.expiry_time

class MessageProcessor:
    """Processes and validates VANET clustering messages"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.message_history: Dict[str, List[VANETMessage]] = {}
        self.pending_responses: Dict[str, VANETMessage] = {}
        self.message_sequence_counters: Dict[str, int] = {}
    
    def create_beacon_message(self, vehicle: Vehicle, cluster: Optional[Cluster] = None) -> VANETMessage:
        """Create a beacon message for a vehicle"""
        message = VANETMessage(
            message_type=MessageType.BEACON,
            source_id=vehicle.id,
            position=(vehicle.x, vehicle.y),
            speed=vehicle.speed,
            direction=vehicle.direction,
            lane_id=vehicle.lane_id,
            sequence_number=self._get_next_sequence(vehicle.id)
        )
        
        if cluster:
            message.is_cluster_head = (cluster.head_id == vehicle.id)
            message.cluster_id = cluster.id
            message.cluster_head_id = cluster.head_id
            message.member_count = cluster.size()
            message.cluster_radius = 300.0  # Default radius
        
        return message
    
    def create_cluster_head_announcement(self, vehicle: Vehicle, cluster: Cluster) -> VANETMessage:
        """Create cluster head announcement message"""
        return VANETMessage(
            message_type=MessageType.CLUSTER_HEAD_ANNOUNCEMENT,
            source_id=vehicle.id,
            position=(vehicle.x, vehicle.y),
            speed=vehicle.speed,
            direction=vehicle.direction,
            is_cluster_head=True,
            cluster_id=cluster.id,
            cluster_head_id=cluster.head_id,
            member_count=cluster.size(),
            cluster_radius=300.0,
            cluster_stability=1.0,  # New cluster
            member_list=list(cluster.member_ids),
            sequence_number=self._get_next_sequence(vehicle.id)
        )
    
    def create_join_request(self, vehicle: Vehicle, target_cluster_id: str, 
                           target_head_id: str) -> VANETMessage:
        """Create cluster join request message"""
        return VANETMessage(
            message_type=MessageType.CLUSTER_JOIN_REQUEST,
            source_id=vehicle.id,
            destination_id=target_head_id,
            position=(vehicle.x, vehicle.y),
            speed=vehicle.speed,
            direction=vehicle.direction,
            cluster_id=target_cluster_id,
            requires_ack=True,
            sequence_number=self._get_next_sequence(vehicle.id)
        )
    
    def create_join_response(self, head_vehicle: Vehicle, requesting_vehicle_id: str, 
                            response_code: JoinResponseCode, cluster: Cluster,
                            reason: str = "") -> VANETMessage:
        """Create cluster join response message"""
        return VANETMessage(
            message_type=MessageType.CLUSTER_JOIN_RESPONSE,
            source_id=head_vehicle.id,
            destination_id=requesting_vehicle_id,
            position=(head_vehicle.x, head_vehicle.y),
            cluster_id=cluster.id,
            join_response_code=response_code,
            rejection_reason=reason,
            member_count=cluster.size(),
            member_list=list(cluster.member_ids),
            sequence_number=self._get_next_sequence(head_vehicle.id)
        )
    
    def create_leave_notification(self, vehicle: Vehicle, cluster_id: str) -> VANETMessage:
        """Create cluster leave notification message"""
        return VANETMessage(
            message_type=MessageType.CLUSTER_LEAVE_NOTIFICATION,
            source_id=vehicle.id,
            cluster_id=cluster_id,
            position=(vehicle.x, vehicle.y),
            sequence_number=self._get_next_sequence(vehicle.id)
        )
    
    def create_heartbeat_message(self, vehicle: Vehicle, cluster: Cluster, 
                                metrics: Dict[str, float]) -> VANETMessage:
        """Create cluster heartbeat message"""
        return VANETMessage(
            message_type=MessageType.CLUSTER_HEARTBEAT,
            source_id=vehicle.id,
            cluster_id=cluster.id,
            position=(vehicle.x, vehicle.y),
            speed=vehicle.speed,
            direction=vehicle.direction,
            cluster_stability=metrics.get('stability', 0.0),
            cluster_quality=metrics.get('quality', 0.0),
            cluster_lifetime=metrics.get('lifetime', 0.0),
            member_count=cluster.size(),
            sequence_number=self._get_next_sequence(vehicle.id)
        )
    
    def create_election_message(self, vehicle: Vehicle, cluster_id: str, 
                               scores: Dict[str, float], round_number: int) -> VANETMessage:
        """Create cluster head election message"""
        return VANETMessage(
            message_type=MessageType.CLUSTER_HEAD_ELECTION,
            source_id=vehicle.id,
            cluster_id=cluster_id,
            position=(vehicle.x, vehicle.y),
            speed=vehicle.speed,
            direction=vehicle.direction,
            connectivity_score=scores.get('connectivity', 0.0),
            mobility_score=scores.get('mobility', 0.0),
            position_score=scores.get('position', 0.0),
            composite_score=scores.get('composite', 0.0),
            election_round=round_number,
            sequence_number=self._get_next_sequence(vehicle.id)
        )
    
    def create_handover_message(self, old_head: Vehicle, new_head_id: str, 
                               cluster: Cluster) -> VANETMessage:
        """Create cluster head handover message"""
        return VANETMessage(
            message_type=MessageType.CLUSTER_HEAD_HANDOVER,
            source_id=old_head.id,
            destination_id=new_head_id,
            cluster_id=cluster.id,
            cluster_head_id=new_head_id,
            member_list=list(cluster.member_ids),
            member_count=cluster.size(),
            position=(old_head.x, old_head.y),
            sequence_number=self._get_next_sequence(old_head.id)
        )
    
    def create_merge_request(self, head_vehicle: Vehicle, source_cluster: Cluster, 
                            target_cluster_id: str, target_head_id: str) -> VANETMessage:
        """Create cluster merge request message"""
        return VANETMessage(
            message_type=MessageType.CLUSTER_MERGE_REQUEST,
            source_id=head_vehicle.id,
            destination_id=target_head_id,
            cluster_id=source_cluster.id,
            merge_target_cluster=target_cluster_id,
            member_count=source_cluster.size(),
            member_list=list(source_cluster.member_ids),
            position=(head_vehicle.x, head_vehicle.y),
            requires_ack=True,
            sequence_number=self._get_next_sequence(head_vehicle.id)
        )
    
    def create_merge_response(self, head_vehicle: Vehicle, requesting_cluster_id: str, 
                             requesting_head_id: str, response_code: MergeResponseCode,
                             cluster: Cluster) -> VANETMessage:
        """Create cluster merge response message"""
        return VANETMessage(
            message_type=MessageType.CLUSTER_MERGE_RESPONSE,
            source_id=head_vehicle.id,
            destination_id=requesting_head_id,
            cluster_id=cluster.id,
            merge_target_cluster=requesting_cluster_id,
            merge_response_code=response_code,
            member_count=cluster.size(),
            position=(head_vehicle.x, head_vehicle.y),
            sequence_number=self._get_next_sequence(head_vehicle.id)
        )
    
    def create_split_notification(self, head_vehicle: Vehicle, cluster_id: str, 
                                 split_groups: List[List[str]], reason: str) -> VANETMessage:
        """Create cluster split notification message"""
        return VANETMessage(
            message_type=MessageType.CLUSTER_SPLIT_NOTIFICATION,
            source_id=head_vehicle.id,
            cluster_id=cluster_id,
            split_groups=[",".join(group) for group in split_groups],
            split_reason=reason,
            position=(head_vehicle.x, head_vehicle.y),
            sequence_number=self._get_next_sequence(head_vehicle.id)
        )
    
    def create_data_message(self, vehicle: Vehicle, data: str, data_type: str,
                           cluster_id: str = "", is_inter_cluster: bool = False,
                           priority: int = 0, is_emergency: bool = False) -> VANETMessage:
        """Create data dissemination message"""
        if is_inter_cluster:
            msg_type = MessageType.INTER_CLUSTER_DATA
        elif cluster_id:
            msg_type = MessageType.INTRA_CLUSTER_DATA
        else:
            msg_type = MessageType.DATA_BROADCAST
        
        return VANETMessage(
            message_type=msg_type,
            source_id=vehicle.id,
            cluster_id=cluster_id,
            payload=data,
            data_type=data_type,
            priority=priority,
            is_emergency=is_emergency,
            position=(vehicle.x, vehicle.y),
            data_timestamp=time.time(),
            sequence_number=self._get_next_sequence(vehicle.id)
        )
    
    def create_emergency_message(self, vehicle: Vehicle, emergency_data: str,
                                cluster_id: str = "") -> VANETMessage:
        """Create emergency broadcast message"""
        msg_type = MessageType.CLUSTER_EMERGENCY if cluster_id else MessageType.EMERGENCY_BROADCAST
        
        return VANETMessage(
            message_type=msg_type,
            source_id=vehicle.id,
            cluster_id=cluster_id,
            payload=emergency_data,
            data_type="emergency",
            priority=10,  # Highest priority
            is_emergency=True,
            position=(vehicle.x, vehicle.y),
            data_timestamp=time.time(),
            expiry_time=time.time() + 60.0,  # Emergency messages expire in 1 minute
            sequence_number=self._get_next_sequence(vehicle.id)
        )
    
    def process_message(self, message: VANETMessage, current_time: float = None) -> Dict[str, Any]:
        """Process an incoming message and return processing results"""
        if current_time is None:
            current_time = time.time()
        
        # Check if message is expired
        if message.is_expired(current_time):
            return {
                'status': 'expired',
                'action': 'discard',
                'reason': 'Message expired'
            }
        
        # Log message
        self._log_message(message)
        
        # Process based on message type
        if message.message_type == MessageType.BEACON:
            return self._process_beacon(message)
        elif message.message_type == MessageType.CLUSTER_HEAD_ANNOUNCEMENT:
            return self._process_head_announcement(message)
        elif message.message_type == MessageType.CLUSTER_JOIN_REQUEST:
            return self._process_join_request(message)
        elif message.message_type == MessageType.CLUSTER_JOIN_RESPONSE:
            return self._process_join_response(message)
        elif message.message_type == MessageType.CLUSTER_LEAVE_NOTIFICATION:
            return self._process_leave_notification(message)
        elif message.message_type == MessageType.CLUSTER_HEARTBEAT:
            return self._process_heartbeat(message)
        elif message.message_type == MessageType.CLUSTER_HEAD_ELECTION:
            return self._process_election_message(message)
        elif message.message_type == MessageType.CLUSTER_HEAD_HANDOVER:
            return self._process_handover_message(message)
        elif message.message_type == MessageType.CLUSTER_MERGE_REQUEST:
            return self._process_merge_request(message)
        elif message.message_type == MessageType.CLUSTER_MERGE_RESPONSE:
            return self._process_merge_response(message)
        elif message.message_type == MessageType.CLUSTER_SPLIT_NOTIFICATION:
            return self._process_split_notification(message)
        elif message.is_emergency:
            return self._process_emergency_message(message)
        else:
            return self._process_data_message(message)
    
    def _get_next_sequence(self, vehicle_id: str) -> int:
        """Get next sequence number for a vehicle"""
        if vehicle_id not in self.message_sequence_counters:
            self.message_sequence_counters[vehicle_id] = 0
        self.message_sequence_counters[vehicle_id] += 1
        return self.message_sequence_counters[vehicle_id]
    
    def _log_message(self, message: VANETMessage):
        """Log message for history tracking"""
        if message.source_id not in self.message_history:
            self.message_history[message.source_id] = []
        
        self.message_history[message.source_id].append(message)
        
        # Keep only recent messages (last 100 per vehicle)
        if len(self.message_history[message.source_id]) > 100:
            self.message_history[message.source_id] = self.message_history[message.source_id][-100:]
    
    def _process_beacon(self, message: VANETMessage) -> Dict[str, Any]:
        """Process beacon message"""
        return {
            'status': 'processed',
            'action': 'update_neighbor',
            'vehicle_id': message.source_id,
            'position': message.position,
            'speed': message.speed,
            'direction': message.direction,
            'cluster_info': {
                'is_head': message.is_cluster_head,
                'cluster_id': message.cluster_id,
                'head_id': message.cluster_head_id
            }
        }
    
    def _process_head_announcement(self, message: VANETMessage) -> Dict[str, Any]:
        """Process cluster head announcement"""
        return {
            'status': 'processed',
            'action': 'cluster_head_announced',
            'cluster_id': message.cluster_id,
            'head_id': message.source_id,
            'member_count': message.member_count,
            'stability': message.cluster_stability,
            'members': message.member_list
        }
    
    def _process_join_request(self, message: VANETMessage) -> Dict[str, Any]:
        """Process cluster join request"""
        return {
            'status': 'processed',
            'action': 'join_request_received',
            'requesting_vehicle': message.source_id,
            'target_cluster': message.cluster_id,
            'vehicle_position': message.position,
            'vehicle_speed': message.speed,
            'requires_response': True
        }
    
    def _process_join_response(self, message: VANETMessage) -> Dict[str, Any]:
        """Process cluster join response"""
        return {
            'status': 'processed',
            'action': 'join_response_received',
            'response_code': message.join_response_code,
            'cluster_id': message.cluster_id,
            'head_id': message.source_id,
            'accepted': message.join_response_code == JoinResponseCode.JOIN_ACCEPTED,
            'reason': message.rejection_reason,
            'members': message.member_list
        }
    
    def _process_leave_notification(self, message: VANETMessage) -> Dict[str, Any]:
        """Process cluster leave notification"""
        return {
            'status': 'processed',
            'action': 'member_left',
            'leaving_vehicle': message.source_id,
            'cluster_id': message.cluster_id
        }
    
    def _process_heartbeat(self, message: VANETMessage) -> Dict[str, Any]:
        """Process cluster heartbeat message"""
        return {
            'status': 'processed',
            'action': 'cluster_heartbeat',
            'cluster_id': message.cluster_id,
            'source': message.source_id,
            'stability': message.cluster_stability,
            'quality': message.cluster_quality,
            'lifetime': message.cluster_lifetime,
            'member_count': message.member_count
        }
    
    def _process_election_message(self, message: VANETMessage) -> Dict[str, Any]:
        """Process cluster head election message"""
        return {
            'status': 'processed',
            'action': 'election_message',
            'cluster_id': message.cluster_id,
            'candidate': message.source_id,
            'scores': {
                'connectivity': message.connectivity_score,
                'mobility': message.mobility_score,
                'position': message.position_score,
                'composite': message.composite_score
            },
            'election_round': message.election_round
        }
    
    def _process_handover_message(self, message: VANETMessage) -> Dict[str, Any]:
        """Process cluster head handover message"""
        return {
            'status': 'processed',
            'action': 'head_handover',
            'cluster_id': message.cluster_id,
            'old_head': message.source_id,
            'new_head': message.destination_id,
            'members': message.member_list
        }
    
    def _process_merge_request(self, message: VANETMessage) -> Dict[str, Any]:
        """Process cluster merge request"""
        return {
            'status': 'processed',
            'action': 'merge_request_received',
            'source_cluster': message.cluster_id,
            'source_head': message.source_id,
            'target_cluster': message.merge_target_cluster,
            'source_members': message.member_list,
            'member_count': message.member_count,
            'requires_response': True
        }
    
    def _process_merge_response(self, message: VANETMessage) -> Dict[str, Any]:
        """Process cluster merge response"""
        return {
            'status': 'processed',
            'action': 'merge_response_received',
            'response_code': message.merge_response_code,
            'source_cluster': message.cluster_id,
            'target_cluster': message.merge_target_cluster,
            'accepted': message.merge_response_code == MergeResponseCode.MERGE_ACCEPTED
        }
    
    def _process_split_notification(self, message: VANETMessage) -> Dict[str, Any]:
        """Process cluster split notification"""
        split_groups = [group.split(',') for group in message.split_groups]
        return {
            'status': 'processed',
            'action': 'cluster_split',
            'cluster_id': message.cluster_id,
            'split_groups': split_groups,
            'reason': message.split_reason
        }
    
    def _process_emergency_message(self, message: VANETMessage) -> Dict[str, Any]:
        """Process emergency message"""
        return {
            'status': 'processed',
            'action': 'emergency_received',
            'source': message.source_id,
            'cluster_id': message.cluster_id,
            'data': message.payload,
            'priority': message.priority,
            'position': message.position,
            'timestamp': message.data_timestamp,
            'requires_forwarding': True
        }
    
    def _process_data_message(self, message: VANETMessage) -> Dict[str, Any]:
        """Process data message"""
        return {
            'status': 'processed',
            'action': 'data_received',
            'source': message.source_id,
            'cluster_id': message.cluster_id,
            'data_type': message.data_type,
            'data': message.payload,
            'priority': message.priority,
            'timestamp': message.data_timestamp
        }
    
    def get_message_statistics(self) -> Dict[str, Any]:
        """Get message processing statistics"""
        total_messages = sum(len(history) for history in self.message_history.values())
        
        # Count by message type
        type_counts = {}
        for history in self.message_history.values():
            for message in history:
                msg_type = message.message_type.name
                type_counts[msg_type] = type_counts.get(msg_type, 0) + 1
        
        return {
            'total_messages_processed': total_messages,
            'active_vehicles': len(self.message_history),
            'message_type_distribution': type_counts,
            'pending_responses': len(self.pending_responses)
        }