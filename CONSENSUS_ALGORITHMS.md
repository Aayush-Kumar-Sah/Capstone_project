# VANET Consensus Algorithms: Raft and Proof of Authority (PoA)

## Overview

This document describes the implementation of consensus algorithms for trust evaluation and malicious node detection in Vehicular Ad-hoc Networks (VANETs). The system implements both **Raft** and **Proof of Authority (PoA)** consensus mechanisms to ensure distributed trust management and network security.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Raft Consensus Algorithm](#raft-consensus-algorithm)
3. [Proof of Authority (PoA)](#proof-of-authority-poa)
4. [Trust Evaluation System](#trust-evaluation-system)
5. [Malicious Node Detection](#malicious-node-detection)
6. [Integration with VANET Application](#integration-with-vanet-application)
7. [Usage Examples](#usage-examples)
8. [Performance Considerations](#performance-considerations)
9. [Security Features](#security-features)

## Architecture Overview

The consensus system consists of several key components:

```
┌─────────────────────────────────────────────────────────────┐
│                     VANET Application                       │
├─────────────────────────────────────────────────────────────┤
│                   Consensus Engine                          │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │  Raft Consensus │  │  PoA Consensus  │  │ Trust Engine │ │
│  │                 │  │                 │  │              │ │
│  │ • Leader Election│  │ • Authority     │  │ • Trust      │ │
│  │ • Log Replication│  │   Management    │  │   Evaluation │ │
│  │ • Fault Tolerance│  │ • Dynamic Leader│  │ • Malicious  │ │
│  │                 │  │   Selection     │  │   Detection  │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Key Features

- **Hybrid Consensus**: Combines Raft and PoA for optimal performance
- **Trust Evaluation**: Multi-metric trust scoring system
- **Malicious Detection**: Real-time identification of malicious behavior
- **Dynamic Leadership**: Adaptive leader selection based on network conditions
- **Fault Tolerance**: Automatic recovery from node failures

## Raft Consensus Algorithm

### Overview

Raft is a consensus algorithm designed for managing a replicated log in distributed systems. In our VANET implementation, Raft is used for:

- **Leader Election**: Selecting cluster heads for coordination
- **Log Replication**: Ensuring consistent state across nodes
- **Fault Tolerance**: Handling node failures and network partitions

### Key Components

#### 1. Node States

```python
class NodeState(Enum):
    FOLLOWER = "follower"      # Default state, follows leader
    CANDIDATE = "candidate"    # Campaigning for leadership
    LEADER = "leader"         # Coordinates cluster operations
    OBSERVER = "observer"     # For PoA authorities
```

#### 2. Message Types

- **REQUEST_VOTE**: Election campaign messages
- **VOTE_RESPONSE**: Voting responses from followers
- **APPEND_ENTRIES**: Log replication from leader
- **HEARTBEAT**: Leader presence notifications

#### 3. Election Process

```python
def start_election(self):
    """Start leader election process"""
    self.state = NodeState.CANDIDATE
    self.current_term += 1
    self.voted_for = self.node_id
    self.votes_received = {self.node_id}
    
    # Send vote requests to all cluster nodes
    for node_id in self.cluster_nodes:
        if node_id != self.node_id:
            self.send_vote_request(node_id)
```

### Use Cases in VANET

1. **Cluster Head Election**: Select optimal cluster heads
2. **Emergency Coordination**: Ensure consistent emergency response
3. **Resource Allocation**: Coordinate bandwidth and channel usage

## Proof of Authority (PoA)

### Overview

PoA is a consensus mechanism where pre-approved authorities validate transactions and maintain network integrity. In VANET context:

- **Authority Nodes**: Trusted vehicles (police, emergency services)
- **Trust Validation**: Authorities vote on node trustworthiness
- **Leader Rotation**: Dynamic authority-based leadership

### Authority Management

#### 1. Authority Selection Criteria

```python
def calculate_authority_score(self, node_id: str) -> float:
    """Calculate authority score based on multiple factors"""
    factors = {
        'connectivity': 0.25,      # Network connections
        'stability': 0.25,         # Historical reliability
        'trust_score': 0.20,       # Current trust level
        'resource_capacity': 0.15,  # Processing/bandwidth
        'reputation': 0.15         # Community reputation
    }
    return weighted_score
```

#### 2. Dynamic Leader Selection

```python
def select_leader(self) -> str:
    """Select leader based on authority scores"""
    if self.authorities:
        return max(self.authorities, 
                  key=lambda x: self.authority_scores.get(x, 0.0))
    return self.node_id
```

### Trust Proposals and Voting

Authorities collaborate to evaluate node trustworthiness:

1. **Trust Proposal**: Node behavior assessment submitted
2. **Authority Voting**: Each authority votes on the proposal
3. **Consensus Decision**: Majority vote determines trust level

## Trust Evaluation System

### Trust Metrics

The system evaluates trust based on five key metrics:

```python
@dataclass
class TrustMetrics:
    message_authenticity: float    # Message integrity (0-1)
    behavior_consistency: float    # Behavioral patterns (0-1)
    network_participation: float   # Network activity level (0-1)
    response_reliability: float    # Response timing/accuracy (0-1)
    location_verification: float   # Location consistency (0-1)
```

### Trust Calculation

```python
def calculate_overall_trust(self) -> float:
    """Calculate weighted trust score"""
    weights = {
        'authenticity': 0.25,
        'consistency': 0.20,
        'participation': 0.20,
        'reliability': 0.20,
        'location': 0.15
    }
    
    return sum(getattr(self, metric) * weight 
              for metric, weight in weights.items())
```

### Trust Levels

| Trust Score | Level | Description | Actions |
|-------------|-------|-------------|---------|
| 0.9 - 1.0 | VERY_HIGH | Highly trusted | Full network access |
| 0.7 - 0.9 | HIGH | Trusted | Normal operations |
| 0.5 - 0.7 | MEDIUM | Moderate trust | Limited privileges |
| 0.3 - 0.5 | LOW | Low trust | Restricted access |
| 0.0 - 0.3 | VERY_LOW | Untrusted | Potential isolation |

## Malicious Node Detection

### Detection Algorithms

#### 1. Location Spoofing Detection

```python
def _detect_location_spoofing(self, node_id: str, behavior_data: Dict) -> bool:
    """Detect impossible location changes"""
    current_location = behavior_data.get('location')
    previous_location = behavior_data.get('previous_location')
    time_diff = behavior_data.get('time_diff', 0)
    max_speed = behavior_data.get('max_reasonable_speed', 200)  # km/h
    
    if current_location and previous_location and time_diff > 0:
        distance = calculate_distance(current_location, previous_location)
        speed_kmh = (distance / 1000) / (time_diff / 3600)
        
        return speed_kmh > max_speed
    return False
```

#### 2. Message Tampering Detection

```python
def _detect_message_tampering(self, behavior_data: Dict) -> bool:
    """Detect message integrity violations"""
    message_integrity = behavior_data.get('message_integrity', 1.0)
    return message_integrity < 0.95  # Threshold
```

#### 3. Timing Attack Detection

```python
def _detect_timing_attacks(self, behavior_data: Dict) -> bool:
    """Detect suspicious timing patterns"""
    response_times = behavior_data.get('response_times', [])
    
    if len(response_times) >= 5:
        fast_responses = [t for t in response_times if t < 0.01]  # <10ms
        return len(fast_responses) / len(response_times) > 0.8
    return False
```

### Response to Malicious Behavior

1. **Immediate Actions**:
   - Reduce trust score
   - Restrict network access
   - Alert other nodes

2. **Cluster Impact**:
   - Emergency head election if malicious head detected
   - Cluster reorganization
   - Isolation of malicious nodes

3. **Network Protection**:
   - Broadcast warnings
   - Update blacklists
   - Consensus-based verification

## Integration with VANET Application

### Initialization

```python
# Initialize VANET application with consensus
app = CustomVANETApplication(ClusteringAlgorithm.MOBILITY_BASED)
app.initialize()

# Setup consensus with authorities
authority_nodes = ["police_001", "emergency_002", "traffic_003"]
app.initialize_consensus(
    node_id="vehicle_001",
    consensus_type="hybrid",
    authority_nodes=authority_nodes
)
```

### Trust Evaluation Integration

```python
# Evaluate node trust
trust_score = app.evaluate_node_trust("vehicle_002")

# Check if node is trusted
is_trusted = app.is_node_trusted("vehicle_002")

# Report malicious activity
app.report_malicious_activity(
    reporter_id="vehicle_001",
    target_id="suspicious_vehicle",
    activity_type="location_spoofing",
    evidence={'location_jump': 1000},  # meters
    severity=0.8
)
```

### Periodic Operations

The system automatically performs trust evaluations during simulation:

```python
def handle_timeStep(self, simulation_time: float):
    """Main simulation loop with trust evaluation"""
    # Regular VANET operations
    self._update_vehicle_states()
    self._process_message_queue()
    self._update_clustering()
    
    # Trust evaluation (every 10 seconds)
    if self.trust_enabled and self._should_update_trust():
        self.update_trust_scores()
```

## Usage Examples

### Basic Setup

```python
from src.custom_vanet_appl import CustomVANETApplication
from src.clustering import ClusteringAlgorithm

# Create VANET application
app = CustomVANETApplication(ClusteringAlgorithm.MOBILITY_BASED)
app.initialize()

# Initialize consensus system
app.initialize_consensus(
    node_id="main_node",
    consensus_type="hybrid",
    authority_nodes=["authority_1", "authority_2"]
)

# Add vehicles to network
app.add_vehicle("vehicle_001", 100.0, 200.0, 50.0, 45.0)
app.add_vehicle("vehicle_002", 150.0, 250.0, 60.0, 90.0)
```

### Trust Evaluation

```python
# Evaluate trust for a specific vehicle
trust_score = app.evaluate_node_trust("vehicle_001")
print(f"Trust score: {trust_score:.2f}")

# Get trust level
trust_level = app.consensus_engine.get_trust_level("vehicle_001")
print(f"Trust level: {trust_level}")

# Check if node should be trusted for sensitive operations
if app.is_node_trusted("vehicle_001"):
    print("Vehicle is trusted for sensitive operations")
```

### Malicious Node Handling

```python
# Simulate malicious behavior detection
behavior_data = {
    'location': (1000, 1000),
    'previous_location': (0, 0),
    'time_diff': 0.01,  # Impossible: 1000m in 10ms
    'max_reasonable_speed': 120,
    'message_integrity': 0.1
}

# Report malicious activity
success = app.report_malicious_activity(
    reporter_id="observer_vehicle",
    target_id="suspicious_vehicle",
    activity_type="location_spoofing_and_tampering",
    evidence=behavior_data,
    severity=0.95
)

if success:
    print("Malicious activity reported successfully")
```

### Statistics and Monitoring

```python
# Get comprehensive statistics
stats = app.get_application_statistics()
trust_stats = stats['trust_and_security']

print(f"Total nodes: {trust_stats['total_nodes']}")
print(f"Trusted nodes: {trust_stats['trusted_nodes']}")
print(f"Malicious nodes: {trust_stats['malicious_nodes']}")
print(f"Average trust: {trust_stats['average_trust_score']:.2f}")
print(f"Trust evaluations: {trust_stats['trust_evaluations']}")
```

## Performance Considerations

### Scalability

- **Node Limit**: Optimal performance with 50-100 nodes per consensus group
- **Authority Ratio**: 10-20% of nodes should be authorities
- **Update Frequency**: Trust evaluations every 10-30 seconds

### Network Overhead

| Operation | Message Overhead | Frequency |
|-----------|------------------|-----------|
| Trust Evaluation | 2-5 messages | Per evaluation |
| Malicious Report | 1 broadcast | Per incident |
| Consensus Vote | 1 per authority | Per proposal |
| Heartbeat | 1 per follower | Every 1-2s |

### Optimization Strategies

1. **Batch Processing**: Group multiple trust evaluations
2. **Selective Evaluation**: Focus on suspicious nodes
3. **Caching**: Cache trust scores for recently evaluated nodes
4. **Hierarchical Consensus**: Multi-level consensus for large networks

## Security Features

### Attack Resistance

1. **Sybil Attack Protection**:
   - Authority-based validation
   - Resource-based verification
   - Behavioral analysis

2. **Byzantine Fault Tolerance**:
   - Majority consensus required
   - Cross-validation of reports
   - Redundant authority nodes

3. **Privacy Protection**:
   - Anonymized reporting
   - Encrypted sensitive data
   - Minimal information disclosure

### Consensus Security

- **Election Security**: Cryptographic vote verification
- **Message Integrity**: Hash-based message authentication
- **Authority Validation**: Multi-factor authority verification
- **Network Isolation**: Automatic quarantine of malicious nodes

## Future Enhancements

1. **Machine Learning Integration**: AI-based behavior analysis
2. **Blockchain Integration**: Immutable trust records
3. **Cross-Network Consensus**: Inter-VANET trust propagation
4. **Real-time Adaptation**: Dynamic algorithm parameter adjustment
5. **Advanced Cryptography**: Post-quantum secure consensus

## Conclusion

The consensus-based trust evaluation system provides robust security and reliability for VANET applications. By combining Raft and PoA consensus mechanisms with comprehensive trust metrics and malicious node detection, the system ensures:

- **Network Integrity**: Reliable identification and isolation of malicious nodes
- **Distributed Trust**: Consensus-based trust evaluation without central authority
- **Fault Tolerance**: Resilience to node failures and network partitions
- **Scalability**: Efficient operation in dynamic vehicular environments

This implementation provides a solid foundation for secure, trustworthy vehicular communication networks.