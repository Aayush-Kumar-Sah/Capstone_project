# VANET Simulation System - Pseudocode Documentation

## Table of Contents
1. [Multi-Metric Raft-Based Leader Election](#1-multi-metric-raft-based-leader-election)
2. [Co-Leader Election and Automatic Succession](#2-co-leader-election-and-automatic-succession)
3. [Proof-of-Authority (PoA) Malicious Detection](#3-proof-of-authority-poa-malicious-detection)
4. [Relay Node Election (Multi-Hop Communication)](#4-relay-node-election-multi-hop-communication)
5. [Boundary Node Election (Inter-Cluster Communication)](#5-boundary-node-election-inter-cluster-communication)
6. [V2V Message Broadcasting with Multi-Hop](#6-v2v-message-broadcasting-with-multi-hop)
7. [Predictive Collision Detection](#7-predictive-collision-detection)
8. [Lane Change Safety Coordination](#8-lane-change-safety-coordination)
9. [Cluster Formation and Merging](#9-cluster-formation-and-merging)
10. [Dynamic Mobility and Road Following](#10-dynamic-mobility-and-road-following)

---

## 1. Multi-Metric Raft-Based Leader Election

### Purpose
Elect cluster head using distributed voting with composite scoring based on trust, connectivity, stability, centrality, and tenure.

### Pseudocode

```
FUNCTION run_cluster_election(cluster_id, cluster, current_time):
    // Step 1: Filter and prepare candidates
    candidates = []
    FOR EACH member_id IN cluster.members:
        vehicle = get_vehicle(member_id)
        
        // Exclude malicious and low-trust nodes
        IF vehicle.trust_score < 0.5 OR vehicle.is_malicious:
            CONTINUE
        
        // Calculate composite score (5 metrics)
        trust_score = vehicle.trust_score * 0.30          // 30% weight
        connectivity = count_neighbors(vehicle) / max_neighbors * 0.25  // 25% weight
        
        // Stability based on position variance
        stability = 1.0 - (position_variance(vehicle) / max_variance) * 0.20
        
        // Centrality = inverse distance to cluster center
        distance_to_center = euclidean_distance(vehicle.position, cluster.centroid)
        centrality = (1.0 - distance_to_center / cluster.radius) * 0.15
        
        // Tenure = time in cluster (rewards stable membership)
        tenure = min(vehicle.time_in_cluster / 30.0, 1.0) * 0.10
        
        composite_score = trust_score + connectivity + stability + centrality + tenure
        
        candidates.ADD({
            vehicle_id: member_id,
            score: composite_score,
            trust: vehicle.trust_score
        })
    END FOR
    
    // Step 2: No candidates - keep current leader or dissolve
    IF candidates.is_empty():
        LOG "No valid candidates for cluster " + cluster_id
        RETURN current_leader
    
    // Step 3: Sort candidates by score (descending)
    candidates.SORT_BY(score, DESCENDING)
    
    // Step 4: Raft-style voting simulation
    total_votes = 0
    vote_counts = HASHMAP()
    
    FOR EACH voter IN cluster.members:
        voter_vehicle = get_vehicle(voter)
        
        // Skip malicious voters
        IF voter_vehicle.is_malicious OR voter_vehicle.trust_score < 0.5:
            CONTINUE
        
        // Vote for highest-scored candidate (trust-weighted)
        best_candidate = candidates[0]
        vote_weight = voter_vehicle.trust_score
        
        vote_counts[best_candidate.vehicle_id] += vote_weight
        total_votes += vote_weight
    END FOR
    
    // Step 5: Determine winner (51% majority)
    winner = NULL
    majority_threshold = total_votes * 0.51
    
    FOR EACH candidate, votes IN vote_counts:
        IF votes >= majority_threshold:
            winner = candidate
            BREAK
    END FOR
    
    // Step 6: If no majority, use highest scorer
    IF winner == NULL:
        winner = candidates[0].vehicle_id
    
    // Step 7: Update cluster leadership
    old_leader = cluster.head_id
    cluster.head_id = winner
    cluster.last_election_time = current_time
    
    get_vehicle(winner).is_cluster_head = TRUE
    IF old_leader != NULL AND old_leader != winner:
        get_vehicle(old_leader).is_cluster_head = FALSE
    
    LOG "Elected " + winner + " as leader of cluster " + cluster_id
    RETURN winner
END FUNCTION
```

### Key Metrics
- **Trust Score**: 30% - from PoA and consensus engine
- **Connectivity**: 25% - number of DSRC neighbors
- **Stability**: 20% - low position variance
- **Centrality**: 15% - proximity to cluster center
- **Tenure**: 10% - time in cluster

---

## 2. Co-Leader Election and Automatic Succession

### Purpose
Select a backup leader (co-leader) who automatically takes over if the primary leader fails.

### Pseudocode

```
FUNCTION elect_co_leader(cluster, current_time):
    // Step 1: Filter candidates (exclude current leader)
    candidates = []
    FOR EACH member_id IN cluster.members:
        IF member_id == cluster.head_id:
            CONTINUE  // Skip current leader
        
        vehicle = get_vehicle(member_id)
        
        // Exclude malicious and low-trust nodes
        IF vehicle.trust_score < 0.5 OR vehicle.is_malicious:
            CONTINUE
        
        // Same composite scoring as leader election
        composite_score = calculate_composite_score(vehicle, cluster)
        
        candidates.ADD({
            vehicle_id: member_id,
            score: composite_score
        })
    END FOR
    
    // Step 2: No candidates - no co-leader
    IF candidates.is_empty():
        cluster.co_leader_id = NULL
        RETURN NULL
    
    // Step 3: Sort and select runner-up (2nd best)
    candidates.SORT_BY(score, DESCENDING)
    co_leader = candidates[0].vehicle_id
    
    // Step 4: Update cluster
    cluster.co_leader_id = co_leader
    
    LOG "Co-leader elected: " + co_leader + " in cluster " + cluster.id
    RETURN co_leader
END FUNCTION


FUNCTION check_leader_failures(current_time):
    FOR EACH cluster_id, cluster IN all_clusters:
        leader = get_vehicle(cluster.head_id)
        
        // Check if leader is out of cluster range
        distance_to_center = euclidean_distance(leader.position, cluster.centroid)
        
        IF distance_to_center > cluster.radius * 1.5:
            LOG "Leader failure detected: " + cluster.head_id + " out of range"
            
            // Automatic co-leader succession
            IF cluster.co_leader_id != NULL:
                co_leader = get_vehicle(cluster.co_leader_id)
                
                // Verify co-leader is still valid
                IF co_leader.trust_score >= 0.5 AND NOT co_leader.is_malicious:
                    // Promote co-leader to leader
                    old_leader = cluster.head_id
                    cluster.head_id = cluster.co_leader_id
                    cluster.co_leader_id = NULL
                    
                    get_vehicle(old_leader).is_cluster_head = FALSE
                    get_vehicle(cluster.head_id).is_cluster_head = TRUE
                    
                    LOG "Co-leader succession: " + cluster.head_id + " promoted to leader"
                    
                    // Elect new co-leader
                    elect_co_leader(cluster, current_time)
                    CONTINUE
            
            // No valid co-leader - trigger full re-election
            LOG "Triggering re-election for cluster " + cluster_id
            run_cluster_election(cluster_id, cluster, current_time)
            elect_co_leader(cluster, current_time)
    END FOR
END FUNCTION
```

### Succession Flow
1. **Leader Failure Detected** → Check if leader out of range or crashed
2. **Co-Leader Valid?** → If yes, instant promotion (no voting)
3. **Elect New Co-Leader** → Select new runner-up
4. **No Co-Leader?** → Trigger full Raft re-election

---

## 3. Proof-of-Authority (PoA) Malicious Detection

### Purpose
Detect and flag malicious nodes using distributed authority voting within clusters.

### Pseudocode

```
FUNCTION detect_malicious_nodes_poa(vehicles, current_time):
    // Step 1: Identify authorities (high-trust nodes)
    authorities = []
    FOR EACH vehicle IN vehicles:
        IF vehicle.trust_score > 0.8:  // Authority threshold
            authorities.ADD(vehicle)
    END FOR
    
    LOG "PoA authorities: " + authorities.count() + " nodes"
    
    // Step 2: Authorities monitor and vote
    suspicion_votes = HASHMAP()  // suspect_id -> vote_count
    
    FOR EACH authority IN authorities:
        // Get authority's cluster or nearby nodes
        cluster = get_cluster_for_vehicle(authority.id)
        
        IF cluster != NULL:
            monitored_nodes = cluster.members
        ELSE:
            // Isolated authority monitors nearby nodes
            monitored_nodes = get_neighbors_within_range(authority, 300)
        
        // Monitor each node for suspicious behavior
        FOR EACH node_id IN monitored_nodes:
            node = get_vehicle(node_id)
            
            suspicion_score = 0.0
            
            // Criterion 1: Low trust
            IF node.trust_score < 0.4:
                suspicion_score += 0.3
            
            // Criterion 2: Known malicious flag
            IF node.is_malicious:
                suspicion_score += 0.5
            
            // Criterion 3: Erratic speed (too fast)
            IF node.speed > 75:  // mph
                suspicion_score += 0.2
            
            // Criterion 4: Message spam
            IF node.message_count > 100:
                suspicion_score += 0.2
            
            // Vote if suspicion exceeds threshold
            IF suspicion_score > 0.5:
                suspicion_votes[node_id] += 1
        END FOR
    END FOR
    
    // Step 3: Flag nodes based on cluster-scoped voting
    FOR EACH suspect_id, vote_count IN suspicion_votes:
        suspect = get_vehicle(suspect_id)
        cluster = get_cluster_for_vehicle(suspect_id)
        
        // Count authorities in same cluster
        cluster_authorities = 0
        FOR EACH authority IN authorities:
            IF get_cluster_for_vehicle(authority.id) == cluster:
                cluster_authorities += 1
        END FOR
        
        // Require 30% of cluster authorities to flag
        threshold = max(cluster_authorities * 0.30, 1)
        
        IF vote_count >= threshold:
            // Flag as malicious
            suspect.is_flagged_malicious = TRUE
            
            // Apply trust penalty
            old_trust = suspect.trust_score
            suspect.trust_score *= 0.7  // 30% reduction
            
            LOG "PoA Detection: " + suspect_id + " flagged (trust: " + 
                old_trust + " → " + suspect.trust_score + ", votes: " + 
                vote_count + "/" + cluster_authorities + ")"
            
            // Remove from cluster head position if applicable
            IF suspect.is_cluster_head:
                cluster.needs_reelection = TRUE
    END FOR
END FUNCTION
```

### Detection Criteria
- **Trust < 0.4**: +0.3 suspicion
- **Known malicious**: +0.5 suspicion
- **Speed > 75 mph**: +0.2 suspicion
- **Message spam (>100)**: +0.2 suspicion
- **Threshold**: >0.5 suspicion triggers vote

### Voting Mechanism
- **Cluster-scoped**: Authorities vote only on cluster members
- **30% threshold**: Requires 30% of cluster authorities to flag
- **Penalty**: 30% trust reduction, removal from leadership

---

## 4. Relay Node Election (Multi-Hop Communication)

### Purpose
Select relay nodes to forward messages to cluster members outside direct DSRC range.

### Pseudocode

```
FUNCTION elect_relay_nodes(cluster, current_time):
    leader = get_vehicle(cluster.head_id)
    communication_range = 250  // DSRC range in pixels
    
    // Step 1: Identify out-of-range members
    out_of_range_members = []
    FOR EACH member_id IN cluster.members:
        member = get_vehicle(member_id)
        distance = euclidean_distance(leader.position, member.position)
        
        IF distance > communication_range:
            out_of_range_members.ADD(member_id)
    END FOR
    
    // Step 2: No relays needed if all in range
    IF out_of_range_members.is_empty():
        cluster.relay_nodes = []
        RETURN []
    
    // Step 3: Score potential relay candidates
    relay_candidates = []
    FOR EACH member_id IN cluster.members:
        IF member_id IN out_of_range_members:
            CONTINUE  // Out-of-range members can't be relays
        
        member = get_vehicle(member_id)
        
        // Exclude malicious nodes
        IF member.is_malicious OR member.trust_score < 0.5:
            CONTINUE
        
        // Calculate relay score (4 metrics)
        trust_component = member.trust_score * 0.35  // 35% weight
        
        // Centrality: distance to cluster center
        dist_to_center = euclidean_distance(member.position, cluster.centroid)
        centrality = (1.0 - dist_to_center / cluster.radius) * 0.25
        
        // Stability: low speed variance
        stability = (1.0 - member.speed_variance / max_variance) * 0.20
        
        // Coverage: how many out-of-range members can this relay reach?
        coverage_count = 0
        FOR EACH oor_member IN out_of_range_members:
            oor_vehicle = get_vehicle(oor_member)
            relay_dist = euclidean_distance(member.position, oor_vehicle.position)
            IF relay_dist <= communication_range:
                coverage_count += 1
        END FOR
        coverage = (coverage_count / out_of_range_members.count()) * 0.20
        
        relay_score = trust_component + centrality + stability + coverage
        
        relay_candidates.ADD({
            vehicle_id: member_id,
            score: relay_score,
            coverage: coverage_count
        })
    END FOR
    
    // Step 4: Select top relay nodes (greedy set cover)
    selected_relays = []
    covered_members = SET()
    
    WHILE covered_members.count() < out_of_range_members.count() AND relay_candidates.is_not_empty():
        // Sort by score
        relay_candidates.SORT_BY(score, DESCENDING)
        
        best_relay = relay_candidates[0]
        selected_relays.ADD(best_relay.vehicle_id)
        
        // Mark covered members
        relay_vehicle = get_vehicle(best_relay.vehicle_id)
        FOR EACH oor_member IN out_of_range_members:
            oor_vehicle = get_vehicle(oor_member)
            distance = euclidean_distance(relay_vehicle.position, oor_vehicle.position)
            IF distance <= communication_range:
                covered_members.ADD(oor_member)
        END FOR
        
        // Remove selected relay from candidates
        relay_candidates.REMOVE(best_relay)
        
        // Limit to 10 relays max
        IF selected_relays.count() >= 10:
            BREAK
    END WHILE
    
    // Step 5: Update cluster
    cluster.relay_nodes = selected_relays
    
    LOG "Relay nodes elected in cluster " + cluster.id + ": " + 
        selected_relays.count() + " relays for " + 
        out_of_range_members.count() + " out-of-range members"
    
    RETURN selected_relays
END FUNCTION
```

### Relay Scoring Metrics
- **Trust**: 35% - reliability of relay
- **Centrality**: 25% - position in cluster
- **Stability**: 20% - low speed variance
- **Coverage**: 20% - members reachable

### Selection Algorithm
- **Greedy set cover**: Select relays that cover most uncovered members
- **Max 10 relays**: Prevent excessive overhead

---

## 5. Boundary Node Election (Inter-Cluster Communication)

### Purpose
Select boundary nodes to act as gateways between neighboring clusters.

### Pseudocode

```
FUNCTION elect_boundary_nodes(cluster, all_clusters, current_time):
    boundary_detection_range = 600  // pixels
    
    // Step 1: Find neighboring clusters
    neighboring_clusters = []
    cluster_center = cluster.centroid
    
    FOR EACH other_cluster_id, other_cluster IN all_clusters:
        IF other_cluster_id == cluster.id:
            CONTINUE
        
        distance = euclidean_distance(cluster_center, other_cluster.centroid)
        
        IF distance <= boundary_detection_range:
            neighboring_clusters.ADD(other_cluster)
    END FOR
    
    // Step 2: No neighbors - no boundary nodes needed
    IF neighboring_clusters.is_empty():
        cluster.boundary_nodes = {}
        RETURN {}
    
    // Step 3: For each neighbor, elect one boundary node
    boundary_nodes = {}  // neighbor_cluster_id -> boundary_node_id
    
    FOR EACH neighbor_cluster IN neighboring_clusters:
        // Score candidates based on proximity to neighbor
        candidates = []
        
        FOR EACH member_id IN cluster.members:
            member = get_vehicle(member_id)
            
            // Exclude malicious and low-trust nodes
            IF member.is_malicious OR member.trust_score < 0.6:
                CONTINUE
            
            // Calculate score (3 metrics)
            trust_component = member.trust_score * 0.40  // 40% weight
            
            // Proximity to neighbor cluster center
            distance_to_neighbor = euclidean_distance(
                member.position, 
                neighbor_cluster.centroid
            )
            proximity = (1.0 - distance_to_neighbor / boundary_detection_range) * 0.35
            
            // Connectivity: number of neighbors
            connectivity = (member.neighbor_count / max_neighbors) * 0.25
            
            boundary_score = trust_component + proximity + connectivity
            
            candidates.ADD({
                vehicle_id: member_id,
                score: boundary_score,
                distance: distance_to_neighbor
            })
        END FOR
        
        // Select best candidate for this neighbor
        IF candidates.is_not_empty():
            candidates.SORT_BY(score, DESCENDING)
            best_boundary = candidates[0].vehicle_id
            boundary_nodes[neighbor_cluster.id] = best_boundary
    END FOR
    
    // Step 4: Update cluster
    cluster.boundary_nodes = boundary_nodes
    
    LOG "Boundary nodes elected in cluster " + cluster.id + ": " + 
        boundary_nodes.count() + " boundary nodes for " + 
        neighboring_clusters.count() + " neighboring clusters"
    
    RETURN boundary_nodes
END FUNCTION
```

### Boundary Scoring Metrics
- **Trust**: 40% - reliable gateway
- **Proximity**: 35% - close to neighbor cluster
- **Connectivity**: 25% - well-connected

### Selection Strategy
- **One boundary per neighbor**: Each neighboring cluster gets one dedicated gateway
- **Bidirectional**: Both clusters elect boundaries toward each other

---

## 6. V2V Message Broadcasting with Multi-Hop

### Purpose
Broadcast safety messages with multi-hop relay forwarding and inter-cluster propagation.

### Pseudocode

```
FUNCTION broadcast_v2v_message(sender_id, message_type, content, priority):
    sender = get_vehicle(sender_id)
    cluster = get_cluster_for_vehicle(sender_id)
    communication_range = 250  // DSRC range
    
    message = {
        id: generate_unique_id(),
        sender: sender_id,
        type: message_type,  // collision_warning, emergency, lane_change, etc.
        content: content,
        priority: priority,
        timestamp: current_time,
        hop_count: 0,
        forwarded_by: []
    }
    
    // Step 1: Direct broadcast to neighbors in DSRC range
    direct_recipients = []
    FOR EACH vehicle IN all_vehicles:
        IF vehicle.id == sender_id:
            CONTINUE
        
        distance = euclidean_distance(sender.position, vehicle.position)
        IF distance <= communication_range:
            vehicle.receive_message(message)
            direct_recipients.ADD(vehicle.id)
    END FOR
    
    LOG "V2V broadcast: " + sender_id + " sent " + message_type + 
        " to " + direct_recipients.count() + " direct recipients"
    
    // Step 2: Multi-hop via relay nodes (if sender is leader)
    IF sender.is_cluster_head AND cluster != NULL:
        FOR EACH relay_id IN cluster.relay_nodes:
            relay = get_vehicle(relay_id)
            
            // Relay forwards to out-of-range members
            FOR EACH member_id IN cluster.members:
                IF member_id IN direct_recipients:
                    CONTINUE  // Already received directly
                
                member = get_vehicle(member_id)
                relay_distance = euclidean_distance(relay.position, member.position)
                
                IF relay_distance <= communication_range:
                    // Create relayed message
                    relayed_msg = COPY(message)
                    relayed_msg.hop_count += 1
                    relayed_msg.forwarded_by.ADD(relay_id)
                    
                    member.receive_message(relayed_msg)
                    statistics.relay_messages += 1
        END FOR
    END IF
    
    // Step 3: Inter-cluster propagation via boundary nodes (for high-priority)
    IF priority == HIGH AND cluster != NULL:
        FOR EACH neighbor_cluster_id, boundary_id IN cluster.boundary_nodes:
            boundary = get_vehicle(boundary_id)
            neighbor_cluster = get_cluster(neighbor_cluster_id)
            
            // Boundary forwards to neighbor cluster's boundary
            IF neighbor_cluster.boundary_nodes.contains(cluster.id):
                neighbor_boundary_id = neighbor_cluster.boundary_nodes[cluster.id]
                neighbor_boundary = get_vehicle(neighbor_boundary_id)
                
                // Forward message
                inter_cluster_msg = COPY(message)
                inter_cluster_msg.hop_count += 1
                inter_cluster_msg.forwarded_by.ADD(boundary_id)
                
                neighbor_boundary.receive_message(inter_cluster_msg)
                
                // Neighbor boundary forwards to its cluster leader
                neighbor_leader = get_vehicle(neighbor_cluster.head_id)
                neighbor_leader.receive_message(inter_cluster_msg)
                
                statistics.inter_cluster_messages += 1
        END FOR
    END IF
    
    RETURN message.id
END FUNCTION


FUNCTION receive_message(message):
    // Process received message based on type
    SWITCH message.type:
        CASE "collision_warning":
            handle_collision_warning(message)
        CASE "emergency_alert":
            handle_emergency_alert(message)
        CASE "lane_change_intent":
            handle_lane_change_request(message)
        CASE "brake_warning":
            handle_brake_warning(message)
        CASE "traffic_jam":
            handle_traffic_jam_alert(message)
    END SWITCH
    
    // Update statistics
    self.messages_received += 1
END FUNCTION
```

### Message Flow
1. **Direct Broadcast**: Sender → All neighbors in DSRC range (250px)
2. **Relay Forwarding**: Leader → Relay → Out-of-range members
3. **Inter-Cluster**: Boundary A → Boundary B → Neighbor Leader

### Priority Levels
- **HIGH**: Emergency alerts, collision warnings (propagate inter-cluster)
- **MEDIUM**: Lane change intents, brake warnings
- **LOW**: Traffic jam alerts, general updates

---

## 7. Predictive Collision Detection

### Purpose
Detect imminent collisions by predicting future vehicle positions.

### Pseudocode

```
FUNCTION check_collision_risk(vehicle, current_time):
    prediction_time = 1.0  // seconds ahead
    collision_threshold = 30  // pixels (safety margin)
    
    // Step 1: Calculate vehicle's future position
    future_x = vehicle.x + vehicle.velocity_x * prediction_time
    future_y = vehicle.y + vehicle.velocity_y * prediction_time
    
    // Step 2: Check all neighbors for potential collision
    FOR EACH neighbor IN get_neighbors_within_range(vehicle, 300):
        // Calculate neighbor's future position
        neighbor_future_x = neighbor.x + neighbor.velocity_x * prediction_time
        neighbor_future_y = neighbor.y + neighbor.velocity_y * prediction_time
        
        // Calculate distance at predicted positions
        future_distance = euclidean_distance(
            (future_x, future_y),
            (neighbor_future_x, neighbor_future_y)
        )
        
        // Collision imminent?
        IF future_distance < collision_threshold:
            // Calculate time to collision
            current_distance = euclidean_distance(
                (vehicle.x, vehicle.y),
                (neighbor.x, neighbor.y)
            )
            relative_speed = abs(vehicle.speed - neighbor.speed)
            
            IF relative_speed > 0:
                time_to_collision = current_distance / relative_speed
            ELSE:
                time_to_collision = INFINITY
            
            // Only warn if collision within 2 seconds
            IF time_to_collision < 2.0:
                // Broadcast collision warning
                broadcast_v2v_message(
                    vehicle.id,
                    "collision_warning",
                    {
                        other_vehicle: neighbor.id,
                        time_to_collision: time_to_collision,
                        predicted_distance: future_distance
                    },
                    priority=HIGH
                )
                
                // Take evasive action
                vehicle.speed *= 0.8  // Reduce speed by 20%
                
                LOG "⚠️ Collision warning: " + vehicle.id + " ↔ " + 
                    neighbor.id + " (TTC: " + time_to_collision + "s)"
                
                statistics.collision_warnings += 1
    END FOR
END FUNCTION


FUNCTION handle_collision_warning(message):
    // Reduce speed immediately
    self.speed *= 0.7  // 30% reduction
    
    // Attempt lane change if safe
    IF self.current_lane > 0:  // Not in rightmost lane
        IF check_lane_change_safety(self, self.current_lane - 1):
            initiate_lane_change(self.current_lane - 1)
END FUNCTION
```

### Detection Algorithm
1. **Predict positions**: 1 second ahead using velocity
2. **Check distance**: If future distance < 30 pixels → collision risk
3. **Calculate TTC**: Time-to-collision based on relative speed
4. **Warn if TTC < 2s**: Broadcast high-priority warning
5. **Evasive action**: Reduce speed 20-30%, attempt lane change

---

## 8. Lane Change Safety Coordination

### Purpose
Coordinate lane changes with neighboring vehicles to ensure safety.

### Pseudocode

```
FUNCTION initiate_lane_change(vehicle, target_lane):
    // Step 1: Broadcast lane change intent
    broadcast_v2v_message(
        vehicle.id,
        "lane_change_intent",
        {
            current_lane: vehicle.current_lane,
            target_lane: target_lane,
            current_speed: vehicle.speed
        },
        priority=MEDIUM
    )
    
    // Step 2: Wait for responses (100ms timeout)
    WAIT(0.1)  // seconds
    
    // Step 3: Check safety
    IF check_lane_change_safety(vehicle, target_lane):
        // Execute lane change
        vehicle.target_lane = target_lane
        vehicle.is_changing_lane = TRUE
        
        LOG "Lane change: " + vehicle.id + " " + 
            vehicle.current_lane + " → " + target_lane
        
        statistics.lane_changes += 1
        RETURN TRUE
    ELSE:
        LOG "Lane change aborted: " + vehicle.id + " (unsafe)"
        RETURN FALSE
END FUNCTION


FUNCTION check_lane_change_safety(vehicle, target_lane):
    safe_distance_front = 50  // pixels
    safe_distance_rear = 40   // pixels
    lane_offset_delta = (target_lane - vehicle.current_lane) * lane_width
    
    // Calculate target position
    target_x = vehicle.x + lane_offset_delta * sin(vehicle.direction)
    target_y = vehicle.y - lane_offset_delta * cos(vehicle.direction)
    
    // Check all vehicles in target lane
    FOR EACH other_vehicle IN all_vehicles:
        IF other_vehicle.id == vehicle.id:
            CONTINUE
        
        // Check if other vehicle is in target lane
        IF other_vehicle.current_lane != target_lane:
            CONTINUE
        
        // Check if on same road
        IF other_vehicle.current_road != vehicle.current_road:
            CONTINUE
        
        distance = euclidean_distance(
            (target_x, target_y),
            (other_vehicle.x, other_vehicle.y)
        )
        
        // Check distance based on relative position
        IF is_vehicle_ahead(other_vehicle, vehicle):
            IF distance < safe_distance_front:
                RETURN FALSE  // Too close in front
        ELSE:
            IF distance < safe_distance_rear:
                RETURN FALSE  // Too close behind
    END FOR
    
    // All checks passed
    RETURN TRUE
END FUNCTION


FUNCTION handle_lane_change_request(message):
    sender = get_vehicle(message.sender)
    
    // Check if this vehicle is in the target lane
    IF self.current_lane == message.content.target_lane:
        // Check if we're in the way
        distance = euclidean_distance(
            (self.x, self.y),
            (sender.x, sender.y)
        )
        
        // If close, adjust speed to create space
        IF distance < 60:
            IF is_vehicle_ahead(self, sender):
                self.speed *= 1.1  // Speed up to create front gap
            ELSE:
                self.speed *= 0.9  // Slow down to create rear gap
            
            LOG "Yielding for lane change: " + message.sender
END FUNCTION
```

### Safety Protocol
1. **Intent Broadcast**: Announce lane change to all neighbors
2. **Wait Period**: 100ms for neighbor responses
3. **Safety Check**: Verify 50px front, 40px rear clearance
4. **Neighbor Cooperation**: Vehicles in target lane adjust speed
5. **Execute**: Gradual lateral movement over 2-3 seconds

---

## 9. Cluster Formation and Merging

### Purpose
Form dynamic clusters and merge overlapping clusters to prevent sub-clustering.

### Pseudocode

```
FUNCTION mobility_based_clustering(vehicles, current_time):
    max_cluster_radius = 450  // pixels
    speed_threshold = 15.0    // m/s difference
    direction_threshold = 1.0  // radians (~57 degrees)
    min_cluster_size = 2
    
    // Step 1: Clear old cluster assignments
    reset_cluster_assignments()
    
    // Step 2: Process each vehicle
    FOR EACH vehicle IN vehicles:
        // Skip if already in a cluster
        IF vehicle.cluster_id != NULL:
            CONTINUE
        
        // Find nearby compatible vehicles
        nearby_compatible = []
        FOR EACH other_vehicle IN vehicles:
            IF other_vehicle.id == vehicle.id:
                CONTINUE
            
            distance = euclidean_distance(vehicle.position, other_vehicle.position)
            IF distance > max_cluster_radius:
                CONTINUE
            
            speed_diff = abs(vehicle.speed - other_vehicle.speed)
            IF speed_diff > speed_threshold:
                CONTINUE
            
            direction_diff = abs(vehicle.direction - other_vehicle.direction)
            direction_diff = min(direction_diff, 2*PI - direction_diff)
            IF direction_diff > direction_threshold:
                CONTINUE
            
            nearby_compatible.ADD(other_vehicle)
        END FOR
        
        // Create cluster if enough compatible neighbors
        IF nearby_compatible.count() >= min_cluster_size - 1:
            new_cluster = create_cluster(vehicle, nearby_compatible, current_time)
            clusters.ADD(new_cluster)
    END FOR
    
    // Step 3: Merge overlapping clusters
    merge_overlapping_clusters(current_time)
    
    RETURN clusters
END FUNCTION


FUNCTION merge_overlapping_clusters(current_time):
    merge_distance_threshold = 450  // pixels
    overlap_ratio_threshold = 0.3   // 30% shared members
    close_distance = 350            // always merge if this close
    
    merged_count = 0
    processed = SET()
    
    // Step 1: Find merge candidates
    FOR EACH cluster1 IN clusters:
        IF cluster1 IN processed:
            CONTINUE
        
        leader1 = get_vehicle(cluster1.head_id)
        merge_targets = []
        
        FOR EACH cluster2 IN clusters:
            IF cluster2 == cluster1 OR cluster2 IN processed:
                CONTINUE
            
            leader2 = get_vehicle(cluster2.head_id)
            
            // Calculate distance between leaders
            distance = euclidean_distance(leader1.position, leader2.position)
            
            IF distance < merge_distance_threshold:
                // Count shared/nearby members
                shared_members = 0
                FOR EACH member IN cluster2.members:
                    member_vehicle = get_vehicle(member)
                    dist_to_leader1 = euclidean_distance(
                        member_vehicle.position,
                        leader1.position
                    )
                    IF dist_to_leader1 < 250:  // Within communication range
                        shared_members += 1
                END FOR
                
                overlap_ratio = shared_members / cluster2.members.count()
                
                // Merge if significant overlap or very close
                IF overlap_ratio > overlap_ratio_threshold OR distance < close_distance:
                    merge_targets.ADD(cluster2)
        END FOR
        
        // Step 2: Execute merges
        IF merge_targets.is_not_empty():
            FOR EACH target_cluster IN merge_targets:
                // Merge all members into cluster1
                FOR EACH member IN target_cluster.members:
                    cluster1.members.ADD(member)
                    get_vehicle(member).cluster_id = cluster1.id
                END FOR
                
                // Remove target cluster
                clusters.REMOVE(target_cluster)
                processed.ADD(target_cluster)
                merged_count += 1
            END FOR
            
            // Recalculate cluster1 properties
            update_cluster_centroid(cluster1)
            update_cluster_radius(cluster1)
            
            LOG "🔗 Merged " + merge_targets.count() + " clusters into " + cluster1.id
    END FOR
    
    LOG "Total merges: " + merged_count
END FUNCTION
```

### Clustering Criteria
- **Proximity**: Within 450-pixel radius
- **Speed**: ±15 m/s difference
- **Direction**: ±57 degrees alignment

### Merging Criteria
- **Leader distance**: < 450 pixels
- **Overlap ratio**: > 30% shared members
- **OR close distance**: < 350 pixels (always merge)

---

## 10. Dynamic Mobility and Road Following

### Purpose
Move vehicles along road network with lane-following and traffic light compliance.

### Pseudocode

```
FUNCTION update_vehicle_position(vehicle, delta_time):
    // Step 1: Check traffic light (if at intersection)
    IF vehicle.at_intersection:
        light_state = get_traffic_light_state(vehicle.current_intersection)
        
        IF light_state == RED AND NOT vehicle.is_emergency:
            // Calculate distance to stop line
            stop_line_distance = calculate_stop_line_distance(vehicle)
            
            IF stop_line_distance < 20:
                // Brake to stop
                vehicle.speed = max(0, vehicle.speed - 10 * delta_time)
                RETURN  // Don't move forward
        END IF
    END IF
    
    // Step 2: Follow current road
    current_road = get_road(vehicle.current_road_id)
    
    // Calculate direction along road
    road_direction = atan2(
        current_road.end_y - current_road.start_y,
        current_road.end_x - current_road.start_x
    )
    
    // Apply lane offset (perpendicular to road direction)
    lane_width = 12  // pixels
    lane_offset = (vehicle.current_lane - num_lanes/2) * lane_width
    
    offset_x = lane_offset * sin(road_direction + PI/2)
    offset_y = lane_offset * cos(road_direction + PI/2)
    
    // Step 3: Update position
    distance_to_travel = vehicle.speed * delta_time
    
    vehicle.x += cos(road_direction) * distance_to_travel + offset_x * 0.1
    vehicle.y += sin(road_direction) * distance_to_travel + offset_y * 0.1
    vehicle.direction = road_direction
    
    // Step 4: Check if reached end of road
    distance_to_end = euclidean_distance(
        (vehicle.x, vehicle.y),
        (current_road.end_x, current_road.end_y)
    )
    
    IF distance_to_end < 10:
        // Transition to next road
        next_road = select_next_road(vehicle, current_road)
        vehicle.current_road_id = next_road.id
        vehicle.at_intersection = TRUE
    ELSE:
        vehicle.at_intersection = FALSE
    END IF
    
    // Step 5: Lane change execution (if in progress)
    IF vehicle.is_changing_lane:
        progress = (current_time - vehicle.lane_change_start_time) / 2.0  // 2s duration
        
        IF progress >= 1.0:
            // Lane change complete
            vehicle.current_lane = vehicle.target_lane
            vehicle.is_changing_lane = FALSE
        ELSE:
            // Gradual lateral movement
            lane_delta = (vehicle.target_lane - vehicle.current_lane) * lane_width
            vehicle.lane_offset = lane_delta * progress
    END IF
    
    // Step 6: Update velocity for next iteration
    vehicle.velocity_x = cos(vehicle.direction) * vehicle.speed
    vehicle.velocity_y = sin(vehicle.direction) * vehicle.speed
END FUNCTION


FUNCTION select_next_road(vehicle, current_road):
    intersection = get_intersection(current_road.end_node)
    outgoing_roads = intersection.outgoing_roads
    
    // Emergency vehicles: prefer straight/fastest route
    IF vehicle.is_emergency:
        RETURN select_straightest_road(outgoing_roads, current_road.direction)
    
    // Normal vehicles: weighted random selection
    weights = []
    FOR EACH road IN outgoing_roads:
        // Prefer roads in similar direction
        direction_diff = abs(road.direction - current_road.direction)
        weight = 1.0 / (1.0 + direction_diff)
        weights.ADD(weight)
    END FOR
    
    RETURN weighted_random_choice(outgoing_roads, weights)
END FUNCTION
```

### Movement Steps
1. **Traffic Light Check**: Stop at red lights (unless emergency)
2. **Road Following**: Move along road direction
3. **Lane Offset**: Apply perpendicular offset for lane position
4. **Position Update**: x,y based on speed × delta_time
5. **Road Transition**: Switch to next road at intersection
6. **Lane Change**: Gradual 2-second lateral movement

---

## Summary of Key Algorithms

| Algorithm | Purpose | Complexity | Key Metrics |
|-----------|---------|------------|-------------|
| **Raft Election** | Cluster head selection | O(n log n) | 5 metrics, trust-weighted voting |
| **Co-Leader** | Automatic succession | O(n log n) | Instant promotion on failure |
| **PoA Detection** | Malicious node flagging | O(a × m) | 30% authority threshold |
| **Relay Election** | Multi-hop coverage | O(n × m) | Greedy set cover |
| **Boundary Election** | Inter-cluster gateway | O(c × n) | One per neighbor cluster |
| **V2V Broadcast** | Message propagation | O(n) | 3-tier: direct/relay/boundary |
| **Collision Detection** | Future position check | O(n²) | 1s prediction, 30px threshold |
| **Lane Change** | Cooperative safety | O(n) | 50px/40px clearance |
| **Clustering** | Dynamic formation | O(n²) | 450px radius, speed/direction |
| **Cluster Merging** | Sub-cluster elimination | O(c²) | 30% overlap, 350px threshold |

**Legend:**
- n = number of vehicles
- m = members per cluster
- a = number of authorities
- c = number of clusters

---

*All pseudocode based on actual implementation in city_traffic_simulator.py*
