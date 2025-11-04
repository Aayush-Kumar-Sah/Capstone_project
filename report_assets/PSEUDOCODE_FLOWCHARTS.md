# VANET System - Pseudocode Flowcharts

## 1. Multi-Metric Raft Leader Election Flow

```
START
  ↓
[Get Cluster Members]
  ↓
FOR EACH member:
  ↓
  [Check Trust Score > 0.5?] ──NO──> [Skip member]
  ↓ YES
  [Calculate 5 Metrics:]
  • Trust (30%)
  • Connectivity (25%)
  • Stability (20%)
  • Centrality (15%)
  • Tenure (10%)
  ↓
  [Composite Score = Σ weighted metrics]
  ↓
  [Add to candidates list]
  ↓
END FOR
  ↓
[Sort candidates by score DESC]
  ↓
[Simulate Raft Voting:]
FOR EACH voter in cluster:
  ↓
  [Vote for top candidate]
  ↓
  [Apply trust weight to vote]
  ↓
END FOR
  ↓
[Winner = candidate with 51% votes]
  ↓
[Update cluster.head_id = winner]
  ↓
[Set winner.is_cluster_head = TRUE]
  ↓
END
```

---

## 2. Co-Leader Succession Flow

```
START: [Leader Failure Detected]
  ↓
[Is co-leader assigned?] ──NO──> [Trigger full re-election]
  ↓ YES                            ↓
[Is co-leader valid?]             [Run Raft election]
  • Trust > 0.5                    ↓
  • Not malicious                 [Elect new leader]
  • Still in cluster               ↓
  ↓ YES          ↓ NO              ↓
[PROMOTE]     [RE-ELECT]     [Elect co-leader]
  ↓              ↓                  ↓
[cluster.head_id = co_leader_id]   END
  ↓
[old_leader.is_cluster_head = FALSE]
  ↓
[new_leader.is_cluster_head = TRUE]
  ↓
[Elect new co-leader]
  ↓
END: [Succession complete - 0ms downtime]
```

---

## 3. PoA Malicious Detection Flow

```
START
  ↓
[Identify Authorities: trust > 0.8]
  ↓
FOR EACH authority:
  ↓
  [Get monitored nodes (cluster members)]
  ↓
  FOR EACH monitored_node:
    ↓
    [Calculate Suspicion Score:]
    • Trust < 0.4? → +0.3
    • Known malicious? → +0.5
    • Speed > 75 mph? → +0.2
    • Msg spam (>100)? → +0.2
    ↓
    [Suspicion > 0.5?] ──NO──> [Skip]
    ↓ YES
    [Cast vote against node]
    ↓
  END FOR
END FOR
  ↓
FOR EACH flagged_node:
  ↓
  [Count cluster authorities]
  ↓
  [Vote threshold = 30% of cluster authorities]
  ↓
  [Votes ≥ threshold?] ──NO──> [No action]
  ↓ YES
  [FLAG as malicious]
  ↓
  [Apply trust penalty: ×0.7]
  ↓
  [Is cluster head?] ──YES──> [Remove from leadership]
  ↓ NO                         ↓
END                          [Trigger re-election]
                               ↓
                              END
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
