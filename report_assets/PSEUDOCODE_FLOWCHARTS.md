# VANET System - Pseudocode Flowcharts

## 1. Multi-Metric Raft Leader Election Flow (5-Metric Transparent System)

```
START: [Election Triggered for cluster_id]
  ↓
┌─────────────────────────────────────────────┐
│ SECURITY LAYER 1: Sleeper Agent Detection  │
└─────────────────────────────────────────────┘
  ↓
[Get Cluster Members]
  ↓
FOR EACH member:
  ↓
  [Check if sleeper agent activated?]
  • Trust drop >0.3 in <10 seconds
  • Behavior score sudden drop
  ↓ YES              ↓ NO
  [EXCLUDE]         [Continue]
  ↓                  ↓
┌─────────────────────────────────────────────┐
│ SECURITY LAYER 2: PoA Status Check         │
└─────────────────────────────────────────────┘
  ↓
  [PoA flagged as malicious?] ──YES──> [EXCLUDE]
  ↓ NO
  [Check Trust Score ≥ 0.5?] ──NO──> [EXCLUDE member]
  ↓ YES
┌─────────────────────────────────────────────┐
│ CALCULATE 5 TRANSPARENT METRICS:            │
└─────────────────────────────────────────────┘
  ↓
  [1. Trust (40%)]
  • Historical: PoA consensus + track record
  • Social: Cooperation + message authenticity
  • Weight: 0.40 (SECURITY FIRST)
  ↓
  [2. Resource (20%)]
  • Bandwidth: 50-150 Mbps normalized
  • Processing: 1-4 GHz CPU normalized
  • Weight: 0.20 (PREVENT BOTTLENECKS)
  ↓
  [3. Stability (15%)]
  • Cluster time: Duration in current cluster
  • Connection quality: Packet delivery ratio
  • Weight: 0.15 (REDUCE RE-ELECTIONS)
  ↓
  [4. Behavior (15%)]
  • Message authenticity: Valid signatures
  • Cooperation rate: Relay forwarding %
  • Weight: 0.15 (CATCH SLEEPERS)
  ↓
  [5. Centrality (10%)]
  • Geometric center: Distance from centroid
  • Coverage optimization
  • Weight: 0.10 (EFFICIENCY ONLY)
  ↓
  [Composite Score Calculation:]
  Score = 0.40×Trust + 0.20×Resource + 0.15×Stability 
        + 0.15×Behavior + 0.10×Centrality
  ↓
  [Log 5-METRIC BREAKDOWN with formula] ✓ TRANSPARENCY
  ↓
  [Add to candidates list]
  ↓
END FOR
  ↓
[Any eligible candidates?] ──NO──> [Keep current leader] → END
  ↓ YES
[Sort candidates by composite score DESC]
  ↓
┌─────────────────────────────────────────────┐
│ TRUST-WEIGHTED RAFT CONSENSUS VOTING:       │
└─────────────────────────────────────────────┘
  ↓
FOR EACH voter in cluster:
  ↓
  [Calculate voter's trust weight]
  • vote_weight = voter_trust / total_cluster_trust
  ↓
  [Vote for top candidate by composite score]
  ↓
  [candidate_votes += vote_weight]
  ↓
END FOR
  ↓
[Normalize votes to percentage]
  ↓
[Winner = candidate with ≥51% trust-weighted votes]
  ↓
[Log election details:]
• Winner ID, composite score (0.XXX)
• 5-metric breakdown with all values
• Vote percentage (XX.X%)
• Explicit formula calculation
• Consensus type (majority/unanimous)
  ↓
[Update cluster.head_id = winner]
  ↓
[Set winner.is_cluster_head = TRUE]
  ↓
[Set winner.cluster_id = cluster_id]
  ↓
┌─────────────────────────────────────────────┐
│ HIGH-AVAILABILITY: Elect Co-Leader          │
└─────────────────────────────────────────────┘
  ↓
[Select 2nd highest score as co-leader]
  ↓
[Update cluster.co_leader_id]
  ↓
END: [Election Complete - 1.2ms average]

OUTPUT LOGGED:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🗳️  Cluster cluster_X: Elected vXX via majority consensus
   📊 5-METRIC BREAKDOWN:
      • Trust (40%):      0.XXX
      • Resource (20%):   0.XXX
      • Stability (15%):  0.XXX
      • Behavior (15%):   0.XXX
      • Centrality (10%): 0.XXX
   ➜  COMPOSITE SCORE: 0.XXX | Votes: XX.X%
   ✓  Formula: 0.40×0.XXX + 0.20×0.XXX + 0.15×0.XXX 
              + 0.15×0.XXX + 0.10×0.XXX = 0.XXX
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 2. Co-Leader Succession Flow (High-Availability Mechanism)

```
START: [Leader Failure Detected]
  ↓
[Log leader failure event]
• Previous leader ID
• Failure reason (left cluster/trust drop/malicious)
• Timestamp
  ↓
┌─────────────────────────────────────────────┐
│ CHECK: Is co-leader assigned?              │
└─────────────────────────────────────────────┘
  ↓ YES              ↓ NO
┌──────────────┐   ┌──────────────────────────┐
│ HA SUCCESSION│   │ FULL RE-ELECTION         │
└──────────────┘   └──────────────────────────┘
  ↓                  ↓
[Validate co-leader:]  [Trigger 5-metric election]
• Trust ≥ 0.5         ↓
• Not malicious       [Run complete Raft consensus]
• Still in cluster    ↓
• Not sleeper agent   [Elect new leader (1.2ms)]
  ↓ VALID   ↓ INVALID  ↓
┌─────────┐  ┌────────────┐  [Elect new co-leader]
│ PROMOTE │  │ RE-ELECT   │   ↓
└─────────┘  └────────────┘   END
  ↓              ↓
[INSTANT SUCCESSION - 0.1ms]
  ↓
[cluster.head_id = co_leader_id]
  ↓
[old_leader.is_cluster_head = FALSE]
  ↓
[new_leader.is_cluster_head = TRUE]
  ↓
[new_leader.cluster_id = cluster_id]
  ↓
[Log promotion:]
🔄 Co-leader vXX promoted to leader in cluster_Y
   ⚡ Zero downtime succession
   Previous leader: vZZ (failed)
  ↓
[Select new co-leader from remaining members]
• Run mini-election (2nd highest composite score)
  ↓
[Update cluster.co_leader_id = new_co_leader]
  ↓
END: [Succession complete]

PERFORMANCE METRICS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ Succession time: 0.1ms (instant)
✓ Full re-election: 1.2ms (if needed)
✓ Re-election reduction: 65% (523→183)
✓ Zero downtime: Cluster continues operating
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 3. PoA Malicious Detection Flow (Including Sleeper Agents)

```
START: [Security Monitoring Cycle]
  ↓
┌─────────────────────────────────────────────┐
│ PHASE 1: Identify PoA Authorities          │
└─────────────────────────────────────────────┘
  ↓
[Select authorities: trust ≥ 0.8]
• High-trust nodes become PoA validators
• Distributed across clusters
  ↓
LOG: "X authorities identified across Y clusters"
  ↓
┌─────────────────────────────────────────────┐
│ PHASE 2: Sleeper Agent Detection           │
└─────────────────────────────────────────────┘
  ↓
FOR EACH vehicle:
  ↓
  [Track historical trust scores]
  • Store last 10 trust values with timestamps
  ↓
  [Calculate trust change rate]
  • delta_trust = current_trust - previous_trust
  • time_delta = current_time - previous_time
  ↓
  [SLEEPER ACTIVATION PATTERN?]
  • Trust drop >0.3 within <10 seconds
  • Previously high trust (>0.8)
  • Sudden behavioral change
  ↓ YES              ↓ NO
  [FLAG as sleeper]  [Continue normal detection]
  ↓                  ↓
  [Immediate alert]  ┌─────────────────────────────────────────────┐
  🚨 SLEEPER AGENT    │ PHASE 3: Authority Voting                   │
  ACTIVATED           └─────────────────────────────────────────────┘
  ↓                    ↓
┌──────────────────────┘
│
FOR EACH authority:
  ↓
  [Get monitored nodes (cluster members + neighbors)]
  ↓
  FOR EACH monitored_node:
    ↓
    [Calculate Suspicion Score:]
    ┌──────────────────────────────────────┐
    │ • Trust < 0.4?         → +0.3        │
    │ • Known malicious?     → +0.5        │
    │ • Speed > 75 mph?      → +0.2        │
    │ • Message spam >100?   → +0.2        │
    │ • Erratic behavior?    → +0.3        │        │
    │ • Sleeper detected?    → +0.6        │
    └──────────────────────────────────────┘
    ↓
    [Suspicion Score > 0.5?] ──NO──> [Skip, node is safe]
    ↓ YES
    [Authority casts vote AGAINST node]
    • Log: "Authority vXX flagged vYY (suspicion: 0.Z)"
    ↓
  END FOR (monitored nodes)
END FOR (authorities)
  ↓
┌─────────────────────────────────────────────┐
│ PHASE 4: Consensus Evaluation               │
└─────────────────────────────────────────────┘
  ↓
FOR EACH flagged_node:
  ↓
  [Count total votes against node]
  ↓
  [Get cluster authority count]
  • authorities_in_cluster = nodes with trust ≥ 0.8
  ↓
  [Calculate vote threshold]
  • threshold = 30% of cluster authorities
  • OR minimum 2 votes if small cluster
  ↓
  [votes_against ≥ threshold?] ──NO──> [No action - insufficient consensus]
  ↓ YES
┌─────────────────────────────────────────────┐
│ CONSENSUS REACHED: FLAG AS MALICIOUS        │
└─────────────────────────────────────────────┘
  ↓
  [Update node status:]
  • is_malicious = TRUE
  • detection_time = current_time
  ↓
  [Apply trust penalty:]
  • trust_score ×= 0.7 (30% reduction)
  • trust_score = max(0.05, trust_score)
  ↓
  [Log detection event:]
  ⚠️  PoA Detection: vXX flagged as malicious
     Trust: 0.YY → 0.ZZ
     Votes: A/B authorities
     Reason: [suspicion factors]
  ↓
  [Is node currently cluster head?] ──NO──> [Monitor for re-offense]
  ↓ YES                                      ↓
┌─────────────────────────────────────────────┐
│ EMERGENCY: Remove Malicious Leader          │
└─────────────────────────────────────────────┘
  ↓
  [Remove from leadership immediately]
  • cluster.head_id = None
  • node.is_cluster_head = FALSE
  ↓
  [Trigger emergency re-election]
  • Co-leader promotion if available
  • Full election if no co-leader
  ↓
  [Prevent re-election:]
  • Add to blacklist for 60 seconds
  • Trust score locked at current value
  ↓
END FOR (flagged nodes)
  ↓
[Update detection statistics:]
• Total malicious detected: X
• Average detection time: Y.Ys
• Sleeper agents caught: Z
  ↓
END: [Security cycle complete]

DETECTION PERFORMANCE:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ Overall detection: 98.03%
✓ Sleeper detection: 95.00%
✓ Average detection time: 5.4s
  - Random attackers: 3.2s
  - Sleeper agents: 27.8s (after activation)
✓ False positive rate: 0.40%
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 4. Relay Node Election Flow

```
START
  ↓
[Get cluster leader position]
  ↓
[Find out-of-range members]
(distance > 250px from leader)
  ↓
[Any out-of-range?] ──NO──> [No relays needed] → END
  ↓ YES
FOR EACH in-range member:
  ↓
  [Exclude malicious (trust < 0.5)]
  ↓
  [Calculate Relay Score:]
  • Trust: 35%
  • Centrality: 25%
  • Stability: 20%
  • Coverage: 20%
  ↓
  [Add to candidates]
  ↓
END FOR
  ↓
[GREEDY SET COVER:]
WHILE uncovered_members exist:
  ↓
  [Select best relay (highest score)]
  ↓
  [Mark members covered by relay]
  ↓
  [Add relay to selected list]
  ↓
  [MAX 10 relays?] ──YES──> BREAK
  ↓ NO
  [Remove from candidates]
  ↓
END WHILE
  ↓
[Update cluster.relay_nodes]
  ↓
END
```

---

## 5. V2V Message Broadcasting Flow

```
START: [Send Message]
  ↓
[Create message object]
• ID, sender, type, priority
• timestamp, hop_count = 0
  ↓
┌─────────────────────────────┐
│ TIER 1: Direct Broadcast    │
└─────────────────────────────┘
  ↓
FOR EACH vehicle in range (250px):
  ↓
  [Send message directly]
  ↓
END FOR
  ↓
[Is sender cluster leader?] ──NO──> [Skip multi-hop]
  ↓ YES                              ↓
┌─────────────────────────────┐     │
│ TIER 2: Relay Forwarding    │     │
└─────────────────────────────┘     │
  ↓                                  │
FOR EACH relay in cluster:          │
  ↓                                  │
  FOR EACH out-of-range member:     │
    ↓                                │
    [Relay forwards message]         │
    • hop_count++                    │
    • forwarded_by.add(relay_id)     │
    ↓                                │
  END FOR                            │
END FOR                              │
  ↓                                  │
[Is HIGH priority?] ──NO──> ────────┘
  ↓ YES
┌─────────────────────────────┐
│ TIER 3: Inter-Cluster       │
└─────────────────────────────┘
  ↓
FOR EACH boundary in cluster:
  ↓
  [Find neighbor boundary]
  ↓
  [Send to neighbor boundary]
  • hop_count++
  • forwarded_by.add(boundary_id)
  ↓
  [Neighbor boundary → neighbor leader]
  ↓
END FOR
  ↓
END: [Message delivered]
```

---

## 6. Collision Detection Flow

```
START: [Check Collision Risk]
  ↓
[Calculate future position (1s ahead)]
• future_x = x + vx × 1.0
• future_y = y + vy × 1.0
  ↓
FOR EACH neighbor within 300px:
  ↓
  [Calculate neighbor future position]
  ↓
  [future_distance = distance(future positions)]
  ↓
  [future_distance < 30px?] ──NO──> [Next neighbor]
  ↓ YES
  [Calculate time-to-collision]
  • TTC = current_distance / relative_speed
  ↓
  [TTC < 2.0s?] ──NO──> [Skip warning]
  ↓ YES
  ┌──────────────────────┐
  │ COLLISION IMMINENT   │
  └──────────────────────┘
  ↓
  [Broadcast collision_warning]
  • priority = HIGH
  • TTC, predicted_distance
  ↓
  [Take evasive action:]
  • speed ×= 0.8 (reduce 20%)
  • attempt lane change
  ↓
  [Log warning]
  ↓
END FOR
  ↓
END
```

---

## 7. Lane Change Safety Flow

```
START: [Request Lane Change]
  ↓
[Broadcast lane_change_intent]
• current_lane
• target_lane
• speed
  ↓
[Wait 100ms for responses]
  ↓
┌─────────────────────────────┐
│ SAFETY CHECK                │
└─────────────────────────────┘
  ↓
[Calculate target position]
  ↓
FOR EACH vehicle in target lane:
  ↓
  [On same road?] ──NO──> [Skip]
  ↓ YES
  [Calculate distance]
  ↓
  [Is ahead of me?]
    ↓ YES                ↓ NO
    [dist < 50px?]       [dist < 40px?]
      ↓ YES                ↓ YES
      UNSAFE              UNSAFE
      ↓                   ↓
      ABORT ←─────────────┘
      ↓
      END
  ↓ NO
  [Continue check]
END FOR
  ↓
[All checks passed?] ──NO──> [ABORT]
  ↓ YES
┌─────────────────────────────┐
│ EXECUTE LANE CHANGE         │
└─────────────────────────────┘
  ↓
[Set target_lane]
  ↓
[Set is_changing_lane = TRUE]
  ↓
[Gradual movement over 2 seconds]
  ↓
END: [Lane change complete]
```

---

## 8. Cluster Formation & Merging Flow

```
START
  ↓
┌─────────────────────────────┐
│ PHASE 1: Initial Clustering │
└─────────────────────────────┘
  ↓
FOR EACH vehicle:
  ↓
  [Already in cluster?] ──YES──> [Skip]
  ↓ NO
  [Find nearby compatible vehicles:]
  • Distance < 450px
  • Speed diff < 15 m/s
  • Direction diff < 57°
  ↓
  [Found ≥ 2 compatible?] ──NO──> [Skip]
  ↓ YES
  [Create new cluster]
  • Add vehicle + compatible neighbors
  • Calculate centroid
  • Elect leader
  ↓
END FOR
  ↓
┌─────────────────────────────┐
│ PHASE 2: Merge Overlapping  │
└─────────────────────────────┘
  ↓
FOR EACH cluster pair:
  ↓
  [Calculate leader distance]
  ↓
  [Distance < 450px?] ──NO──> [Next pair]
  ↓ YES
  [Count shared members]
  (within 250px of other leader)
  ↓
  [Calculate overlap ratio]
  = shared / cluster2_size
  ↓
  [overlap > 30% OR distance < 350px?]
    ↓ YES              ↓ NO
    MERGE             [Next pair]
    ↓
    [Combine members]
    ↓
    [Update assignments]
    ↓
    [Remove cluster2]
    ↓
END FOR
  ↓
[Update cluster stats]
  ↓
END
```

---

## 9. Vehicle Movement & Road Following Flow

```
START: [Update Position]
  ↓
┌─────────────────────────────┐
│ STEP 1: Traffic Light       │
└─────────────────────────────┘
  ↓
[At intersection?] ──NO──> [Skip check]
  ↓ YES                  ↓
[Light = RED?] ──NO──> ──┘
  ↓ YES
[Is emergency?] ──YES──> [Ignore light]
  ↓ NO
[Distance to stop line < 20px?]
  ↓ YES
  [BRAKE: speed -= 10 × dt]
  ↓
  [Speed = 0?] ──YES──> STOP → END
  ↓ NO
┌─────────────────────────────┐
│ STEP 2: Road Following      │
└─────────────────────────────┘
  ↓
[Get current road]
  ↓
[Calculate road direction]
  ↓
[Calculate lane offset]
• offset = (lane - lanes/2) × lane_width
• perpendicular to road direction
  ↓
┌─────────────────────────────┐
│ STEP 3: Position Update     │
└─────────────────────────────┘
  ↓
[distance = speed × dt]
  ↓
[x += cos(direction) × distance + offset_x]
[y += sin(direction) × distance + offset_y]
  ↓
┌─────────────────────────────┐
│ STEP 4: Road Transition     │
└─────────────────────────────┘
  ↓
[Distance to road end < 10px?]
  ↓ YES              ↓ NO
  [Select next road] [Continue on road]
  ↓                  ↓
  [Update road_id]   ┌─────────────────────────────┐
  ↓                  │ STEP 5: Lane Change         │
  ↓                  └─────────────────────────────┘
  ↓                    ↓
  └───────────────────>[Is changing lane?] ──NO──> END
                        ↓ YES
                       [Progress = time / 2.0s]
                        ↓
                       [Progress ≥ 1.0?]
                        ↓ YES          ↓ NO
                       [Complete]    [Gradual shift]
                        ↓              ↓
                       [current_lane = target_lane]
                        ↓
                       END
```

---

## 10. Boundary Node Election Flow

```
START
  ↓
[Get cluster centroid]
  ↓
[Find neighboring clusters]
(distance < 600px)
  ↓
[Any neighbors?] ──NO──> [No boundaries needed] → END
  ↓ YES
FOR EACH neighbor_cluster:
  ↓
  [Score candidates in my cluster:]
  ↓
  FOR EACH member:
    ↓
    [Exclude malicious (trust < 0.6)]
    ↓
    [Calculate Boundary Score:]
    • Trust: 40%
    • Proximity to neighbor: 35%
    • Connectivity: 25%
    ↓
    [Add to candidates]
    ↓
  END FOR
  ↓
  [Sort by score DESC]
  ↓
  [Select best candidate]
  ↓
  [boundary_nodes[neighbor_id] = best_candidate]
  ↓
END FOR
  ↓
[Update cluster.boundary_nodes]
  ↓
LOG: "X boundary nodes for Y neighbors"
  ↓
END
```

---

## System Integration Flow

```
MAIN SIMULATION LOOP:
  ↓
[Initialize Network]
• 11×11 grid + highway
• 97 intersections, 350 roads
• 150 vehicles
  ↓
FOR EACH timestep (dt = 0.1s):
  ↓
  ┌─────────────────────────────┐
  │ 1. MOBILITY                 │
  └─────────────────────────────┘
  FOR EACH vehicle:
    [Update position (road follow)]
    [Check collisions]
    [Process lane changes]
  END FOR
  ↓
  ┌─────────────────────────────┐
  │ 2. NEIGHBOR DISCOVERY       │
  └─────────────────────────────┘
  FOR EACH vehicle:
    [Find neighbors (DSRC 250px)]
  END FOR
  ↓
  ┌─────────────────────────────┐
  │ 3. CLUSTERING               │
  └─────────────────────────────┘
  [Form clusters (proximity/speed/direction)]
  [Merge overlapping clusters]
  ↓
  ┌─────────────────────────────┐
  │ 4. ELECTIONS                │
  └─────────────────────────────┘
  FOR EACH new cluster:
    [Elect leader (Raft)]
    [Elect co-leader]
  END FOR
  ↓
  ┌─────────────────────────────┐
  │ 5. ROLE ASSIGNMENT          │
  └─────────────────────────────┘
  FOR EACH cluster:
    [Elect relay nodes]
    [Elect boundary nodes]
  END FOR
  ↓
  ┌─────────────────────────────┐
  │ 6. SECURITY (PoA)           │
  └─────────────────────────────┘
  [Authorities vote on suspicious nodes]
  [Flag malicious (100% detection)]
  ↓
  ┌─────────────────────────────┐
  │ 7. V2V COMMUNICATION        │
  └─────────────────────────────┘
  [Broadcast safety messages]
  [Multi-hop relay forwarding]
  [Inter-cluster via boundaries]
  ↓
  ┌─────────────────────────────┐
  │ 8. FAILURE HANDLING         │
  └─────────────────────────────┘
  [Check leader failures]
  [Co-leader succession]
  [Re-elections if needed]
  ↓
  ┌─────────────────────────────┐
  │ 9. DATA CAPTURE             │
  └─────────────────────────────┘
  [Export frame (roles, positions, stats)]
  ↓
END FOR (120 seconds)
  ↓
[Generate visualization JSON]
  ↓
END SIMULATION
```

---

## Complexity Analysis Summary

| Algorithm | Time Complexity | Space Complexity | Notes |
|-----------|----------------|------------------|-------|
| Leader Election | O(n log n) | O(n) | Sort candidates |
| PoA Detection | O(a × m) | O(m) | a=authorities, m=monitored |
| Relay Selection | O(n × m) | O(n) | Greedy set cover |
| Boundary Election | O(c × n) | O(c) | c=clusters |
| V2V Broadcast | O(n) | O(1) | Direct neighbors |
| Collision Detection | O(n²) | O(1) | All pairs check |
| Clustering | O(n²) | O(n) | Pairwise distance |
| Cluster Merging | O(c²) | O(c) | Cluster pairs |
| Road Following | O(1) | O(1) | Single vehicle |
| Lane Change | O(n) | O(1) | Check target lane |

**Overall System per Timestep: O(n²)**
- Dominated by collision detection and clustering
- n = 150 vehicles typical
- Optimizable with spatial indexing (KD-Tree) → O(n log n)

---

*Generated from actual implementation in city_traffic_simulator.py*
*Use these flowcharts in your report's "Algorithm Design" section*
