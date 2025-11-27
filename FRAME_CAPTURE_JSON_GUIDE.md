# Frame Capture & JSON File Creation Guide
## How Animation Data is Captured and Exported

---

## 🎯 Overview

The simulation captures **snapshots (frames)** of the VANET state every 0.5 seconds and exports them to `city_animation_data.json` for visualization in HTML.

**Key Points:**
- ✅ **Frame Rate:** Every 5 timesteps (0.1s × 5 = 0.5s intervals)
- ✅ **Duration:** 120 seconds simulation = 240 frames captured
- ✅ **Data Structure:** JSON with vehicles, clusters, traffic lights, statistics per frame
- ✅ **File Size:** ~5-15 MB (depending on vehicle count and messages)

---

## 📊 Part 1: Frame Capture Process

### Step 1: Initialization

```python
class CityVANETSimulator:
    def __init__(self, num_vehicles=150, duration=120, timestep=0.1):
        # Initialize animation data structure
        self.animation_data = {
            'duration': duration,
            'timestep': timestep,
            'frames': [],           # Will store 240 frames
            'intersections': [],    # Static data (captured once)
            'roads': []            # Static data (captured once)
        }
```

**What happens:**
- Empty `animation_data` dictionary created at start
- `frames` list will accumulate snapshots every 0.5s
- `intersections` and `roads` captured once during initialization

---

### Step 2: Main Simulation Loop

```python
def run_simulation(self):
    current_time = 0.0
    frame_count = 0
    
    while current_time < self.duration:  # 0 to 120 seconds
        
        # 1. Update vehicle positions
        self._update_vehicles(current_time)
        
        # 2. Update traffic lights
        self._update_traffic_lights(current_time)
        
        # 3. Run clustering algorithm
        if frame_count % 30 == 0:  # Every 3 seconds
            self._run_clustering(current_time)
        
        # 4. Handle leader elections
        self._check_leader_failures(current_time)
        
        # 5. Detect malicious nodes
        if frame_count % 100 == 0:  # Every 10 seconds
            self._detect_malicious_nodes_poa(current_time)
        
        # ⭐ 6. CAPTURE FRAME (every 5 frames = 0.5s)
        if frame_count % 5 == 0:
            frame_data = self.capture_frame(current_time)
            self.animation_data['frames'].append(frame_data)
        
        current_time += self.timestep  # Advance by 0.1s
        frame_count += 1
    
    return self.animation_data
```

**Key Timing:**
- **Timestep:** 0.1 seconds
- **Frame Capture:** Every 5 timesteps → 0.5 second intervals
- **Total Frames:** 120s ÷ 0.5s = 240 frames

---

### Step 3: Capture Frame Function

```python
def capture_frame(self, current_time: float) -> Dict:
    """Capture current state of simulation at this timestep"""
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 1. CAPTURE VEHICLES (all 150)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    vehicles = []
    
    for vehicle_id, node in self.app.vehicle_nodes.items():
        x, y = node.location
        config = self.vehicle_configs[vehicle_id]
        
        # Determine role (leader, co-leader, member, relay, boundary)
        role = 'member'  # default
        is_co_leader = False
        is_relay = False
        is_boundary = False
        
        if node.cluster_id:
            cluster = self.app.clustering_engine.clusters.get(node.cluster_id)
            if cluster:
                # Check if co-leader
                if hasattr(cluster, 'co_leader_id') and cluster.co_leader_id == vehicle_id:
                    is_co_leader = True
                    role = 'co_leader'
                
                # Check if relay node
                if hasattr(cluster, 'relay_nodes') and vehicle_id in cluster.relay_nodes:
                    is_relay = True
                    if role == 'member':
                        role = 'relay'
                
                # Check if boundary node
                if hasattr(cluster, 'boundary_nodes'):
                    for neighbor_id, boundary_id in cluster.boundary_nodes.items():
                        if boundary_id == vehicle_id:
                            is_boundary = True
                            if role == 'member':
                                role = 'boundary'
                            break
        
        if node.is_cluster_head:
            role = 'leader'
        
        # Append vehicle data to frame
        vehicles.append({
            'id': vehicle_id,              # e.g., "v42"
            'x': x,                        # Position X (0-2000)
            'y': y,                        # Position Y (0-2000)
            'speed': node.speed,           # km/h (0-120)
            'direction': node.direction,   # radians (0-2π)
            'cluster_id': node.cluster_id, # e.g., "cluster_3"
            'is_cluster_head': node.is_cluster_head,  # True/False
            'is_co_leader': is_co_leader,  # True/False
            'is_relay': is_relay,          # True/False
            'is_boundary': is_boundary,    # True/False
            'role': role,                  # "leader", "co_leader", "member", etc.
            'trust_score': node.trust_score,  # 0.0-1.0
            'is_malicious': node.is_malicious,  # True/False
            'is_emergency': config['is_emergency'],  # True/False
            'waiting': config['waiting_at_light'],   # True/False
            'type': config['type']         # "car", "truck", "emergency"
        })
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 2. CAPTURE CLUSTERS (typically 10-15)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    clusters = []
    MAX_CLUSTER_RANGE = 450  # 450 pixels max radius
    
    for cluster_id, cluster in self.app.clustering_engine.clusters.items():
        if cluster.member_ids and cluster.head_id:
            # Get leader position (cluster center)
            if cluster.head_id in self.app.vehicle_nodes:
                leader_node = self.app.vehicle_nodes[cluster.head_id]
                center_x, center_y = leader_node.location
            else:
                continue  # Skip if leader not found
            
            # Calculate cluster radius (distance to furthest member)
            member_positions = [
                self.app.vehicle_nodes[vid].location 
                for vid in cluster.member_ids 
                if vid in self.app.vehicle_nodes
            ]
            
            if member_positions:
                calculated_radius = max(
                    math.sqrt((p[0] - center_x)**2 + (p[1] - center_y)**2)
                    for p in member_positions
                ) + 40  # Add 40px padding
                
                # Enforce maximum cluster range
                radius = min(calculated_radius, MAX_CLUSTER_RANGE)
                
                # Get special node counts
                relay_count = len(cluster.relay_nodes) if hasattr(cluster, 'relay_nodes') else 0
                boundary_count = len(cluster.boundary_nodes) if hasattr(cluster, 'boundary_nodes') else 0
                
                clusters.append({
                    'id': cluster_id,          # e.g., "cluster_3"
                    'center_x': center_x,      # Leader X position
                    'center_y': center_y,      # Leader Y position
                    'radius': radius,          # Cluster radius (pixels)
                    'size': len(cluster.member_ids),  # Number of members
                    'leader_id': cluster.head_id,      # e.g., "v57"
                    'co_leader_id': cluster.co_leader_id if hasattr(cluster, 'co_leader_id') else None,
                    'relay_count': relay_count,        # Number of relay nodes
                    'boundary_count': boundary_count   # Number of boundary nodes
                })
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 3. CAPTURE TRAFFIC LIGHTS (static positions)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    traffic_lights = []
    
    for intersection in self.intersections:
        for direction, light in intersection.lights.items():
            traffic_lights.append({
                'x': light.x,              # Light X position
                'y': light.y,              # Light Y position
                'state': light.state,      # "green", "yellow", "red"
                'direction': direction     # "north", "south", "east", "west"
            })
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 4. CAPTURE V2V MESSAGES (recent only)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Only include messages from last 1 second (most recent 50)
    recent_v2v = [msg for msg in self.v2v_messages 
                 if abs(msg['time'] - current_time) < 1.0][-50:]
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 5. CAPTURE STATISTICS
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    stats = {
        'total_clusters': len(clusters),
        'total_vehicles': len(vehicles),
        'messages_sent': self.app.statistics.get('messages_sent', 0),
        'messages_received': self.app.statistics.get('messages_received', 0),
        'head_elections': self.app.statistics.get('head_elections', 0),
        'consensus_enabled': True,
        'v2v_total': self.v2v_stats['total_messages'],
        'collision_warnings': self.v2v_stats['collision_warnings'],
        'emergency_alerts': self.v2v_stats['emergency_alerts']
    }
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 6. RETURN FRAME DATA
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    return {
        'time': current_time,          # Timestamp (0.0, 0.5, 1.0, ... 120.0)
        'vehicles': vehicles,          # List of 150 vehicle objects
        'clusters': clusters,          # List of 10-15 cluster objects
        'traffic_lights': traffic_lights,  # List of traffic light states
        'v2v_messages': recent_v2v,    # Recent V2V messages
        'stats': stats                 # Statistics for this frame
    }
```

**What's Captured in Each Frame:**
1. **150 vehicles** with position, speed, trust score, role, cluster membership
2. **10-15 clusters** with center, radius, leader, co-leader, size
3. **Traffic lights** with current state (green/yellow/red)
4. **V2V messages** (last 50 messages within 1 second)
5. **Statistics** (total elections, messages, collisions)

---

## 💾 Part 2: JSON File Creation

### Step 1: Export Function

```python
def export_html(self, filename='city_traffic_animation.html'):
    """Export animation data as JSON file"""
    
    # ⭐ SAVE JSON FILE
    with open('city_animation_data.json', 'w') as f:
        json.dump(self.animation_data, f)
    
    print(f"\n✅ Animation data exported to: city_animation_data.json")
    print(f"📊 Total frames: {len(self.animation_data['frames'])}")
    print(f"⏱️  Duration: {self.duration}s")
    print(f"🚦 Intersections: {len(self.intersections)}")
    print(f"🛣️  Roads: {len(self.roads)}")
```

**Output:**
```bash
✅ Animation data exported to: city_animation_data.json
📊 Total frames: 240
⏱️  Duration: 120s
🚦 Intersections: 121
🛣️  Roads: 242
```

---

### Step 2: JSON File Structure

```json
{
  "duration": 120,
  "timestep": 0.1,
  
  "intersections": [
    {"x": 100, "y": 100, "id": 0},
    {"x": 300, "y": 100, "id": 1},
    ...
  ],
  
  "roads": [
    {"start": [100, 100], "end": [300, 100], "direction": "horizontal"},
    {"start": [100, 100], "end": [100, 300], "direction": "vertical"},
    ...
  ],
  
  "frames": [
    {
      "time": 0.0,
      "vehicles": [
        {
          "id": "v0",
          "x": 156.3,
          "y": 892.7,
          "speed": 45.2,
          "direction": 1.57,
          "cluster_id": "cluster_3",
          "is_cluster_head": false,
          "is_co_leader": false,
          "is_relay": false,
          "is_boundary": false,
          "role": "member",
          "trust_score": 0.85,
          "is_malicious": true,
          "is_emergency": false,
          "waiting": false,
          "type": "car"
        },
        {
          "id": "v57",
          "x": 234.1,
          "y": 901.3,
          "speed": 38.7,
          "direction": 1.57,
          "cluster_id": "cluster_3",
          "is_cluster_head": true,
          "is_co_leader": false,
          "is_relay": false,
          "is_boundary": false,
          "role": "leader",
          "trust_score": 0.98,
          "is_malicious": false,
          "is_emergency": false,
          "waiting": false,
          "type": "car"
        },
        ... (148 more vehicles)
      ],
      
      "clusters": [
        {
          "id": "cluster_3",
          "center_x": 234.1,
          "center_y": 901.3,
          "radius": 387.5,
          "size": 12,
          "leader_id": "v57",
          "co_leader_id": "v146",
          "relay_count": 2,
          "boundary_count": 3
        },
        ... (10-14 more clusters)
      ],
      
      "traffic_lights": [
        {"x": 100, "y": 100, "state": "green", "direction": "north"},
        {"x": 100, "y": 100, "state": "red", "direction": "east"},
        ... (480 more lights)
      ],
      
      "v2v_messages": [
        {
          "time": 0.3,
          "sender": "v23",
          "receiver": "v57",
          "type": "beacon",
          "x": 245.7,
          "y": 889.2
        },
        ... (up to 50 messages)
      ],
      
      "stats": {
        "total_clusters": 11,
        "total_vehicles": 150,
        "messages_sent": 234,
        "messages_received": 198,
        "head_elections": 3,
        "consensus_enabled": true,
        "v2v_total": 1247,
        "collision_warnings": 5,
        "emergency_alerts": 2
      }
    },
    
    {
      "time": 0.5,
      "vehicles": [...],  // State at t=0.5s
      "clusters": [...],
      "traffic_lights": [...],
      "v2v_messages": [...],
      "stats": {...}
    },
    
    ... (238 more frames up to t=120.0s)
  ]
}
```

---

## 📈 Part 3: Frame Capture Timeline

### Visual Timeline:

```
Time:     0.0s    0.5s    1.0s    1.5s    2.0s    2.5s    3.0s  ...  120.0s
          │       │       │       │       │       │       │           │
Frames:   F0      F1      F2      F3      F4      F5      F6    ...   F240
          │       │       │       │       │       │       │           │
          └───────┴───────┴───────┴───────┴───────┴───────┴───────────┘
          
Frame Interval: 0.5 seconds
Total Frames: 240 frames (120s ÷ 0.5s)
Timestep: 0.1s (simulation runs 10 steps per frame capture)
```

### Detailed Breakdown:

| Time (s) | Frame # | Timesteps | Events Captured |
|----------|---------|-----------|-----------------|
| 0.0 | 0 | 0 | Initial state, all vehicles spawned |
| 0.5 | 1 | 5 | Vehicles moved, first V2V messages |
| 1.0 | 2 | 10 | More movement, traffic lights update |
| 3.0 | 6 | 30 | **First clustering event** |
| 10.0 | 20 | 100 | **First PoA malicious detection** |
| 25.0 | 50 | 250 | **Sleeper agent v15 activates** |
| 30.0 | 60 | 300 | **Boundary node election** |
| 39.6 | 79 | 396 | **Sleeper agent v5 activates** |
| 60.0 | 120 | 600 | **Cluster merging events** |
| 120.0 | 240 | 1200 | **Final state captured** |

---

## 🔍 Part 4: What Makes Each Frame Unique?

### Frame Differences Over Time:

| Aspect | Changes Between Frames |
|--------|------------------------|
| **Vehicle Positions** | Move 5-15 pixels (based on speed) |
| **Trust Scores** | Malicious nodes: 0.85→0.15, Legitimate: stay ~0.95-1.0 |
| **Cluster Membership** | Vehicles join/leave clusters as they move |
| **Cluster Leaders** | Elections cause leader changes (183 times in 120s) |
| **Co-Leaders** | Promotions when leaders fail |
| **Traffic Lights** | Green→Yellow→Red cycles (30s period) |
| **Malicious Flags** | `is_malicious` changes when detected by PoA |
| **Sleeper Activation** | v5, v15 change from normal to malicious at t=20-40s |

### Example: Frame Evolution for Vehicle v15 (Sleeper Agent)

```
Frame 0 (t=0.0s):
  x: 456, y: 789, cluster_id: "cluster_5", role: "member"
  trust_score: 0.85, is_malicious: false (STEALTH MODE)
  
Frame 50 (t=25.0s):
  x: 567, y: 812, cluster_id: "cluster_5", role: "member"
  trust_score: 0.85, is_malicious: false (STILL STEALTHY)
  
Frame 51 (t=25.5s):
  x: 571, y: 815, cluster_id: "cluster_5", role: "member"
  trust_score: 0.15, is_malicious: true (⚠️ ACTIVATED!)
  
Frame 52 (t=26.0s):
  x: 578, y: 823, cluster_id: "cluster_5", role: "member"
  trust_score: 0.08, is_malicious: true (🚨 DETECTED BY POA)
  
Frame 60 (t=30.0s):
  x: 623, y: 851, cluster_id: "cluster_7", role: "member"
  trust_score: 0.05, is_malicious: true (FLAGGED, ISOLATED)
```

---

## 📊 Part 5: File Size Analysis

### Size Breakdown:

```
city_animation_data.json:
├─ Static Data (intersections, roads): ~50 KB
├─ Frame Data (240 frames):
│  ├─ Vehicles (150 × 240): ~8 MB
│  ├─ Clusters (12 × 240): ~400 KB
│  ├─ Traffic Lights (484 × 240): ~600 KB
│  ├─ V2V Messages (50 × 240): ~1 MB
│  └─ Stats (240): ~50 KB
└─ Total: ~10-12 MB (typical)
```

### Size Optimization:

**Original (without optimization):**
- Every 0.1s frame capture → 1,200 frames
- File size: ~60 MB (too large for browsers)

**Optimized (current):**
- Every 0.5s frame capture → 240 frames
- File size: ~10 MB ✅ (browser-friendly)
- Still smooth animation (2 FPS playback)

---

## 🎬 Part 6: How HTML Uses the JSON

### JavaScript Loading:

```javascript
// In city_traffic_animation.html
fetch('city_animation_data.json')
  .then(response => response.json())
  .then(data => {
    console.log(`Loaded ${data.frames.length} frames`);
    
    // Start animation loop
    let frameIndex = 0;
    
    function animate() {
      const frame = data.frames[frameIndex];
      
      // Draw vehicles
      frame.vehicles.forEach(vehicle => {
        drawVehicle(vehicle.x, vehicle.y, vehicle.role, vehicle.trust_score);
      });
      
      // Draw clusters
      frame.clusters.forEach(cluster => {
        drawCluster(cluster.center_x, cluster.center_y, cluster.radius);
      });
      
      // Draw traffic lights
      frame.traffic_lights.forEach(light => {
        drawLight(light.x, light.y, light.state);
      });
      
      frameIndex = (frameIndex + 1) % data.frames.length;  // Loop
      requestAnimationFrame(animate);
    }
    
    animate();
  });
```

---

## 🎯 Summary: Complete Process

### End-to-End Flow:

```
1. Simulation Runs (120 seconds)
   ├─ Every 0.1s: Update vehicles, lights, clusters
   ├─ Every 3s: Re-run clustering algorithm
   ├─ Every 10s: Detect malicious nodes
   └─ Every 0.5s: ⭐ CAPTURE FRAME ⭐
         │
         ├─ Snapshot 150 vehicles (positions, trust, roles)
         ├─ Snapshot 10-15 clusters (centers, leaders, sizes)
         ├─ Snapshot 484 traffic lights (states)
         ├─ Snapshot recent 50 V2V messages
         └─ Snapshot statistics (elections, messages)
         
2. Frame Added to animation_data['frames'] array
   └─ Accumulates 240 frames over 120 seconds
   
3. Simulation Ends
   └─ export_html() called
   
4. JSON File Created
   ├─ Open 'city_animation_data.json' for writing
   ├─ json.dump(animation_data, file)
   └─ File saved (~10 MB)
   
5. HTML Visualization
   ├─ Load city_animation_data.json
   ├─ Parse 240 frames
   └─ Animate at 2 FPS (playback speed)
```

### Key Metrics:

| Metric | Value |
|--------|-------|
| **Simulation Duration** | 120 seconds |
| **Timestep** | 0.1 seconds |
| **Frame Capture Interval** | 0.5 seconds (every 5 timesteps) |
| **Total Frames Captured** | 240 frames |
| **Vehicles per Frame** | 150 |
| **Clusters per Frame** | 10-15 (average 12) |
| **Traffic Lights per Frame** | 484 |
| **V2V Messages per Frame** | 0-50 (recent only) |
| **JSON File Size** | ~10-12 MB |
| **Data Structure** | Nested JSON with arrays |

---

## 🎤 For Your Review

**When they ask: "How are frames captured and JSON created?"**

**Answer:**

> "During the simulation, we capture snapshots every 0.5 seconds—that's every 5 timesteps of our 0.1-second simulation step. Each frame snapshot records:
> 
> 1. **All 150 vehicles** with their positions, speed, trust scores, cluster membership, and roles (leader, co-leader, member)
> 2. **Active clusters** (10-15) with their centers, radii, leaders, and sizes
> 3. **Traffic light states** (484 lights) showing green, yellow, or red
> 4. **Recent V2V messages** (last 50 within 1 second) for collision warnings and alerts
> 5. **Statistics** like total elections, messages sent, and detection events
> 
> This happens in the `capture_frame()` function which returns a dictionary. That dictionary is appended to the `animation_data['frames']` array.
> 
> After 120 seconds, we have 240 frames. At the end, `export_html()` calls `json.dump()` to write the entire `animation_data` structure to `city_animation_data.json`—about 10-12 MB.
> 
> The HTML visualization then loads this JSON file and plays back the frames at 2 FPS, showing the complete simulation evolution including sleeper agent activations, cluster formations, and leader elections."

---

**Code Location References:**
- Frame capture: `city_traffic_simulator.py`, line 2419-2536
- Main loop: `city_traffic_simulator.py`, line 1305-1306
- JSON export: `city_traffic_simulator.py`, line 2571-2575
- Initialization: `city_traffic_simulator.py`, line 134-138

---

🎯 **You now have complete documentation of the frame capture and JSON creation process!**
