#!/usr/bin/env python3
"""
Dynamic VANET Cluster Animation with Real Vehicle Movement

Creates an HTML animation showing vehicles actually moving along roads,
forming and leaving clusters dynamically.
"""

import json
import random
import math
from typing import List, Dict, Tuple
import sys
import os

# Add src to path
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.custom_vanet_appl import CustomVANETApplication
from src.clustering import ClusteringAlgorithm

class DynamicVehicleSimulator:
    """Simulates vehicles with realistic movement patterns"""
    
    def __init__(self, num_vehicles=20, duration=30, timestep=0.5):
        self.num_vehicles = num_vehicles
        self.duration = duration
        self.timestep = timestep
        self.app = CustomVANETApplication(ClusteringAlgorithm.MOBILITY_BASED)
        self.app.trust_enabled = True
        
        # Road network (simulated highway with lanes)
        self.road_lanes = [
            {'y': 200, 'direction': 1, 'speed': 25},   # Eastbound
            {'y': 250, 'direction': 1, 'speed': 30},   # Eastbound fast
            {'y': 350, 'direction': -1, 'speed': 27},  # Westbound
            {'y': 400, 'direction': -1, 'speed': 22},  # Westbound slow
        ]
        
        self.animation_data = {
            'frames': [],
            'vehicles': {},
            'metadata': {
                'duration': duration,
                'timestep': timestep,
                'num_vehicles': num_vehicles
            }
        }
        
    def initialize_vehicles(self):
        """Create vehicles with random positions and speeds"""
        vehicle_configs = []
        
        for i in range(self.num_vehicles):
            # Randomly assign to a lane
            lane = random.choice(self.road_lanes)
            
            # Random starting position
            x = random.uniform(0, 1000)
            y = lane['y']
            speed = lane['speed'] + random.uniform(-5, 5)
            direction = 0 if lane['direction'] > 0 else 180
            
            # Mark some as malicious
            is_malicious = (i % 7 == 0)  # ~14% malicious
            
            vehicle_id = f'v{i}'
            self.app.add_vehicle(
                vehicle_id=vehicle_id,
                x=x, y=y,
                speed=speed,
                direction=direction,
                lane_id=f'lane_{self.road_lanes.index(lane)}'
            )
            
            # Store initial config
            vehicle_configs.append({
                'id': vehicle_id,
                'lane_index': self.road_lanes.index(lane),
                'is_malicious': is_malicious,
                'color': '#ff4444' if is_malicious else '#44ff44'
            })
            
            if is_malicious:
                # Inject malicious behavior
                node = self.app.vehicle_nodes[vehicle_id]
                node.is_malicious = True
                node.trust_score = 0.3
        
        self.animation_data['vehicles'] = {
            vc['id']: vc for vc in vehicle_configs
        }
    
    def update_vehicle_positions(self, current_time: float):
        """Update all vehicle positions based on speed and direction"""
        for vehicle_id, node in self.app.vehicle_nodes.items():
            # Get current position
            x, y = node.location
            speed = node.speed
            direction = node.direction
            
            # Calculate new position
            # direction: 0 = East, 180 = West
            if direction < 90 or direction > 270:  # Eastbound
                dx = speed * self.timestep * 0.5  # Scale for visualization
            else:  # Westbound
                dx = -speed * self.timestep * 0.5
            
            # Update position
            new_x = x + dx
            
            # Wrap around at boundaries
            if new_x > 1000:
                new_x = 0
            elif new_x < 0:
                new_x = 1000
            
            # Update node location
            node.location = (new_x, y)
            node.last_update = current_time
            
            # Occasionally change speed (simulate traffic)
            if random.random() < 0.05:
                speed_change = random.uniform(-2, 2)
                node.speed = max(15, min(40, node.speed + speed_change))
    
    def run_simulation(self):
        """Run the full simulation and capture frames"""
        print(f"Initializing {self.num_vehicles} vehicles...")
        self.initialize_vehicles()
        
        current_time = 0.0
        frame_count = 0
        
        print(f"Running simulation for {self.duration} seconds...")
        
        while current_time < self.duration:
            # Update vehicle positions
            self.update_vehicle_positions(current_time)
            
            # Update clustering
            self.app.handle_timeStep(current_time)
            
            # Capture frame data
            frame_data = self.capture_frame(current_time)
            self.animation_data['frames'].append(frame_data)
            
            # Progress indicator
            if frame_count % 10 == 0:
                progress = (current_time / self.duration) * 100
                print(f"Progress: {progress:.1f}% - Time: {current_time:.1f}s - "
                      f"Clusters: {len(self.app.clustering_engine.clusters)}")
            
            current_time += self.timestep
            frame_count += 1
        
        print(f"Simulation complete! Captured {frame_count} frames")
        return self.animation_data
    
    def capture_frame(self, current_time: float) -> Dict:
        """Capture current state as a frame"""
        vehicles = []
        clusters = []
        
        # Capture vehicle positions and states
        for vehicle_id, node in self.app.vehicle_nodes.items():
            x, y = node.location
            
            vehicle_data = {
                'id': vehicle_id,
                'x': x,
                'y': y,
                'speed': node.speed,
                'direction': node.direction,
                'cluster_id': node.cluster_id if node.cluster_id else None,
                'is_cluster_head': node.is_cluster_head,
                'trust_score': node.trust_score,
                'is_malicious': node.is_malicious
            }
            vehicles.append(vehicle_data)
        
        # Capture cluster information
        for cluster_id, cluster in self.app.clustering_engine.clusters.items():
            if cluster.member_ids:
                # Calculate cluster center
                member_positions = [
                    self.app.vehicle_nodes[vid].location 
                    for vid in cluster.member_ids 
                    if vid in self.app.vehicle_nodes
                ]
                
                if member_positions:
                    center_x = sum(p[0] for p in member_positions) / len(member_positions)
                    center_y = sum(p[1] for p in member_positions) / len(member_positions)
                    
                    # Calculate radius (max distance from center)
                    radius = max(
                        math.sqrt((p[0] - center_x)**2 + (p[1] - center_y)**2)
                        for p in member_positions
                    ) + 50  # Add buffer
                    
                    cluster_data = {
                        'id': cluster_id,
                        'center_x': center_x,
                        'center_y': center_y,
                        'radius': radius,
                        'size': len(cluster.member_ids),
                        'head_id': cluster.head_id
                    }
                    clusters.append(cluster_data)
        
        return {
            'time': current_time,
            'vehicles': vehicles,
            'clusters': clusters,
            'stats': {
                'total_clusters': len(clusters),
                'total_vehicles': len(vehicles),
                'messages_sent': self.app.statistics.get('messages_sent', 0),
                'messages_received': self.app.statistics.get('messages_received', 0)
            }
        }
    
    def export_html(self, filename='dynamic_movement.html'):
        """Export animation as interactive HTML"""
        html_template = """<!DOCTYPE html>
<html>
<head>
    <title>Dynamic VANET Cluster Animation - Real Movement</title>
    <style>
        body {{
            margin: 0;
            padding: 20px;
            font-family: Arial, sans-serif;
            background: #1a1a1a;
            color: #ffffff;
        }}
        #container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        h1 {{
            text-align: center;
            color: #00ff88;
            margin-bottom: 10px;
        }}
        #canvas {{
            background: #2a2a2a;
            border: 2px solid #00ff88;
            border-radius: 8px;
            display: block;
            margin: 20px auto;
            box-shadow: 0 0 20px rgba(0,255,136,0.3);
        }}
        #controls {{
            background: #333;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
            box-shadow: 0 2px 10px rgba(0,0,0,0.5);
        }}
        .control-group {{
            margin: 15px 0;
            display: flex;
            align-items: center;
            gap: 15px;
        }}
        button {{
            background: #00ff88;
            color: #1a1a1a;
            border: none;
            padding: 12px 24px;
            border-radius: 6px;
            cursor: pointer;
            font-weight: bold;
            font-size: 14px;
            transition: all 0.3s;
        }}
        button:hover {{
            background: #00dd77;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,255,136,0.4);
        }}
        button:active {{
            transform: translateY(0);
        }}
        input[type="range"] {{
            flex: 1;
            height: 6px;
            border-radius: 3px;
            background: #555;
            outline: none;
        }}
        input[type="range"]::-webkit-slider-thumb {{
            -webkit-appearance: none;
            width: 18px;
            height: 18px;
            border-radius: 50%;
            background: #00ff88;
            cursor: pointer;
        }}
        #stats {{
            background: #333;
            padding: 20px;
            border-radius: 8px;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
        }}
        .stat-box {{
            background: #444;
            padding: 15px;
            border-radius: 6px;
            border-left: 4px solid #00ff88;
        }}
        .stat-label {{
            color: #aaa;
            font-size: 12px;
            text-transform: uppercase;
            margin-bottom: 5px;
        }}
        .stat-value {{
            color: #00ff88;
            font-size: 24px;
            font-weight: bold;
        }}
        .legend {{
            background: #333;
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
        }}
        .legend-item {{
            display: inline-flex;
            align-items: center;
            margin-right: 20px;
            margin-bottom: 10px;
        }}
        .legend-color {{
            width: 20px;
            height: 20px;
            border-radius: 50%;
            margin-right: 8px;
            border: 2px solid #fff;
        }}
        label {{
            color: #aaa;
            margin-right: 10px;
        }}
        .value-display {{
            color: #00ff88;
            font-weight: bold;
            min-width: 60px;
        }}
    </style>
</head>
<body>
    <div id="container">
        <h1>🚗 Dynamic VANET Cluster Animation - Real Vehicle Movement 🚗</h1>
        
        <div class="legend">
            <div class="legend-item">
                <div class="legend-color" style="background: #44ff44;"></div>
                <span>Normal Vehicle</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background: #ff4444;"></div>
                <span>Malicious Vehicle</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background: #ffff44;"></div>
                <span>Cluster Head</span>
            </div>
            <div class="legend-item">
                <div style="width: 20px; height: 20px; border: 3px dashed rgba(255,255,255,0.3); border-radius: 50%; margin-right: 8px;"></div>
                <span>Cluster Boundary</span>
            </div>
        </div>
        
        <canvas id="canvas" width="1200" height="600"></canvas>
        
        <div id="controls">
            <div class="control-group">
                <button id="playPause">▶️ Play</button>
                <button id="reset">🔄 Reset</button>
                <label>Speed:</label>
                <input type="range" id="speed" min="0.5" max="5" step="0.5" value="1">
                <span class="value-display"><span id="speedValue">1.0</span>x</span>
            </div>
            <div class="control-group">
                <label>Timeline:</label>
                <input type="range" id="timeline" min="0" max="100" value="0">
                <span class="value-display"><span id="timeValue">0.0</span>s / <span id="totalTime">0.0</span>s</span>
            </div>
        </div>
        
        <div id="stats">
            <div class="stat-box">
                <div class="stat-label">Active Clusters</div>
                <div class="stat-value" id="clusterCount">0</div>
            </div>
            <div class="stat-box">
                <div class="stat-label">Active Vehicles</div>
                <div class="stat-value" id="vehicleCount">0</div>
            </div>
            <div class="stat-box">
                <div class="stat-label">Messages Sent</div>
                <div class="stat-value" id="messagesSent">0</div>
            </div>
            <div class="stat-box">
                <div class="stat-label">Messages Received</div>
                <div class="stat-value" id="messagesReceived">0</div>
            </div>
        </div>
    </div>
    
    <script>
        const animationData = {animation_json};
        
        const canvas = document.getElementById('canvas');
        const ctx = canvas.getContext('2d');
        
        let currentFrame = 0;
        let isPlaying = false;
        let playbackSpeed = 1.0;
        let animationId = null;
        let lastFrameTime = 0;
        
        const totalFrames = animationData.frames.length;
        const totalDuration = animationData.metadata.duration;
        
        document.getElementById('totalTime').textContent = totalDuration.toFixed(1);
        document.getElementById('timeline').max = totalFrames - 1;
        
        // Vehicle trails for motion effect
        const vehicleTrails = {{}};
        
        function drawFrame(frameIndex) {{
            const frame = animationData.frames[frameIndex];
            
            // Clear canvas
            ctx.fillStyle = '#2a2a2a';
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            
            // Draw road lanes
            ctx.strokeStyle = '#444';
            ctx.lineWidth = 2;
            ctx.setLineDash([10, 5]);
            [200, 250, 350, 400].forEach(y => {{
                ctx.beginPath();
                ctx.moveTo(0, y);
                ctx.lineTo(canvas.width, y);
                ctx.stroke();
            }});
            ctx.setLineDash([]);
            
            // Draw clusters
            frame.clusters.forEach((cluster, idx) => {{
                const hue = (idx * 137.5) % 360;
                ctx.strokeStyle = `hsla(${{hue}}, 70%, 60%, 0.6)`;
                ctx.fillStyle = `hsla(${{hue}}, 70%, 60%, 0.1)`;
                ctx.lineWidth = 3;
                ctx.setLineDash([5, 5]);
                
                ctx.beginPath();
                ctx.arc(cluster.center_x, cluster.center_y, cluster.radius, 0, Math.PI * 2);
                ctx.fill();
                ctx.stroke();
                ctx.setLineDash([]);
                
                // Cluster label
                ctx.fillStyle = '#fff';
                ctx.font = 'bold 12px Arial';
                ctx.fillText(`Cluster ${{cluster.id}} (${{cluster.size}})`, 
                           cluster.center_x - 40, cluster.center_y - cluster.radius - 10);
            }});
            
            // Draw vehicles with trails
            frame.vehicles.forEach(vehicle => {{
                // Update trail
                if (!vehicleTrails[vehicle.id]) {{
                    vehicleTrails[vehicle.id] = [];
                }}
                vehicleTrails[vehicle.id].push({{x: vehicle.x, y: vehicle.y}});
                if (vehicleTrails[vehicle.id].length > 15) {{
                    vehicleTrails[vehicle.id].shift();
                }}
                
                // Draw trail
                ctx.strokeStyle = vehicle.is_malicious ? 'rgba(255,68,68,0.3)' : 'rgba(68,255,68,0.3)';
                ctx.lineWidth = 2;
                ctx.beginPath();
                vehicleTrails[vehicle.id].forEach((pos, i) => {{
                    if (i === 0) {{
                        ctx.moveTo(pos.x, pos.y);
                    }} else {{
                        ctx.lineTo(pos.x, pos.y);
                    }}
                }});
                ctx.stroke();
                
                // Draw vehicle
                const size = vehicle.is_cluster_head ? 10 : 7;
                ctx.fillStyle = vehicle.is_cluster_head ? '#ffff44' : 
                               (vehicle.is_malicious ? '#ff4444' : '#44ff44');
                
                ctx.beginPath();
                ctx.arc(vehicle.x, vehicle.y, size, 0, Math.PI * 2);
                ctx.fill();
                
                // Outline
                ctx.strokeStyle = '#fff';
                ctx.lineWidth = 2;
                ctx.stroke();
                
                // Direction indicator (arrow)
                const arrowLen = 15;
                const angle = vehicle.direction * Math.PI / 180;
                const dx = Math.cos(angle) * arrowLen;
                const dy = Math.sin(angle) * arrowLen;
                
                ctx.strokeStyle = '#fff';
                ctx.lineWidth = 2;
                ctx.beginPath();
                ctx.moveTo(vehicle.x, vehicle.y);
                ctx.lineTo(vehicle.x + dx, vehicle.y);
                ctx.stroke();
                
                // Vehicle ID (when cluster head)
                if (vehicle.is_cluster_head) {{
                    ctx.fillStyle = '#fff';
                    ctx.font = 'bold 10px Arial';
                    ctx.fillText(vehicle.id, vehicle.x - 10, vehicle.y - 15);
                }}
            }});
            
            // Update stats
            document.getElementById('clusterCount').textContent = frame.stats.total_clusters;
            document.getElementById('vehicleCount').textContent = frame.stats.total_vehicles;
            document.getElementById('messagesSent').textContent = frame.stats.messages_sent;
            document.getElementById('messagesReceived').textContent = frame.stats.messages_received;
            document.getElementById('timeValue').textContent = frame.time.toFixed(1);
            document.getElementById('timeline').value = frameIndex;
        }}
        
        function animate(timestamp) {{
            if (!isPlaying) return;
            
            const elapsed = timestamp - lastFrameTime;
            const frameDelay = (1000 / 60) / playbackSpeed; // 60 FPS base
            
            if (elapsed >= frameDelay) {{
                drawFrame(currentFrame);
                currentFrame++;
                
                if (currentFrame >= totalFrames) {{
                    currentFrame = 0;
                }}
                
                lastFrameTime = timestamp;
            }}
            
            animationId = requestAnimationFrame(animate);
        }}
        
        // Controls
        document.getElementById('playPause').addEventListener('click', () => {{
            isPlaying = !isPlaying;
            document.getElementById('playPause').textContent = isPlaying ? '⏸️ Pause' : '▶️ Play';
            if (isPlaying) {{
                lastFrameTime = performance.now();
                animate(lastFrameTime);
            }} else {{
                if (animationId) {{
                    cancelAnimationFrame(animationId);
                }}
            }}
        }});
        
        document.getElementById('reset').addEventListener('click', () => {{
            currentFrame = 0;
            vehicleTrails.length = 0;
            Object.keys(vehicleTrails).forEach(key => {{
                vehicleTrails[key] = [];
            }});
            drawFrame(0);
        }});
        
        document.getElementById('speed').addEventListener('input', (e) => {{
            playbackSpeed = parseFloat(e.target.value);
            document.getElementById('speedValue').textContent = playbackSpeed.toFixed(1);
        }});
        
        document.getElementById('timeline').addEventListener('input', (e) => {{
            currentFrame = parseInt(e.target.value);
            drawFrame(currentFrame);
        }});
        
        // Initial draw
        drawFrame(0);
    </script>
</body>
</html>"""
        
        html_content = html_template.replace(
            '{animation_json}',
            json.dumps(self.animation_data, indent=2)
        )
        
        with open(filename, 'w') as f:
            f.write(html_content)
        
        print(f"\n✅ Animation exported to: {filename}")
        print(f"📊 Total frames: {len(self.animation_data['frames'])}")
        print(f"⏱️  Duration: {self.duration}s")
        print(f"\nOpen in browser: file://{os.path.abspath(filename)}")


if __name__ == '__main__':
    print("🚗 Dynamic VANET Cluster Animation Generator 🚗")
    print("=" * 60)
    
    # Create simulator
    simulator = DynamicVehicleSimulator(
        num_vehicles=20,
        duration=30,
        timestep=0.5
    )
    
    # Run simulation
    animation_data = simulator.run_simulation()
    
    # Export HTML
    simulator.export_html('dynamic_movement.html')
    
    print("\n✅ Done! Open dynamic_movement.html in your browser to see real vehicle movement!")
