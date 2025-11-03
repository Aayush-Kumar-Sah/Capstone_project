# Enhanced Cluster Visualization Guide

## Overview
This enhanced visualization clearly distinguishes all cluster node roles with unique colors, symbols, and cluster circles centered on the leader position.

## How to View

Open `enhanced_cluster_visualization.html` in your web browser to see the improved visualization.

## Visual Features

### 🎨 Node Roles & Colors

#### Leadership Nodes
- **🟡 Leader (♕)** - Gold circle with white border and crown symbol
  - Positioned at the CENTER of the cluster circle
  - Connects to all cluster members with lines
  - Most important node in the cluster

- **🔴 Co-Leader (★)** - Red circle with white border and star symbol
  - Backup leader for failover
  - Takes over if leader fails
  - Second most important node

#### Special Function Nodes
- **🔵 Relay Node (⚡)** - Cyan circle with lightning symbol
  - Enables multi-hop communication
  - Forwards messages to out-of-range members
  - Critical for cluster-wide coverage

- **🟣 Boundary Node (◈)** - Pink circle with diamond symbol
  - Gateway for inter-cluster communication
  - Positioned at cluster edges
  - Connects to neighboring clusters

#### Regular Nodes
- **🟢 Member** - Green circle with cluster color border
  - Regular cluster member
  - Receives messages via leader or relays

- **🔴 Emergency Vehicle** - Red circle
  - Priority vehicle
  - Broadcasts emergency alerts

- **🟣 Malicious Node** - Purple circle
  - Detected by PoA consensus
  - Low trust score

### 🎯 Cluster Circles

- **Centered on Leader**: All cluster circles are centered on the leader's position (not geometric center)
- **Dashed Border**: Semi-transparent dashed circle in cluster color
- **Size**: Maximum 450 pixels radius (3 blocks diameter)
- **Label**: Shows cluster ID and member count above the circle
- **Connection Lines**: Faint lines from leader to all members

### 📊 Real-Time Statistics

The visualization displays:
- **Frame Count**: Current frame / Total frames
- **Simulation Time**: Current time in seconds
- **Total Clusters**: Number of active clusters
- **Leader Count**: Number of cluster heads
- **Co-Leader Count**: Number of backup leaders
- **Relay Nodes**: Total relay nodes across all clusters
- **Boundary Nodes**: Total boundary nodes for inter-cluster communication

## Latest Simulation Results

```
🗳️  Cluster Statistics:
   Total head elections: 371
   Malicious nodes detected: 15/15 (100% detection rate)
   
📡 V2V Communication:
   Total messages: 12,943
   Collision warnings: 4,693
   Emergency alerts: 3,070
   
🔁 Multi-Hop Relay System:
   Total relay nodes: 9
   Relayed messages: 241
   Average hops: 1.19
   
🔷 Inter-Cluster Communication:
   Total boundary nodes: 54
   Clusters with boundaries: 26
   Inter-cluster messages: 1,030
   Average boundaries per cluster: 2.1
```

## Key Improvements

### 1. **Leader-Centered Clusters** ✅
- Clusters are now centered on the leader's actual position
- More accurate representation of cluster structure
- Shows leader's central role in the cluster

### 2. **Clear Role Distinction** ✅
- Each node role has unique color and symbol
- Easy to identify leaders, co-leaders, relays, and boundaries at a glance
- Border colors match cluster color for members

### 3. **Enhanced Legend** ✅
- Comprehensive legend on the right side
- Shows all node types with visual examples
- Organized by category (Leadership, Special Roles, Regular)

### 4. **Statistics Dashboard** ✅
- Real-time counts of each node type
- Track cluster formation and role assignments
- Monitor system performance

## Controls

- **⏯️ Play/Pause**: Start/stop animation
- **🔄 Reset**: Return to first frame
- **⏮️ Prev**: Previous frame
- **⏭️ Next**: Next frame
- **Speed Slider**: Adjust playback speed (0.25x to 2x)

## Visual Hierarchy

From most to least important:
1. **Leader** - Gold with crown (♕) - Center of cluster
2. **Co-Leader** - Red with star (★) - Backup leader
3. **Relay Node** - Cyan with lightning (⚡) - Multi-hop communication
4. **Boundary Node** - Pink with diamond (◈) - Inter-cluster gateway
5. **Member** - Green - Regular node
6. **Emergency** - Red - Priority vehicle
7. **Malicious** - Purple - Detected threat

## Technical Details

### Cluster Circle Calculation
```python
# Centered on leader position
leader_x, leader_y = leader_node.location
center_x, center_y = leader_x, leader_y

# Radius from leader to furthest member
radius = max(distance(leader, member) for member in cluster)
radius = min(radius, MAX_CLUSTER_RANGE)  # Cap at 450px
```

### Role Determination
```python
if node.is_cluster_head:
    role = 'leader'  # Gold with crown
elif node.id == cluster.co_leader_id:
    role = 'co_leader'  # Red with star
elif node.id in cluster.relay_nodes:
    role = 'relay'  # Cyan with lightning
elif node.id in cluster.boundary_nodes.values():
    role = 'boundary'  # Pink with diamond
else:
    role = 'member'  # Green
```

## Files

- `enhanced_cluster_visualization.html` - New enhanced visualization
- `city_animation_data.json` - Simulation data (updated with role information)
- `city_traffic_simulator.py` - Updated to export role data

## Next Steps

1. Open `enhanced_cluster_visualization.html` in your browser
2. Click Play to start the animation
3. Observe how roles change over time
4. Watch leaders maintain central positions
5. See relay and boundary nodes elected dynamically

## Notes

- Cluster circles are now **leader-centric** instead of geometric center
- Leaders are always visible at the exact center of their cluster circle
- All special roles (co-leader, relay, boundary) are clearly marked
- Colors are consistent across frames for the same cluster
- Real-time statistics update every frame

Enjoy the enhanced visualization! 🚗📡🎨
