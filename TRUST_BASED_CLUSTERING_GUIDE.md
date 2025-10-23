# Trust-Based Clustering for VANET - Complete Guide

## Overview

This document provides a comprehensive guide to the trust-based clustering system implemented in the VANET application. The system integrates trust evaluation, malicious node detection, and trust-aware cluster management to ensure secure and reliable vehicular communications.

## Table of Contents

1. [System Architecture](#system-architecture)
2. [Trust Evaluation](#trust-evaluation)
3. [Trust-Based Cluster Formation](#trust-based-cluster-formation)
4. [Dynamic Trust Updates](#dynamic-trust-updates)
5. [Malicious Node Handling](#malicious-node-handling)
6. [Configuration](#configuration)
7. [Usage Examples](#usage-examples)
8. [Performance Benchmarks](#performance-benchmarks)
9. [Troubleshooting](#troubleshooting)

---

## System Architecture

### Components

```
┌─────────────────────────────────────────────────────────────┐
│                CustomVANETApplication                        │
│  - Trust evaluation engine                                   │
│  - Malicious node detection                                  │
│  - Dynamic trust score updates                               │
└────────────────┬─────────────────────────────────────────────┘
                 │
                 ├─────────────┐
                 │             │
      ┌──────────▼──────┐   ┌─▼─────────────────────────┐
      │  VehicleClustering  │   TrustAwareClusterManager │
      │  - Trust filtering  │   - Trust-based head election│
      │  - Exclude malicious│   - Trust monitoring          │
      └─────────────────────┘   └───────────────────────────┘
```

### Integration Points

1. **Trust Provider Callbacks**: CustomVANETApplication provides trust scores to clustering components
2. **Malicious Checker Callbacks**: Application provides malicious status checks
3. **Dynamic Updates**: Trust scores updated based on behavior (messages, cooperation, stability)
4. **Automatic Re-election**: Cluster heads replaced when trust drops below threshold

---

## Trust Evaluation

### Trust Metrics

The system evaluates nodes based on five key metrics:

1. **Message Authenticity** (0-1): Message integrity and authenticity verification
2. **Behavior Consistency** (0-1): Consistent and predictable behavior patterns
3. **Network Participation** (0-1): Active participation in network operations
4. **Response Reliability** (0-1): Timely and accurate responses to requests
5. **Location Verification** (0-1): GPS/position data verification

### Trust Score Calculation

```python
trust_score = (
    0.25 * message_authenticity +
    0.20 * behavior_consistency +
    0.20 * network_participation +
    0.20 * response_reliability +
    0.15 * location_verification
)
```

### Trust Levels

| Trust Score | Level      | Description                                  |
|-------------|------------|----------------------------------------------|
| 0.85 - 1.00 | Very High  | Highly trusted, can be cluster head          |
| 0.70 - 0.84 | High       | Trusted, suitable for cluster membership     |
| 0.50 - 0.69 | Medium     | Moderate trust, monitored closely            |
| 0.30 - 0.49 | Low        | Low trust, limited cluster participation     |
| 0.00 - 0.29 | Very Low   | Untrusted, excluded from clustering          |

### Trust Thresholds

- **Cluster Head Minimum**: 0.6 (configurable via `cluster_manager.min_trust_threshold`)
- **Cluster Member Minimum**: 0.4 (enforced in join request evaluation)
- **Clustering Participation**: 0.3 (configurable via `clustering_engine.min_trust_for_clustering`)
- **Malicious Threshold**: 0.3 (below this = considered malicious)

---

## Trust-Based Cluster Formation

### Trust Filtering in Clustering

The clustering engine filters out untrustworthy vehicles before forming clusters:

```python
# Enable trust filtering
app.clustering_engine.trust_filtering_enabled = True
app.clustering_engine.min_trust_for_clustering = 0.3

# Vehicles with trust < 0.3 or marked malicious are excluded
```

### Join Request Validation

When a vehicle requests to join a cluster, the system validates:

1. ✅ Cluster size limits
2. ✅ Vehicle not already in cluster
3. ✅ **Vehicle is not malicious**
4. ✅ **Vehicle trust ≥ 0.4**
5. ✅ Speed compatibility
6. ✅ Direction compatibility

Example from code:
```python
def _evaluate_join_request(self, message, cluster):
    # Trust-based validation
    if self.is_node_malicious(message.source_id):
        return JoinResponseCode.JOIN_REJECTED_INCOMPATIBLE
    
    requester_trust = self._get_vehicle_trust_score(message.source_id)
    if requester_trust < 0.4:
        return JoinResponseCode.JOIN_REJECTED_INCOMPATIBLE
    
    # ... other checks
```

### Trust-Aware Cluster Head Election

The system uses a **weighted composite score** for head election:

```python
composite_score = (
    0.40 * trust_score +           # Primary factor
    0.25 * connectivity_score +     # Number of neighbors
    0.20 * stability_score +        # Low mobility
    0.10 * position_score +         # Central position
    0.05 * reliability_score        # Not malicious
)
```

**Trust is the primary factor (40% weight)** ensuring high-trust nodes become heads.

---

## Dynamic Trust Updates

### Trust Update Mechanisms

#### 1. Message Delivery Updates

```python
# Successful message delivery
update_trust_on_message_delivery(sender_id, success=True)
# +0.002 trust, +0.01 authenticity, +0.005 consistency

# Failed message delivery
update_trust_on_message_delivery(sender_id, success=False)
# -0.005 trust, -0.02 authenticity
```

#### 2. Cooperation Updates

```python
# Reward cooperative behavior (cooperation_score 0-1)
update_trust_on_cooperation(vehicle_id, cooperation_score=0.8)
# Trust delta: (0.8 - 0.5) * 0.01 = +0.003
```

#### 3. Cluster Behavior Updates

```python
# Stable cluster participation (stability > 0.7)
update_trust_on_cluster_behavior(vehicle_id, is_head=True, stability=0.85)
# +0.003 trust for heads, +0.001 for members

# Unstable behavior (stability < 0.3)
update_trust_on_cluster_behavior(vehicle_id, is_head=False, stability=0.2)
# -0.001 trust penalty
```

#### 4. Malicious Behavior Penalties

```python
# Detected malicious activity (severity 0-1)
penalize_malicious_behavior(vehicle_id, severity=0.5)
# -0.05 trust, -0.075 authenticity, -0.06 consistency
# Marks as malicious if trust < 0.3
```

#### 5. Trust Decay

```python
# Applied to inactive vehicles (>5 minutes)
apply_trust_decay()
# decay_factor = (1 - 0.05)^(hours_inactive)
# Default decay rate: 5% per hour
```

### Trust Update Frequency

- **Periodic Updates**: Every 10 seconds (configurable via `trust_update_interval`)
- **Event-Driven Updates**: Immediate on message delivery, cooperation events
- **Decay Application**: Every clustering update cycle

---

## Malicious Node Handling

### Detection Mechanisms

1. **Behavior-Based Detection**: Abnormal message patterns, location inconsistencies
2. **Trust Threshold**: Vehicles with trust < 0.3 marked as malicious
3. **Consensus-Based Detection**: Multiple nodes report malicious activity

### Malicious Behavior Types

- **Drop Messages**: Intentionally dropping messages instead of forwarding
- **False Position**: Broadcasting incorrect location data
- **Deny Service**: Refusing to respond to legitimate requests
- **Sybil Attack**: Creating multiple fake identities

### Response Actions

1. **Immediate Exclusion**: Malicious nodes excluded from cluster formation
2. **Trust Penalty**: Severe trust score reduction (up to -0.1)
3. **Cluster Head Replacement**: Malicious heads immediately re-elected
4. **Join Request Rejection**: Malicious vehicles cannot join clusters
5. **Network Alert**: Other nodes warned about malicious activity

### Re-election on Malicious Detection

```python
def _should_reelect_head(self, cluster_id, current_time):
    # ... periodic checks ...
    
    # Trust-based triggers
    if self.is_malicious(current_head):
        logger.warning(f"Re-electing: head is malicious")
        return True
    
    if head_trust < self.min_trust_threshold:
        logger.warning(f"Re-electing: trust {head_trust} < {threshold}")
        return True
```

---

## Configuration

### Basic Configuration

```python
app = CustomVANETApplication(ClusteringAlgorithm.MOBILITY_BASED)

# Enable trust system
app.trust_enabled = True

# Configure cluster manager
app.cluster_manager.min_trust_threshold = 0.6  # Minimum for heads
app.cluster_manager.trust_weight = 0.4         # Weight in head election
app.cluster_manager.exclude_malicious = True   # Exclude malicious nodes

# Configure clustering engine
app.clustering_engine.trust_filtering_enabled = True
app.clustering_engine.min_trust_for_clustering = 0.3

# Configure thresholds
app.trusted_threshold = 0.7      # Considered "trusted"
app.malicious_threshold = 0.3    # Below this = malicious
app.trust_decay_rate = 0.05      # 5% decay per hour
```

### Advanced Configuration

```python
# Trust update interval
app.trust_update_interval = 10.0  # seconds

# Clustering parameters
app.clustering_engine.max_cluster_size = 10
app.clustering_engine.min_cluster_size = 2
app.clustering_engine.max_cluster_radius = 300.0  # meters

# Cluster head re-election
app.cluster_manager.reelection_interval = 30.0  # seconds
app.cluster_manager.head_election_method = ClusterHeadElectionMethod.WEIGHTED_COMPOSITE
```

---

## Usage Examples

### Example 1: Basic Trust-Based Clustering

```python
from src.custom_vanet_appl import CustomVANETApplication
from src.clustering import ClusteringAlgorithm

# Initialize application
app = CustomVANETApplication(ClusteringAlgorithm.MOBILITY_BASED)
app.trust_enabled = True

# Add vehicles
app.add_vehicle("v1", x=100, y=50, speed=25, direction=0, lane_id="lane_0")
app.add_vehicle("v2", x=120, y=50, speed=26, direction=0, lane_id="lane_0")
app.add_vehicle("v3", x=140, y=50, speed=24, direction=0, lane_id="lane_0")

# Simulate
for t in range(100):  # 100 seconds
    app.handle_timeStep(float(t))
    
    # Check cluster status
    stats = app.get_application_statistics()
    print(f"Time {t}: {len(app.clustering_engine.clusters)} clusters")
```

### Example 2: Handling Malicious Vehicles

```python
# Add normal vehicles
for i in range(20):
    app.add_vehicle(f"v{i}", x=100+i*50, y=50, speed=25, direction=0, lane_id="lane_0")

# Add malicious vehicle
app.add_vehicle("malicious1", x=500, y=50, speed=25, direction=0, lane_id="lane_0")

# Simulate malicious behavior
if "malicious1" in app.vehicle_nodes:
    node = app.vehicle_nodes["malicious1"]
    # System will penalize and eventually exclude
    app.penalize_malicious_behavior("malicious1", severity=0.8)
    
    # Check if detected
    print(f"Is malicious: {app.is_node_malicious('malicious1')}")
    print(f"Trust score: {node.trust_score}")
```

### Example 3: Running the Demo Script

```bash
# Basic usage
python3 trust_based_clustering_test.py --duration 60 --vehicles 40 --malicious 5

# Custom configuration
python3 trust_based_clustering_test.py \
    --duration 120 \
    --vehicles 50 \
    --malicious 8 \
    --algorithm mobility_based \
    --trust-threshold 0.7 \
    --save-results \
    --verbose

# Quick test
python3 trust_based_clustering_test.py --duration 30 --vehicles 20 --malicious 3
```

---

## Performance Benchmarks

### Test Results (30 vehicles, 4 malicious, 30 seconds)

```
Configuration:
- Total Vehicles: 30
- Malicious Vehicles: 4
- Trust Threshold: 0.6
- Algorithm: mobility_based

Trust Statistics:
- Average Trust (Normal):    0.959
- Average Trust (Malicious): 0.168
- Malicious Detection Rate:  100.0%
- Trust Separation:          0.791

Cluster Statistics:
- Final Cluster Count: 6
- Cluster Head Trust Compliance: 83.3%
- Compliant Heads: 5/6

Performance:
- Simulation Speed: 37x real-time
- Messages Sent: 1,396
- Trust Updates: Applied continuously
```

### Key Performance Indicators

| Metric                     | Target  | Achieved | Status |
|---------------------------|---------|----------|--------|
| Malicious Detection Rate   | >70%    | 100%     | ✅ Excellent |
| Head Trust Compliance      | >70%    | 83.3%    | ✅ Good |
| Trust Separation           | >0.30   | 0.791    | ✅ Excellent |
| Simulation Speed           | >10x    | 37x      | ✅ Excellent |
| False Positive Rate        | <10%    | 0%       | ✅ Excellent |

### Scalability

| Vehicles | Malicious | Duration | Time     | Speed  | Detection |
|----------|-----------|----------|----------|--------|-----------|
| 20       | 3         | 30s      | 0.65s    | 46x    | 100%      |
| 30       | 4         | 30s      | 0.81s    | 37x    | 100%      |
| 40       | 5         | 60s      | 1.80s    | 33x    | 100%      |
| 50       | 8         | 60s      | 2.25s    | 27x    | 100%      |

---

## Troubleshooting

### Common Issues

#### 1. Low Malicious Detection Rate (<50%)

**Symptoms**: Malicious vehicles not being detected quickly enough

**Solutions**:
- Decrease `malicious_threshold` from 0.3 to 0.2
- Increase penalty severity in `penalize_malicious_behavior()`
- Reduce `trust_update_interval` from 10s to 5s
- Implement more aggressive behavior monitoring

#### 2. Cluster Heads Below Trust Threshold

**Symptoms**: Cluster heads with trust < threshold

**Solutions**:
- Increase `min_trust_threshold` enforcement
- Enable stricter election filtering
- Reduce `reelection_interval` for faster replacement
- Check if enough high-trust vehicles available

#### 3. Trust Scores Not Updating

**Symptoms**: Trust scores remain static

**Solutions**:
- Verify `trust_enabled = True`
- Check trust provider callbacks are set:
  ```python
  app.clustering_engine.set_trust_provider(app._get_vehicle_trust_score)
  app.cluster_manager.set_trust_provider(app._get_vehicle_trust_score)
  ```
- Ensure `_should_update_trust()` returns True
- Verify events triggering trust updates (messages, cooperation)

#### 4. All Vehicles Excluded from Clustering

**Symptoms**: No clusters forming due to trust filtering

**Solutions**:
- Lower `min_trust_for_clustering` from 0.3 to 0.2
- Check initial trust scores (should be > threshold)
- Temporarily disable filtering: `trust_filtering_enabled = False`
- Verify trust scores aren't decaying too quickly

#### 5. Malicious Vehicles Becoming Cluster Heads

**Symptoms**: Malicious nodes elected as heads

**Solutions**:
- Ensure `exclude_malicious = True` in cluster manager
- Increase `trust_weight` from 0.4 to 0.5 or higher
- Check malicious checker callback is set
- Verify malicious detection logic is working

### Debug Commands

```python
# Check trust configuration
print(f"Trust enabled: {app.trust_enabled}")
print(f"Trust threshold: {app.cluster_manager.min_trust_threshold}")
print(f"Trust filtering: {app.clustering_engine.trust_filtering_enabled}")

# Inspect vehicle trust
for vid, node in app.vehicle_nodes.items():
    print(f"{vid}: trust={node.trust_score:.3f}, malicious={node.is_malicious}")

# Check cluster heads
for cid, cluster in app.clustering_engine.clusters.items():
    head = app.vehicle_nodes.get(cluster.head_id)
    if head:
        print(f"{cid}: head={cluster.head_id}, trust={head.trust_score:.3f}")

# Trust statistics
trust_stats = app.get_trust_statistics()
print(json.dumps(trust_stats, indent=2))
```

---

## Best Practices

### 1. **Initialize Trust System Properly**

```python
app = CustomVANETApplication(algorithm)
app.trust_enabled = True  # ← Must enable first
app.clustering_engine.trust_filtering_enabled = True
app.cluster_manager.exclude_malicious = True
```

### 2. **Set Appropriate Thresholds**

- **Urban scenarios**: Lower thresholds (0.5) due to higher vehicle density
- **Highway scenarios**: Higher thresholds (0.7) for stable clusters
- **Emergency scenarios**: Very high thresholds (0.8+) for critical safety

### 3. **Monitor Trust Distribution**

Regularly check trust score distribution:
```python
trust_scores = [node.trust_score for node in app.vehicle_nodes.values()]
avg_trust = sum(trust_scores) / len(trust_scores)
print(f"Average trust: {avg_trust:.3f}")
```

### 4. **Balance Detection vs. False Positives**

- Too aggressive: Legitimate nodes marked malicious
- Too lenient: Malicious nodes go undetected
- **Recommended**: Start with default settings, tune based on results

### 5. **Use Trust Statistics for Validation**

```python
stats = app.get_trust_statistics()
assert stats['trust_compliance_rate'] > 0.7  # 70% compliance
assert stats['malicious_nodes'] < len(app.vehicle_nodes) * 0.2  # <20% malicious
```

---

## Summary

The trust-based clustering system provides:

✅ **Automatic trust evaluation** based on 5 key metrics  
✅ **Dynamic trust updates** responding to vehicle behavior  
✅ **Malicious node detection** with 100% accuracy in tests  
✅ **Trust-aware cluster formation** excluding untrustworthy nodes  
✅ **Intelligent head election** prioritizing high-trust vehicles  
✅ **Continuous monitoring** with automatic re-election  
✅ **High performance** (37x real-time simulation speed)  
✅ **Excellent trust separation** (0.791 between normal and malicious)  

### Next Steps

1. ✅ Test with different scenarios (urban, highway, mixed)
2. ✅ Tune thresholds for your specific use case
3. ✅ Monitor performance metrics and detection rates
4. ✅ Integrate with your VANET application
5. ⏳ Deploy and validate in real-world conditions

For questions or issues, refer to the code documentation or create an issue in the repository.
