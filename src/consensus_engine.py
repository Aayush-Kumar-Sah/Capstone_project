"""
Consensus Engine for VANET Trust Evaluation and Malicious Node Detection

This module implements Raft and Proof of Authority (PoA) consensus algorithms
for distributed trust evaluation, leader election, and malicious node detection
in vehicular ad-hoc networks.
"""

import time
import logging
import random
import hashlib
import json
from typing import Dict, List, Optional, Set, Any, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
import threading
import asyncio
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class NodeState(Enum):
    """Raft node states"""
    FOLLOWER = "follower"
    CANDIDATE = "candidate"
    LEADER = "leader"
    OBSERVER = "observer"  # For PoA authorities

class TrustLevel(Enum):
    """Trust levels for node evaluation"""
    UNKNOWN = 0
    VERY_LOW = 1
    LOW = 2
    MEDIUM = 3
    HIGH = 4
    VERY_HIGH = 5

class ConsensusMessageType(Enum):
    """Types of consensus messages"""
    # Raft messages
    REQUEST_VOTE = "request_vote"
    VOTE_RESPONSE = "vote_response"
    APPEND_ENTRIES = "append_entries"
    APPEND_RESPONSE = "append_response"
    HEARTBEAT = "heartbeat"
    
    # PoA messages
    AUTHORITY_ANNOUNCEMENT = "authority_announcement"
    TRUST_PROPOSAL = "trust_proposal"
    TRUST_VOTE = "trust_vote"
    MALICIOUS_NODE_REPORT = "malicious_node_report"
    
    # Trust evaluation messages
    TRUST_UPDATE = "trust_update"
    REPUTATION_QUERY = "reputation_query"
    REPUTATION_RESPONSE = "reputation_response"

@dataclass
class TrustMetrics:
    """Trust evaluation metrics for a node"""
    node_id: str
    message_authenticity: float = 0.0  # 0-1 scale
    behavior_consistency: float = 0.0   # 0-1 scale
    network_participation: float = 0.0  # 0-1 scale
    response_reliability: float = 0.0   # 0-1 scale
    location_verification: float = 0.0  # 0-1 scale
    timestamp: float = field(default_factory=time.time)
    
    def calculate_overall_trust(self) -> float:
        """Calculate overall trust score (0-1)"""
        weights = {
            'authenticity': 0.25,
            'consistency': 0.20,
            'participation': 0.20,
            'reliability': 0.20,
            'location': 0.15
        }
        
        return (
            self.message_authenticity * weights['authenticity'] +
            self.behavior_consistency * weights['consistency'] +
            self.network_participation * weights['participation'] +
            self.response_reliability * weights['reliability'] +
            self.location_verification * weights['location']
        )

@dataclass
class MaliciousActivity:
    """Record of malicious activity detection"""
    reporter_id: str
    target_id: str
    activity_type: str
    severity: float  # 0-1 scale
    evidence: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)
    verified: bool = False

@dataclass
class LogEntry:
    """Raft log entry"""
    term: int
    index: int
    command: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'term': self.term,
            'index': self.index,
            'command': self.command,
            'timestamp': self.timestamp
        }

@dataclass
class ConsensusMessage:
    """Base consensus message"""
    msg_type: ConsensusMessageType
    sender_id: str
    receiver_id: str
    term: int
    data: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)

class ConsensusAlgorithm(ABC):
    """Abstract base class for consensus algorithms"""
    
    @abstractmethod
    def process_message(self, message: ConsensusMessage) -> Optional[ConsensusMessage]:
        """Process incoming consensus message"""
        pass
    
    @abstractmethod
    def get_leader(self) -> Optional[str]:
        """Get current leader node ID"""
        pass
    
    @abstractmethod
    def is_leader(self, node_id: str) -> bool:
        """Check if node is current leader"""
        pass

class RaftConsensus(ConsensusAlgorithm):
    """Raft consensus algorithm implementation"""
    
    def __init__(self, node_id: str, cluster_nodes: List[str]):
        self.node_id = node_id
        self.cluster_nodes = set(cluster_nodes)
        self.state = NodeState.FOLLOWER
        
        # Raft state
        self.current_term = 0
        self.voted_for: Optional[str] = None
        self.log: List[LogEntry] = []
        self.commit_index = 0
        self.last_applied = 0
        
        # Leader state
        self.next_index: Dict[str, int] = {}
        self.match_index: Dict[str, int] = {}
        
        # Timing
        self.election_timeout = random.uniform(5.0, 10.0)  # seconds
        self.heartbeat_interval = 1.0  # seconds
        self.last_heartbeat = time.time()
        self.election_start_time = 0.0
        
        # Voting
        self.votes_received: Set[str] = set()
        
        logger.info(f"Raft node {node_id} initialized with {len(cluster_nodes)} cluster nodes")
    
    def process_message(self, message: ConsensusMessage) -> Optional[ConsensusMessage]:
        """Process incoming Raft message"""
        if message.msg_type == ConsensusMessageType.REQUEST_VOTE:
            return self._handle_vote_request(message)
        elif message.msg_type == ConsensusMessageType.VOTE_RESPONSE:
            return self._handle_vote_response(message)
        elif message.msg_type == ConsensusMessageType.APPEND_ENTRIES:
            return self._handle_append_entries(message)
        elif message.msg_type == ConsensusMessageType.HEARTBEAT:
            return self._handle_heartbeat(message)
        
        return None
    
    def _handle_vote_request(self, message: ConsensusMessage) -> Optional[ConsensusMessage]:
        """Handle vote request from candidate"""
        candidate_id = message.sender_id
        candidate_term = message.term
        last_log_index = message.data.get('last_log_index', -1)
        last_log_term = message.data.get('last_log_term', 0)
        
        # Update term if candidate's term is higher
        if candidate_term > self.current_term:
            self.current_term = candidate_term
            self.voted_for = None
            self.state = NodeState.FOLLOWER
        
        # Vote for candidate if eligible
        vote_granted = False
        if (candidate_term == self.current_term and 
            (self.voted_for is None or self.voted_for == candidate_id) and
            self._is_log_up_to_date(last_log_index, last_log_term)):
            
            vote_granted = True
            self.voted_for = candidate_id
            self.last_heartbeat = time.time()
        
        return ConsensusMessage(
            msg_type=ConsensusMessageType.VOTE_RESPONSE,
            sender_id=self.node_id,
            receiver_id=candidate_id,
            term=self.current_term,
            data={'vote_granted': vote_granted}
        )
    
    def _handle_vote_response(self, message: ConsensusMessage) -> Optional[ConsensusMessage]:
        """Handle vote response from follower"""
        if self.state != NodeState.CANDIDATE or message.term != self.current_term:
            return None
        
        if message.data.get('vote_granted', False):
            self.votes_received.add(message.sender_id)
            
            # Check if we have majority
            if len(self.votes_received) > len(self.cluster_nodes) // 2:
                self._become_leader()
        
        return None
    
    def _handle_append_entries(self, message: ConsensusMessage) -> Optional[ConsensusMessage]:
        """Handle append entries from leader"""
        leader_id = message.sender_id
        leader_term = message.term
        prev_log_index = message.data.get('prev_log_index', -1)
        prev_log_term = message.data.get('prev_log_term', 0)
        entries = message.data.get('entries', [])
        leader_commit = message.data.get('leader_commit', 0)
        
        success = False
        
        # Update term and become follower if leader's term is higher
        if leader_term >= self.current_term:
            self.current_term = leader_term
            self.state = NodeState.FOLLOWER
            self.voted_for = None
            self.last_heartbeat = time.time()
            
            # Check log consistency
            if self._check_log_consistency(prev_log_index, prev_log_term):
                # Append new entries
                if entries:
                    self._append_entries(prev_log_index + 1, entries)
                
                # Update commit index
                if leader_commit > self.commit_index:
                    self.commit_index = min(leader_commit, len(self.log) - 1)
                
                success = True
        
        return ConsensusMessage(
            msg_type=ConsensusMessageType.APPEND_RESPONSE,
            sender_id=self.node_id,
            receiver_id=leader_id,
            term=self.current_term,
            data={
                'success': success,
                'match_index': len(self.log) - 1 if success else -1
            }
        )
    
    def _handle_heartbeat(self, message: ConsensusMessage) -> None:
        """Handle heartbeat from leader"""
        if message.term >= self.current_term:
            self.current_term = message.term
            self.state = NodeState.FOLLOWER
            self.last_heartbeat = time.time()
    
    def start_election(self) -> List[ConsensusMessage]:
        """Start leader election"""
        self.state = NodeState.CANDIDATE
        self.current_term += 1
        self.voted_for = self.node_id
        self.votes_received = {self.node_id}
        self.election_start_time = time.time()
        
        last_log_index = len(self.log) - 1
        last_log_term = self.log[-1].term if self.log else 0
        
        vote_requests = []
        for node_id in self.cluster_nodes:
            if node_id != self.node_id:
                vote_requests.append(ConsensusMessage(
                    msg_type=ConsensusMessageType.REQUEST_VOTE,
                    sender_id=self.node_id,
                    receiver_id=node_id,
                    term=self.current_term,
                    data={
                        'last_log_index': last_log_index,
                        'last_log_term': last_log_term
                    }
                ))
        
        logger.info(f"Node {self.node_id} started election for term {self.current_term}")
        return vote_requests
    
    def _become_leader(self):
        """Transition to leader state"""
        self.state = NodeState.LEADER
        
        # Initialize leader state
        for node_id in self.cluster_nodes:
            if node_id != self.node_id:
                self.next_index[node_id] = len(self.log)
                self.match_index[node_id] = 0
        
        logger.info(f"Node {self.node_id} became leader for term {self.current_term}")
    
    def get_leader(self) -> Optional[str]:
        """Get current leader node ID"""
        if self.state == NodeState.LEADER:
            return self.node_id
        return None
    
    def is_leader(self, node_id: str) -> bool:
        """Check if node is current leader"""
        return self.state == NodeState.LEADER and node_id == self.node_id
    
    def should_start_election(self) -> bool:
        """Check if election timeout has occurred"""
        return (self.state == NodeState.FOLLOWER and 
                time.time() - self.last_heartbeat > self.election_timeout)
    
    def _is_log_up_to_date(self, last_log_index: int, last_log_term: int) -> bool:
        """Check if candidate's log is at least as up-to-date as receiver's log"""
        if not self.log:
            return True
        
        my_last_term = self.log[-1].term
        my_last_index = len(self.log) - 1
        
        return (last_log_term > my_last_term or 
                (last_log_term == my_last_term and last_log_index >= my_last_index))
    
    def _check_log_consistency(self, prev_log_index: int, prev_log_term: int) -> bool:
        """Check log consistency for append entries"""
        if prev_log_index == -1:
            return True
        
        if prev_log_index >= len(self.log):
            return False
        
        return self.log[prev_log_index].term == prev_log_term
    
    def _append_entries(self, start_index: int, entries: List[Dict[str, Any]]):
        """Append entries to log"""
        # Remove conflicting entries
        if start_index < len(self.log):
            self.log = self.log[:start_index]
        
        # Append new entries
        for entry_data in entries:
            entry = LogEntry(
                term=entry_data['term'],
                index=entry_data['index'],
                command=entry_data['command']
            )
            self.log.append(entry)

class PoAConsensus(ConsensusAlgorithm):
    """Proof of Authority consensus algorithm implementation"""
    
    def __init__(self, node_id: str, initial_authorities: List[str]):
        self.node_id = node_id
        self.authorities: Set[str] = set(initial_authorities)
        self.authority_scores: Dict[str, float] = {}
        self.current_leader: Optional[str] = None
        self.leader_rotation_interval = 30.0  # seconds
        self.last_leader_change = time.time()
        
        # Initialize authority scores
        for auth_id in self.authorities:
            self.authority_scores[auth_id] = 1.0
        
        # Trust evaluation state
        self.trust_proposals: Dict[str, Dict] = {}
        self.trust_votes: Dict[str, Dict[str, bool]] = {}
        
        logger.info(f"PoA node {node_id} initialized with {len(initial_authorities)} authorities")
    
    def process_message(self, message: ConsensusMessage) -> Optional[ConsensusMessage]:
        """Process incoming PoA message"""
        if message.msg_type == ConsensusMessageType.AUTHORITY_ANNOUNCEMENT:
            return self._handle_authority_announcement(message)
        elif message.msg_type == ConsensusMessageType.TRUST_PROPOSAL:
            return self._handle_trust_proposal(message)
        elif message.msg_type == ConsensusMessageType.TRUST_VOTE:
            return self._handle_trust_vote(message)
        elif message.msg_type == ConsensusMessageType.MALICIOUS_NODE_REPORT:
            return self._handle_malicious_report(message)
        
        return None
    
    def _handle_authority_announcement(self, message: ConsensusMessage) -> Optional[ConsensusMessage]:
        """Handle authority announcement"""
        authority_id = message.sender_id
        authority_score = message.data.get('authority_score', 0.0)
        
        if authority_id in self.authorities:
            self.authority_scores[authority_id] = authority_score
            logger.debug(f"Updated authority score for {authority_id}: {authority_score}")
        
        return None
    
    def _handle_trust_proposal(self, message: ConsensusMessage) -> Optional[ConsensusMessage]:
        """Handle trust evaluation proposal"""
        proposal_id = message.data.get('proposal_id')
        target_node = message.data.get('target_node')
        trust_metrics = message.data.get('trust_metrics')
        
        if proposal_id and target_node and trust_metrics:
            self.trust_proposals[proposal_id] = {
                'target_node': target_node,
                'trust_metrics': trust_metrics,
                'proposer': message.sender_id,
                'timestamp': time.time()
            }
            
            # Vote on proposal if we're an authority
            if self.node_id in self.authorities:
                vote = self._evaluate_trust_proposal(trust_metrics)
                return ConsensusMessage(
                    msg_type=ConsensusMessageType.TRUST_VOTE,
                    sender_id=self.node_id,
                    receiver_id=message.sender_id,
                    term=0,
                    data={
                        'proposal_id': proposal_id,
                        'vote': vote,
                        'authority_score': self.authority_scores.get(self.node_id, 0.0)
                    }
                )
        
        return None
    
    def _handle_trust_vote(self, message: ConsensusMessage) -> None:
        """Handle trust vote from authority"""
        proposal_id = message.data.get('proposal_id')
        vote = message.data.get('vote')
        authority_score = message.data.get('authority_score', 0.0)
        
        if proposal_id and vote is not None:
            if proposal_id not in self.trust_votes:
                self.trust_votes[proposal_id] = {}
            
            self.trust_votes[proposal_id][message.sender_id] = {
                'vote': vote,
                'authority_score': authority_score,
                'timestamp': time.time()
            }
    
    def _handle_malicious_report(self, message: ConsensusMessage) -> Optional[ConsensusMessage]:
        """Handle malicious node report"""
        target_node = message.data.get('target_node')
        activity_type = message.data.get('activity_type')
        evidence = message.data.get('evidence', {})
        severity = message.data.get('severity', 0.0)
        
        # Process malicious activity report
        if target_node and activity_type:
            logger.warning(f"Malicious activity reported: {target_node} - {activity_type} (severity: {severity})")
            
            # If we're an authority, investigate the report
            if self.node_id in self.authorities:
                self._investigate_malicious_report(target_node, activity_type, evidence, severity)
        
        return None
    
    def select_leader(self) -> str:
        """Select leader based on authority scores"""
        if not self.authorities:
            return self.node_id
        
        # Check if it's time for leader rotation
        if (self.current_leader and 
            time.time() - self.last_leader_change < self.leader_rotation_interval):
            return self.current_leader
        
        # Select authority with highest score
        best_authority = max(self.authorities, 
                           key=lambda x: self.authority_scores.get(x, 0.0))
        
        if best_authority != self.current_leader:
            self.current_leader = best_authority
            self.last_leader_change = time.time()
            logger.info(f"New PoA leader selected: {best_authority}")
        
        return self.current_leader
    
    def get_leader(self) -> Optional[str]:
        """Get current leader node ID"""
        return self.select_leader()
    
    def is_leader(self, node_id: str) -> bool:
        """Check if node is current leader"""
        return self.get_leader() == node_id
    
    def add_authority(self, node_id: str, initial_score: float = 0.5):
        """Add new authority node"""
        self.authorities.add(node_id)
        self.authority_scores[node_id] = initial_score
        logger.info(f"Added authority node: {node_id}")
    
    def remove_authority(self, node_id: str):
        """Remove authority node"""
        self.authorities.discard(node_id)
        self.authority_scores.pop(node_id, None)
        
        if self.current_leader == node_id:
            self.current_leader = None
        
        logger.info(f"Removed authority node: {node_id}")
    
    def update_authority_score(self, node_id: str, score: float):
        """Update authority score for node"""
        if node_id in self.authorities:
            self.authority_scores[node_id] = max(0.0, min(1.0, score))
    
    def _evaluate_trust_proposal(self, trust_metrics: Dict[str, float]) -> bool:
        """Evaluate trust proposal and return vote"""
        overall_trust = 0.0
        total_weight = 0.0
        
        weights = {
            'message_authenticity': 0.25,
            'behavior_consistency': 0.20,
            'network_participation': 0.20,
            'response_reliability': 0.20,
            'location_verification': 0.15
        }
        
        for metric, value in trust_metrics.items():
            if metric in weights:
                overall_trust += value * weights[metric]
                total_weight += weights[metric]
        
        if total_weight > 0:
            overall_trust /= total_weight
        
        # Vote based on trust threshold
        return overall_trust >= 0.6
    
    def _investigate_malicious_report(self, target_node: str, activity_type: str, 
                                    evidence: Dict[str, Any], severity: float):
        """Investigate malicious node report"""
        # Implement investigation logic based on evidence
        # This is a placeholder for more sophisticated analysis
        
        investigation_score = 0.0
        
        # Analyze evidence
        if 'message_inconsistencies' in evidence:
            investigation_score += 0.3 * min(evidence['message_inconsistencies'], 1.0)
        
        if 'location_spoofing' in evidence:
            investigation_score += 0.4 * min(evidence['location_spoofing'], 1.0)
        
        if 'timing_attacks' in evidence:
            investigation_score += 0.3 * min(evidence['timing_attacks'], 1.0)
        
        # If investigation score is high, consider node malicious
        if investigation_score >= 0.7:
            logger.warning(f"Node {target_node} confirmed as malicious (score: {investigation_score})")
            # Additional actions could be taken here (e.g., blacklisting)

class TrustEvaluationEngine:
    """Trust evaluation and malicious node detection engine"""
    
    def __init__(self, node_id: str):
        self.node_id = node_id
        self.trust_scores: Dict[str, TrustMetrics] = {}
        self.malicious_reports: List[MaliciousActivity] = []
        self.trust_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        
        # Thresholds
        self.malicious_threshold = 0.3
        self.trusted_threshold = 0.7
        self.report_confidence_threshold = 0.8
        
        logger.info(f"Trust evaluation engine initialized for node {node_id}")
    
    def evaluate_node_trust(self, node_id: str, metrics: TrustMetrics) -> float:
        """Evaluate trust score for a node"""
        self.trust_scores[node_id] = metrics
        overall_trust = metrics.calculate_overall_trust()
        
        # Update trust history
        self.trust_history[node_id].append({
            'trust_score': overall_trust,
            'timestamp': time.time()
        })
        
        return overall_trust
    
    def detect_malicious_behavior(self, node_id: str, behavior_data: Dict[str, Any]) -> Optional[MaliciousActivity]:
        """Detect malicious behavior based on node activity"""
        malicious_indicators = []
        
        # Check for location spoofing
        if self._detect_location_spoofing(node_id, behavior_data):
            malicious_indicators.append(('location_spoofing', 0.8))
        
        # Check for message tampering
        if self._detect_message_tampering(behavior_data):
            malicious_indicators.append(('message_tampering', 0.9))
        
        # Check for timing attacks
        if self._detect_timing_attacks(behavior_data):
            malicious_indicators.append(('timing_attack', 0.7))
        
        # Check for inconsistent behavior
        if self._detect_inconsistent_behavior(node_id, behavior_data):
            malicious_indicators.append(('inconsistent_behavior', 0.6))
        
        # Calculate overall malicious score
        if malicious_indicators:
            total_severity = sum(severity for _, severity in malicious_indicators)
            avg_severity = total_severity / len(malicious_indicators)
            
            if avg_severity >= self.report_confidence_threshold:
                activity = MaliciousActivity(
                    reporter_id=self.node_id,
                    target_id=node_id,
                    activity_type=', '.join(activity for activity, _ in malicious_indicators),
                    severity=avg_severity,
                    evidence={
                        'indicators': malicious_indicators,
                        'behavior_data': behavior_data
                    }
                )
                
                self.malicious_reports.append(activity)
                logger.warning(f"Malicious behavior detected: {node_id} - {activity.activity_type}")
                return activity
        
        return None
    
    def get_trust_level(self, node_id: str) -> TrustLevel:
        """Get trust level for a node"""
        if node_id not in self.trust_scores:
            return TrustLevel.UNKNOWN
        
        trust_score = self.trust_scores[node_id].calculate_overall_trust()
        
        if trust_score >= 0.9:
            return TrustLevel.VERY_HIGH
        elif trust_score >= 0.7:
            return TrustLevel.HIGH
        elif trust_score >= 0.5:
            return TrustLevel.MEDIUM
        elif trust_score >= 0.3:
            return TrustLevel.LOW
        else:
            return TrustLevel.VERY_LOW
    
    def is_node_trusted(self, node_id: str) -> bool:
        """Check if node is considered trusted"""
        if node_id not in self.trust_scores:
            return False
        
        trust_score = self.trust_scores[node_id].calculate_overall_trust()
        return trust_score >= self.trusted_threshold
    
    def is_node_malicious(self, node_id: str) -> bool:
        """Check if node is considered malicious"""
        if node_id not in self.trust_scores:
            return False
        
        trust_score = self.trust_scores[node_id].calculate_overall_trust()
        return trust_score <= self.malicious_threshold
    
    def _detect_location_spoofing(self, node_id: str, behavior_data: Dict[str, Any]) -> bool:
        """Detect location spoofing attacks"""
        # Check for impossible location changes
        current_location = behavior_data.get('location')
        previous_location = behavior_data.get('previous_location')
        time_diff = behavior_data.get('time_diff', 0)
        max_speed = behavior_data.get('max_reasonable_speed', 200)  # km/h
        
        if current_location and previous_location and time_diff > 0:
            # Calculate distance and speed
            distance = self._calculate_distance(current_location, previous_location)
            speed_kmh = (distance / 1000) / (time_diff / 3600)  # km/h
            
            if speed_kmh > max_speed:
                logger.warning(f"Impossible speed detected for {node_id}: {speed_kmh} km/h")
                return True
        
        return False
    
    def _detect_message_tampering(self, behavior_data: Dict[str, Any]) -> bool:
        """Detect message tampering"""
        # Check for message integrity violations
        message_integrity = behavior_data.get('message_integrity', 1.0)
        integrity_threshold = 0.95
        
        return message_integrity < integrity_threshold
    
    def _detect_timing_attacks(self, behavior_data: Dict[str, Any]) -> bool:
        """Detect timing-based attacks"""
        # Check for suspicious timing patterns
        response_times = behavior_data.get('response_times', [])
        
        if len(response_times) >= 5:
            avg_response_time = sum(response_times) / len(response_times)
            
            # Look for extremely fast responses (possible replay attack)
            fast_responses = [t for t in response_times if t < 0.01]  # < 10ms
            
            if len(fast_responses) / len(response_times) > 0.8:
                return True
        
        return False
    
    def _detect_inconsistent_behavior(self, node_id: str, behavior_data: Dict[str, Any]) -> bool:
        """Detect inconsistent behavior patterns"""
        # Check historical behavior consistency
        if node_id not in self.trust_history:
            return False
        
        history = list(self.trust_history[node_id])
        if len(history) < 5:
            return False
        
        # Check for sudden trust score drops
        recent_scores = [entry['trust_score'] for entry in history[-5:]]
        score_variance = sum((score - sum(recent_scores) / len(recent_scores)) ** 2 
                           for score in recent_scores) / len(recent_scores)
        
        return score_variance > 0.1  # High variance indicates inconsistency
    
    def _calculate_distance(self, loc1: Tuple[float, float], loc2: Tuple[float, float]) -> float:
        """Calculate distance between two locations in meters"""
        # Simple Euclidean distance (for demonstration)
        # In practice, use haversine formula for GPS coordinates
        dx = loc1[0] - loc2[0]
        dy = loc1[1] - loc2[1]
        return (dx ** 2 + dy ** 2) ** 0.5

class ConsensusEngine:
    """Main consensus engine coordinating Raft and PoA algorithms"""
    
    def __init__(self, node_id: str, consensus_type: str = "hybrid"):
        self.node_id = node_id
        self.consensus_type = consensus_type
        
        # Consensus algorithms
        self.raft: Optional[RaftConsensus] = None
        self.poa: Optional[PoAConsensus] = None
        
        # Trust evaluation
        self.trust_engine = TrustEvaluationEngine(node_id)
        
        # Message queues
        self.outbound_messages: deque = deque()
        self.inbound_messages: deque = deque()
        
        # State
        self.is_running = False
        self.message_handlers: Dict[ConsensusMessageType, Callable] = {}
        
        logger.info(f"Consensus engine initialized for node {node_id} with type {consensus_type}")
    
    def initialize_raft(self, cluster_nodes: List[str]):
        """Initialize Raft consensus"""
        self.raft = RaftConsensus(self.node_id, cluster_nodes)
        logger.info(f"Raft consensus initialized with {len(cluster_nodes)} nodes")
    
    def initialize_poa(self, authorities: List[str]):
        """Initialize PoA consensus"""
        self.poa = PoAConsensus(self.node_id, authorities)
        logger.info(f"PoA consensus initialized with {len(authorities)} authorities")
    
    def start(self):
        """Start consensus engine"""
        self.is_running = True
        logger.info(f"Consensus engine started for node {self.node_id}")
    
    def stop(self):
        """Stop consensus engine"""
        self.is_running = False
        logger.info(f"Consensus engine stopped for node {self.node_id}")
    
    def process_message(self, message: ConsensusMessage) -> Optional[ConsensusMessage]:
        """Process incoming consensus message"""
        if not self.is_running:
            return None
        
        response = None
        
        # Route message to appropriate consensus algorithm
        if message.msg_type in [ConsensusMessageType.REQUEST_VOTE, 
                               ConsensusMessageType.VOTE_RESPONSE,
                               ConsensusMessageType.APPEND_ENTRIES,
                               ConsensusMessageType.HEARTBEAT]:
            if self.raft:
                response = self.raft.process_message(message)
        
        elif message.msg_type in [ConsensusMessageType.AUTHORITY_ANNOUNCEMENT,
                                 ConsensusMessageType.TRUST_PROPOSAL,
                                 ConsensusMessageType.TRUST_VOTE,
                                 ConsensusMessageType.MALICIOUS_NODE_REPORT]:
            if self.poa:
                response = self.poa.process_message(message)
        
        return response
    
    def get_current_leader(self) -> Optional[str]:
        """Get current consensus leader"""
        if self.consensus_type == "raft" and self.raft:
            return self.raft.get_leader()
        elif self.consensus_type == "poa" and self.poa:
            return self.poa.get_leader()
        elif self.consensus_type == "hybrid":
            # In hybrid mode, prefer PoA leader for trust decisions
            if self.poa:
                return self.poa.get_leader()
            elif self.raft:
                return self.raft.get_leader()
        
        return None
    
    def is_leader(self) -> bool:
        """Check if this node is the current leader"""
        current_leader = self.get_current_leader()
        return current_leader == self.node_id
    
    def evaluate_node_trust(self, node_id: str, metrics: TrustMetrics) -> float:
        """Evaluate trust for a node"""
        return self.trust_engine.evaluate_node_trust(node_id, metrics)
    
    def report_malicious_activity(self, target_node: str, activity_type: str, 
                                 evidence: Dict[str, Any], severity: float) -> ConsensusMessage:
        """Report malicious activity"""
        return ConsensusMessage(
            msg_type=ConsensusMessageType.MALICIOUS_NODE_REPORT,
            sender_id=self.node_id,
            receiver_id="broadcast",  # Broadcast to all authorities
            term=0,
            data={
                'target_node': target_node,
                'activity_type': activity_type,
                'evidence': evidence,
                'severity': severity
            }
        )
    
    def propose_trust_update(self, target_node: str, trust_metrics: Dict[str, float]) -> ConsensusMessage:
        """Propose trust score update"""
        proposal_id = hashlib.sha256(
            f"{self.node_id}_{target_node}_{time.time()}".encode()
        ).hexdigest()[:16]
        
        return ConsensusMessage(
            msg_type=ConsensusMessageType.TRUST_PROPOSAL,
            sender_id=self.node_id,
            receiver_id="broadcast",
            term=0,
            data={
                'proposal_id': proposal_id,
                'target_node': target_node,
                'trust_metrics': trust_metrics
            }
        )
    
    def get_trust_level(self, node_id: str) -> TrustLevel:
        """Get trust level for a node"""
        return self.trust_engine.get_trust_level(node_id)
    
    def is_node_trusted(self, node_id: str) -> bool:
        """Check if node is trusted"""
        return self.trust_engine.is_node_trusted(node_id)
    
    def is_node_malicious(self, node_id: str) -> bool:
        """Check if node is malicious"""
        return self.trust_engine.is_node_malicious(node_id)
    
    def get_consensus_statistics(self) -> Dict[str, Any]:
        """Get consensus engine statistics"""
        stats = {
            'node_id': self.node_id,
            'consensus_type': self.consensus_type,
            'is_leader': self.is_leader(),
            'current_leader': self.get_current_leader(),
            'trust_evaluations': len(self.trust_engine.trust_scores),
            'malicious_reports': len(self.trust_engine.malicious_reports)
        }
        
        if self.raft:
            stats['raft'] = {
                'state': self.raft.state.value,
                'current_term': self.raft.current_term,
                'log_length': len(self.raft.log),
                'cluster_size': len(self.raft.cluster_nodes)
            }
        
        if self.poa:
            stats['poa'] = {
                'authorities': len(self.poa.authorities),
                'authority_scores': dict(self.poa.authority_scores),
                'current_leader': self.poa.current_leader
            }
        
        return stats