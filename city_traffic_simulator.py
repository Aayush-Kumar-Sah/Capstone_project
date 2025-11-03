#!/usr/bin/env python3
"""
Advanced VANET City Simulation with Intersections and Traffic Lights

Features:
- Multiple intersections with traffic lights
- Realistic traffic light timing
- Vehicles that stop/go based on lights
- Turn behavior at intersections
- Complex road network
- Emergency vehicle handling
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
from src.clustering import ClusteringAlgorithm, Cluster

class TrafficLight:
    """Traffic light with realistic timing"""
    def __init__(self, x, y, initial_state='red'):
        self.x = x
        self.y = y
        self.state = initial_state  # 'red', 'yellow', 'green'
        self.timer = 0
        self.green_duration = 15.0  # seconds
        self.yellow_duration = 3.0
        self.red_duration = 15.0
        
    def update(self, dt):
        """Update traffic light state"""
        self.timer += dt
        
        if self.state == 'green' and self.timer >= self.green_duration:
            self.state = 'yellow'
            self.timer = 0
        elif self.state == 'yellow' and self.timer >= self.yellow_duration:
            self.state = 'red'
            self.timer = 0
        elif self.state == 'red' and self.timer >= self.red_duration:
            self.state = 'green'
            self.timer = 0

class Intersection:
    """Road intersection with traffic lights"""
    def __init__(self, x, y, name):
        self.x = x
        self.y = y
        self.name = name
        # Traffic lights for each direction (N, S, E, W)
        self.lights = {
            'north': TrafficLight(x, y - 50, 'red'),
            'south': TrafficLight(x, y + 50, 'green'),
            'east': TrafficLight(x + 50, y, 'red'),
            'west': TrafficLight(x - 50, y, 'green')
        }
        self.stop_line_distance = 50  # Distance before intersection to stop
        
    def update(self, dt):
        """Update all traffic lights"""
        for light in self.lights.values():
            light.update(dt)
    
    def can_enter(self, vehicle_x, vehicle_y, direction) -> bool:
        """Check if vehicle can enter intersection"""
        # Determine which light applies based on approach direction
        if abs(vehicle_y - self.y) < 30:  # Horizontal approach
            if vehicle_x < self.x:  # Approaching from west
                return self.lights['west'].state == 'green'
            else:  # Approaching from east
                return self.lights['east'].state == 'green'
        else:  # Vertical approach
            if vehicle_y < self.y:  # Approaching from north
                return self.lights['north'].state == 'green'
            else:  # Approaching from south
                return self.lights['south'].state == 'green'

class Road:
    """Road segment with direction and speed limit"""
    def __init__(self, start_x, start_y, end_x, end_y, lanes=2, speed_limit=30):
        self.start_x = start_x
        self.start_y = start_y
        self.end_x = end_x
        self.end_y = end_y
        self.lanes = lanes
        self.speed_limit = speed_limit
        
        # Calculate direction
        dx = end_x - start_x
        dy = end_y - start_y
        self.direction = math.degrees(math.atan2(dy, dx))
        self.length = math.sqrt(dx*dx + dy*dy)

class CityVANETSimulator:
    """Advanced city VANET simulation with complex traffic and V2V communication"""
    
    def __init__(self, num_vehicles=30, duration=60, timestep=0.1):
        self.num_vehicles = num_vehicles
        self.duration = duration
        self.timestep = timestep
        self.app = CustomVANETApplication(ClusteringAlgorithm.MOBILITY_BASED)
        self.app.trust_enabled = True
        
        # V2V Communication settings
        self.communication_range = 250  # meters (pixels)
        self.v2v_messages = []  # Store all V2V messages for visualization
        self.collision_warnings = []  # Track collision warnings
        self.lane_change_alerts = []  # Track lane change alerts
        self.emergency_broadcasts = []  # Track emergency vehicle alerts
        
        # Statistics for V2V
        self.v2v_stats = {
            'total_messages': 0,
            'collision_warnings': 0,
            'lane_change_alerts': 0,
            'emergency_alerts': 0,
            'brake_warnings': 0,
            'traffic_jam_alerts': 0,
            'inter_cluster_messages': 0
        }
        
        # Create city road network
        self.setup_city_network()
        
        self.animation_data = {
            'frames': [],
            'vehicles': {},
            'intersections': [],
            'roads': [],
            'v2v_messages': [],  # Add V2V message history
            'metadata': {
                'duration': duration,
                'timestep': timestep,
                'num_vehicles': num_vehicles,
                'communication_range': self.communication_range
            }
        }
        
    def setup_city_network(self):
        """Create a MASSIVE Manhattan-style grid inspired by Times Square area"""
        self.intersections = []
        self.roads = []
        
        # HIGHWAY-FOCUSED NETWORK - Long highway through middle with fewer intersections
        grid_spacing = 300  # Distance between intersections
        grid_offset_x = 100
        grid_offset_y = 80
        num_intersections_x = 11
        num_intersections_y = 11
        
        # Create intersections - SKIP middle rows 4,5,6,7 for long highway corridor
        for i in range(num_intersections_y):
            for j in range(num_intersections_x):
                # Skip middle 4 rows (4,5,6,7) except for on/off ramp positions
                if 4 <= i <= 7:
                    # Only create on/off ramps at positions 0, 3, 6, 9, 10
                    if j not in [0, 3, 6, 9, 10]:
                        continue
                
                x = grid_offset_x + j * grid_spacing
                y = grid_offset_y + i * grid_spacing
                
                # Name based on location
                if 4 <= i <= 7:
                    # Highway exits
                    if j == 0:
                        intersection = Intersection(x, y, f"West Exit {i-3}")
                    elif j == 10:
                        intersection = Intersection(x, y, f"East Exit {i-3}")
                    else:
                        intersection = Intersection(x, y, f"Highway Exit {j}")
                else:
                    # Regular city streets
                    street_name = f"{i+42}St"
                    avenue_name = f"{j+1}Ave"
                    intersection = Intersection(x, y, f"{avenue_name}/{street_name}")
                
                self.intersections.append(intersection)
        
        print(f"🛣️  Created {len(self.intersections)} intersections (highway corridor in middle)")
        
        # Create horizontal roads (STREETS) - skip middle highway area
        for i in range(num_intersections_y):
            y = grid_offset_y + i * grid_spacing
            
            # Skip middle rows for highways
            if 4 <= i <= 7:
                continue
            
            for j in range(num_intersections_x - 1):
                x_start = grid_offset_x + j * grid_spacing
                x_end = grid_offset_x + (j + 1) * grid_spacing
                
                # Variable speed limits
                speed = 35 if i % 2 == 0 else 30
                lane_offset = 25 if i % 2 == 0 else 20
                lanes = 2
                
                # Eastbound lane
                self.roads.append(Road(x_start, y - lane_offset, x_end, y - lane_offset, 
                                      lanes=lanes, speed_limit=speed))
                # Westbound lane
                self.roads.append(Road(x_end, y + lane_offset, x_start, y + lane_offset, 
                                      lanes=lanes, speed_limit=speed))
        
        # Create vertical roads (AVENUES) - skip middle highway area
        for j in range(num_intersections_x):
            x = grid_offset_x + j * grid_spacing
            
            # For columns with highway exits, connect to highway
            for i in range(num_intersections_y - 1):
                y_start = grid_offset_y + i * grid_spacing
                y_end = grid_offset_y + (i + 1) * grid_spacing
                
                # Skip connections through highway zone (rows 4-7)
                if (4 <= i <= 6):
                    # Only allow connections at exit ramps
                    if j not in [0, 3, 6, 9, 10]:
                        continue
                
                speed = 40 if j % 3 == 0 else 35
                lane_offset = 28 if j % 3 == 0 else 25
                lanes = 3 if j % 3 == 0 else 2
                
                # Southbound lane
                self.roads.append(Road(x + lane_offset, y_start, x + lane_offset, y_end, 
                                      lanes=lanes, speed_limit=speed))
                # Northbound lane
                self.roads.append(Road(x - lane_offset, y_end, x - lane_offset, y_start, 
                                      lanes=lanes, speed_limit=speed))
        
        # CREATE LONG EXPRESS HIGHWAYS through middle (rows 4,5,6,7)
        highway_y_positions = [
            grid_offset_y + 4 * grid_spacing - 50,  # Highway 1 (northbound)
            grid_offset_y + 5 * grid_spacing,       # Highway 2 (middle north)
            grid_offset_y + 6 * grid_spacing,       # Highway 3 (middle south)
            grid_offset_y + 7 * grid_spacing + 50,  # Highway 4 (southbound)
        ]
        
        for idx, y in enumerate(highway_y_positions):
            # Long highway spanning entire width
            x_start = grid_offset_x
            x_end = grid_offset_x + (num_intersections_x - 1) * grid_spacing
            
            # Eastbound highway (faster lanes)
            self.roads.append(Road(x_start, y - 40, x_end, y - 40, 
                                  lanes=6, speed_limit=70))  # High speed highway
            # Westbound highway
            self.roads.append(Road(x_end, y + 40, x_start, y + 40, 
                                  lanes=6, speed_limit=70))
        
        # Add on/off ramps connecting city to highways
        ramp_positions = [0, 3, 6, 9, 10]  # Exit positions
        for j in ramp_positions:
            x = grid_offset_x + j * grid_spacing
            
            # On-ramps from row 3 to highway area
            y_from = grid_offset_y + 3 * grid_spacing
            y_to = highway_y_positions[0]
            self.roads.append(Road(x, y_from, x + 20, y_to, lanes=2, speed_limit=45))
            
            # Off-ramps from highway to row 8
            y_from_hw = highway_y_positions[3]
            y_to_city = grid_offset_y + 8 * grid_spacing
            self.roads.append(Road(x + 20, y_from_hw, x, y_to_city, lanes=2, speed_limit=45))
        
        # Add perimeter express highways
        # Top express highway
        self.roads.append(Road(100, 50, 3100, 50, lanes=4, speed_limit=65))
        self.roads.append(Road(3100, 50, 100, 50, lanes=4, speed_limit=65))
        
        # Bottom express highway
        self.roads.append(Road(100, 3030, 3100, 3030, lanes=4, speed_limit=65))
        self.roads.append(Road(3100, 3030, 100, 3030, lanes=4, speed_limit=65))
        
        # Left express highway
        self.roads.append(Road(50, 80, 50, 3030, lanes=4, speed_limit=65))
        self.roads.append(Road(50, 3030, 50, 80, lanes=4, speed_limit=65))
        
        # Right express highway
        self.roads.append(Road(3130, 80, 3130, 3030, lanes=4, speed_limit=65))
        self.roads.append(Road(3130, 3030, 3130, 80, lanes=4, speed_limit=65))
        
        print(f"\n🛣️  HIGHWAY-FOCUSED VANET NETWORK 🛣️")
        print(f"=" * 70)
        print(f"  📍 Intersections: {len(self.intersections)} (city areas only)")
        print(f"  🛣️  Roads: {len(self.roads)} road segments")
        print(f"  🏎️  LONG HIGHWAY CORRIDOR: 4 express lanes (70 mph)")
        print(f"     - Spans full network width (~{num_intersections_x * grid_spacing} pixels)")
        print(f"     - 6 lanes per direction (12 total)")
        print(f"  🚗 City streets: {num_intersections_y - 4} rows (35 mph)")
        print(f"  🎯 Highway exits: {len(ramp_positions)} on/off ramps")
        print(f"  🚦 Perimeter highways: 65 mph express ring")
        print(f"=" * 70)
    
    def initialize_vehicles(self):
        """Create vehicles on various roads"""
        vehicle_configs = []
        
        for i in range(self.num_vehicles):
            # Randomly choose a road
            road = random.choice(self.roads)
            
            # Position along the road
            progress = random.random()
            x = road.start_x + (road.end_x - road.start_x) * progress
            y = road.start_y + (road.end_y - road.start_y) * progress
            
            # Speed based on road limit
            speed = road.speed_limit + random.uniform(-5, 5)
            direction = road.direction
            
            # Vehicle types with different behaviors
            vehicle_type = random.choice(['car', 'car', 'car', 'truck', 'emergency'])
            is_emergency = (vehicle_type == 'emergency')
            is_malicious = (i % 8 == 0) and not is_emergency  # ~12% malicious
            
            vehicle_id = f'v{i}'
            self.app.add_vehicle(
                vehicle_id=vehicle_id,
                x=x, y=y,
                speed=speed,
                direction=direction,
                lane_id=f'road_{self.roads.index(road)}'
            )
            
            vehicle_configs.append({
                'id': vehicle_id,
                'type': vehicle_type,
                'is_emergency': is_emergency,
                'is_malicious': is_malicious,
                'current_road': road,  # Track current road
                'target_road': None,
                'waiting_at_light': False,
                'current_lane': random.choice([-1, 1]),  # -1 = left lane, 1 = right lane
                'lane_change_timer': 0.0,  # Cooldown between lane changes
                'target_lane': None  # Lane being changed to
            })
            
            # Configure in app
            node = self.app.vehicle_nodes[vehicle_id]
            node.vehicle_type = vehicle_type
            node.lane_offset = 0.0  # Lateral position offset from road center
            
            if is_malicious:
                node.is_malicious = True
                node.trust_score = 0.2
                node.message_count = 150  # High message spam (suspicious)
                node.erratic_behavior_count = 0
            else:
                node.message_count = random.randint(10, 50)
            
            if is_emergency:
                node.trust_score = 1.0
        
        # Store configs without Road objects (not JSON serializable)
        self.vehicle_configs = {}
        for vc in vehicle_configs:
            self.vehicle_configs[vc['id']] = {
                'id': vc['id'],
                'type': vc['type'],
                'is_emergency': vc['is_emergency'],
                'is_malicious': vc['is_malicious'],
                'current_road': vc['current_road'],  # Keep for simulation
                'target_road': vc['target_road'],
                'waiting_at_light': vc['waiting_at_light'],
                'current_lane': vc['current_lane'],
                'lane_change_timer': vc['lane_change_timer'],
                'target_lane': vc['target_lane']
            }
        
        # Don't add vehicle_configs to animation_data yet (has Road objects)
    
    def broadcast_v2v_message(self, sender_id: str, message_type: str, data: dict, current_time: float):
        """
        Broadcast V2V message to nearby vehicles within communication range
        Uses relay nodes for multi-hop communication within clusters
        Message types: collision_warning, lane_change, emergency_alert, brake_warning, traffic_jam
        """
        if sender_id not in self.app.vehicle_nodes:
            return []
        
        sender_node = self.app.vehicle_nodes[sender_id]
        sender_x, sender_y = sender_node.location
        
        # Find direct recipients (within communication range)
        direct_recipients = []
        for vehicle_id, node in self.app.vehicle_nodes.items():
            if vehicle_id == sender_id:
                continue
            
            x, y = node.location
            distance = math.sqrt((x - sender_x)**2 + (y - sender_y)**2)
            
            if distance <= self.communication_range:
                direct_recipients.append(vehicle_id)
                
                # Process message at recipient
                self._handle_v2v_message(vehicle_id, sender_id, message_type, data, current_time)
        
        # Multi-hop relay for cluster members
        relayed_recipients = []
        if hasattr(sender_node, 'cluster_id') and sender_node.cluster_id:
            cluster = self.app.clustering_engine.clusters.get(sender_node.cluster_id)
            
            if cluster:
                # Use relay forwarding for cluster members
                message = {'type': message_type, 'data': data}
                cluster_recipients = self._forward_message_through_relays(
                    cluster, message, sender_id, current_time
                )
                
                # Process relayed messages
                for recipient_id in cluster_recipients:
                    if recipient_id not in direct_recipients:
                        relayed_recipients.append(recipient_id)
                        self._handle_v2v_message(recipient_id, sender_id, message_type, data, current_time)
        
        all_recipients = direct_recipients + relayed_recipients
        
        # Log message for statistics
        self.v2v_stats['total_messages'] += 1
        if message_type in self.v2v_stats:
            self.v2v_stats[message_type] += 1
        
        if relayed_recipients:
            self.v2v_stats['relayed_messages'] = self.v2v_stats.get('relayed_messages', 0) + 1
        
        # Store for visualization
        message_record = {
            'time': current_time,
            'sender': sender_id,
            'type': message_type,
            'recipients': len(all_recipients),
            'direct': len(direct_recipients),
            'relayed': len(relayed_recipients),
            'data': data
        }
        self.v2v_messages.append(message_record)
        
        return all_recipients
    
    def _handle_v2v_message(self, recipient_id: str, sender_id: str, message_type: str, 
                           data: dict, current_time: float):
        """Handle received V2V message and take appropriate action"""
        if recipient_id not in self.app.vehicle_nodes:
            return
        
        recipient_node = self.app.vehicle_nodes[recipient_id]
        sender_node = self.app.vehicle_nodes[sender_id] if sender_id in self.app.vehicle_nodes else None
        
        if message_type == 'collision_warnings':
            # Reduce speed to avoid collision
            recipient_node.speed = max(10, recipient_node.speed * 0.7)
            
        elif message_type == 'lane_change_alerts':
            # Acknowledge lane change, adjust position if needed
            # Slow down slightly to give space
            if data.get('safe') == False:
                recipient_node.speed = max(5, recipient_node.speed * 0.9)
            
        elif message_type == 'emergency_alerts':
            # Emergency vehicle approaching - clear the way
            if not self.vehicle_configs[recipient_id]['is_emergency']:
                recipient_node.speed = max(5, recipient_node.speed * 0.5)  # Slow down significantly
                
        elif message_type == 'brake_warnings':
            # Vehicle ahead is braking hard
            recipient_node.speed = max(0, recipient_node.speed - 10)
            
        elif message_type == 'traffic_jam_alerts':
            # Traffic jam ahead, find alternate route
            # (Would trigger rerouting in advanced implementation)
            recipient_node.speed = max(5, recipient_node.speed * 0.6)
    
    def broadcast_inter_cluster_message(self, sender_cluster_id: str, message_type: str, 
                                        data: dict, current_time: float):
        """
        Broadcast message from one cluster to neighboring clusters via boundary nodes
        Enables inter-cluster communication for wider area awareness
        """
        if sender_cluster_id not in self.app.clustering_engine.clusters:
            return []
        
        sender_cluster = self.app.clustering_engine.clusters[sender_cluster_id]
        
        if not hasattr(sender_cluster, 'boundary_nodes') or not sender_cluster.boundary_nodes:
            # No boundary nodes elected yet
            return []
        
        inter_cluster_recipients = []
        
        # For each neighboring cluster
        for neighbor_cluster_id, boundary_node_id in sender_cluster.boundary_nodes.items():
            if neighbor_cluster_id not in self.app.clustering_engine.clusters:
                continue
            
            if boundary_node_id not in self.app.vehicle_nodes:
                continue
            
            neighbor_cluster = self.app.clustering_engine.clusters[neighbor_cluster_id]
            boundary_node = self.app.vehicle_nodes[boundary_node_id]
            
            # Check if neighbor cluster also has a boundary node facing us
            neighbor_boundary_node_id = None
            if hasattr(neighbor_cluster, 'boundary_nodes') and neighbor_cluster.boundary_nodes:
                neighbor_boundary_node_id = neighbor_cluster.boundary_nodes.get(sender_cluster_id)
            
            if neighbor_boundary_node_id and neighbor_boundary_node_id in self.app.vehicle_nodes:
                # Both clusters have boundary nodes facing each other
                neighbor_boundary_node = self.app.vehicle_nodes[neighbor_boundary_node_id]
                
                # Check if boundary nodes are within communication range
                bn_x, bn_y = boundary_node.location
                nbn_x, nbn_y = neighbor_boundary_node.location
                
                boundary_distance = math.sqrt((bn_x - nbn_x)**2 + (bn_y - nbn_y)**2)
                
                if boundary_distance <= self.communication_range:
                    # Boundary nodes can communicate!
                    # Forward message to neighbor cluster's leader
                    if neighbor_cluster.head_id and neighbor_cluster.head_id in self.app.vehicle_nodes:
                        # Leader broadcasts to its cluster
                        leader_recipients = self.broadcast_v2v_message(
                            neighbor_cluster.head_id, message_type, data, current_time
                        )
                        
                        inter_cluster_recipients.extend(leader_recipients)
                        
                        # Track inter-cluster message
                        self.v2v_stats['inter_cluster_messages'] = \
                            self.v2v_stats.get('inter_cluster_messages', 0) + 1
        
        return inter_cluster_recipients
    
    def check_collision_risk(self, vehicle_id: str, current_time: float):
        """
        Check if vehicle is at risk of collision with nearby vehicles
        Broadcasts warning if imminent collision detected
        Now considers lane positions for more accurate detection
        """
        if vehicle_id not in self.app.vehicle_nodes:
            return False
        
        node = self.app.vehicle_nodes[vehicle_id]
        config = self.vehicle_configs[vehicle_id]
        x, y = node.location
        speed = node.speed
        direction = node.direction
        my_lane = config['current_lane']
        
        # Calculate future position (1 second ahead)
        future_x = x + speed * math.cos(math.radians(direction)) * 1.0
        future_y = y + speed * math.sin(math.radians(direction)) * 1.0
        
        collision_risk = False
        
        # Check all nearby vehicles
        for other_id, other_node in self.app.vehicle_nodes.items():
            if other_id == vehicle_id:
                continue
            
            other_config = self.vehicle_configs[other_id]
            other_x, other_y = other_node.location
            other_lane = other_config['current_lane']
            
            # Check current distance
            current_distance = math.sqrt((x - other_x)**2 + (y - other_y)**2)
            
            if current_distance > 100:  # Only check nearby vehicles
                continue
            
            # Check if in same lane or changing to same lane
            same_lane = (my_lane == other_lane)
            my_changing = config['target_lane'] is not None
            other_changing = other_config['target_lane'] is not None
            
            # Risk if both in same lane, or both changing to same lane
            lane_conflict = same_lane or (my_changing and other_changing and 
                                         config['target_lane'] == other_config['target_lane'])
            
            if not lane_conflict and not my_changing and not other_changing:
                continue  # Different lanes, no risk
            
            # Calculate other vehicle's future position
            other_future_x = other_x + other_node.speed * math.cos(math.radians(other_node.direction)) * 1.0
            other_future_y = other_y + other_node.speed * math.sin(math.radians(other_node.direction)) * 1.0
            
            # Check if future positions are too close (potential collision)
            future_distance = math.sqrt((future_x - other_future_x)**2 + (future_y - other_future_y)**2)
            
            # Tighter threshold during lane changes
            threshold = 25 if (my_changing or other_changing) else 30
            
            if future_distance < threshold:  # Collision threshold
                collision_risk = True
                
                # Broadcast collision warning
                self.broadcast_v2v_message(
                    vehicle_id,
                    'collision_warnings',
                    {
                        'target_vehicle': other_id,
                        'distance': current_distance,
                        'time_to_collision': future_distance / max(1, speed),
                        'lane_change_involved': my_changing or other_changing
                    },
                    current_time
                )
                
                self.collision_warnings.append({
                    'time': current_time,
                    'vehicle1': vehicle_id,
                    'vehicle2': other_id,
                    'distance': current_distance,
                    'lane_change': my_changing or other_changing
                })
                
                break
        
        return collision_risk
    
    def check_lane_change_safety(self, vehicle_id: str, target_lane_offset: float, current_time: float):
        """
        Check if lane change is safe and broadcast alert to nearby vehicles
        Returns True if safe, False otherwise
        Checks for vehicles in target lane with proper spacing
        """
        if vehicle_id not in self.app.vehicle_nodes:
            return False
        
        node = self.app.vehicle_nodes[vehicle_id]
        config = self.vehicle_configs[vehicle_id]
        x, y = node.location
        direction = node.direction
        current_lane = config['current_lane']
        target_lane = -current_lane  # Opposite lane
        
        # Check for vehicles in target lane
        safe = True
        closest_distance = float('inf')
        
        for other_id, other_node in self.app.vehicle_nodes.items():
            if other_id == vehicle_id:
                continue
            
            other_config = self.vehicle_configs[other_id]
            other_x, other_y = other_node.location
            other_lane = other_config['current_lane']
            
            # Check if other vehicle is in target lane or changing to it
            target_lane_conflict = (other_lane == target_lane or 
                                   other_config.get('target_lane') == target_lane)
            
            if not target_lane_conflict:
                continue
            
            # Calculate distance
            distance = math.sqrt((x - other_x)**2 + (y - other_y)**2)
            closest_distance = min(closest_distance, distance)
            
            # Check if in similar direction (within 60 degrees)
            angle_diff = abs((other_node.direction - direction + 180) % 360 - 180)
            if angle_diff > 60:
                continue  # Different direction, not a concern
            
            # Safety distance depends on relative speed
            relative_speed = abs(node.speed - other_node.speed)
            min_safe_distance = 40 + (relative_speed * 2)  # Dynamic safety margin
            
            # If vehicle is too close in target lane
            if distance < min_safe_distance:
                safe = False
                break
        
        # Broadcast lane change alert regardless (inform others of intention)
        self.broadcast_v2v_message(
            vehicle_id,
            'lane_change_alerts',
            {
                'direction': 'left' if target_lane_offset < 0 else 'right',
                'safe': safe,
                'closest_vehicle_distance': closest_distance if closest_distance != float('inf') else None
            },
            current_time
        )
        
        self.lane_change_alerts.append({
            'time': current_time,
            'vehicle': vehicle_id,
            'safe': safe,
            'closest_distance': closest_distance
        })
        
        return safe
    
    def broadcast_emergency_alert(self, vehicle_id: str, current_time: float):
        """Emergency vehicle broadcasts alert to clear the way"""
        if vehicle_id not in self.app.vehicle_nodes:
            return
        
        config = self.vehicle_configs.get(vehicle_id)
        if not config or not config['is_emergency']:
            return
        
        # Broadcast to own cluster
        recipients = self.broadcast_v2v_message(
            vehicle_id,
            'emergency_alerts',
            {
                'type': 'emergency_vehicle',
                'direction': self.app.vehicle_nodes[vehicle_id].direction,
                'speed': self.app.vehicle_nodes[vehicle_id].speed
            },
            current_time
        )
        
        # Also broadcast to neighboring clusters via boundary nodes
        vehicle_node = self.app.vehicle_nodes.get(vehicle_id)
        if vehicle_node and hasattr(vehicle_node, 'cluster_id') and vehicle_node.cluster_id:
            inter_cluster_recipients = self.broadcast_inter_cluster_message(
                vehicle_node.cluster_id,
                'emergency_alerts',
                {
                    'type': 'emergency_vehicle',
                    'direction': vehicle_node.direction,
                    'speed': vehicle_node.speed
                },
                current_time
            )
            recipients.extend(inter_cluster_recipients)
        
        self.emergency_broadcasts.append({
            'time': current_time,
            'vehicle': vehicle_id,
            'recipients': len(recipients)
        })
    def find_nearest_road(self, x, y, current_direction=None, max_distance=100):
        """Find the nearest road to a position, optionally matching direction"""
        best_road = None
        min_distance = float('inf')
        
        for road in self.roads:
            # Calculate distance from point to road segment
            dx = road.end_x - road.start_x
            dy = road.end_y - road.start_y
            length_sq = dx*dx + dy*dy
            
            if length_sq == 0:
                continue
            
            # Find closest point on road segment
            t = max(0, min(1, ((x - road.start_x) * dx + (y - road.start_y) * dy) / length_sq))
            closest_x = road.start_x + t * dx
            closest_y = road.start_y + t * dy
            
            distance = math.sqrt((x - closest_x)**2 + (y - closest_y)**2)
            
            # Prefer roads matching current direction (within 45 degrees)
            if current_direction is not None:
                angle_diff = abs((road.direction - current_direction + 180) % 360 - 180)
                if angle_diff > 45:
                    distance += 100  # Penalty for wrong direction
            
            if distance < min_distance and distance < max_distance:
                min_distance = distance
                best_road = road
        
        return best_road
    
    def find_connecting_road_at_intersection(self, intersection, current_direction):
        """Find a road connecting to an intersection, allowing turns"""
        connecting_roads = []
        
        for road in self.roads:
            # Check if road starts near this intersection
            start_dist = math.sqrt((road.start_x - intersection.x)**2 + (road.start_y - intersection.y)**2)
            
            # Increased tolerance for finding connecting roads
            if start_dist < 100:
                connecting_roads.append(road)
        
        if not connecting_roads:
            return None
        
        # 70% continue straight, 30% turn
        if random.random() < 0.7 and len(connecting_roads) > 1:
            # Prefer same direction (within 60 degrees for more flexibility)
            straight_roads = [r for r in connecting_roads 
                            if abs((r.direction - current_direction + 180) % 360 - 180) < 60]
            if straight_roads:
                return random.choice(straight_roads)
        
        # Otherwise pick any connecting road
        return random.choice(connecting_roads)
    
    def _is_blocked_ahead(self, vehicle_id: str, x: float, y: float, direction: float) -> bool:
        """Check if there's a slower vehicle ahead in the same lane"""
        if vehicle_id not in self.app.vehicle_nodes:
            return False
        
        my_node = self.app.vehicle_nodes[vehicle_id]
        my_config = self.vehicle_configs[vehicle_id]
        my_lane = my_config['current_lane']
        
        # Look ahead 100 pixels
        look_ahead_distance = 100
        ahead_x = x + look_ahead_distance * math.cos(math.radians(direction))
        ahead_y = y + look_ahead_distance * math.sin(math.radians(direction))
        
        for other_id, other_node in self.app.vehicle_nodes.items():
            if other_id == vehicle_id:
                continue
            
            other_config = self.vehicle_configs[other_id]
            other_x, other_y = other_node.location
            
            # Check if in same lane
            if other_config['current_lane'] != my_lane:
                continue
            
            # Check if ahead of us
            dist_to_other = math.sqrt((other_x - x)**2 + (other_y - y)**2)
            if dist_to_other > look_ahead_distance or dist_to_other < 5:
                continue
            
            # Check if in our path (similar direction)
            angle_diff = abs((other_node.direction - direction + 180) % 360 - 180)
            if angle_diff > 45:
                continue
            
            # Check if slower
            if other_node.speed < my_node.speed - 5:
                return True
        
        return False
    
    def update_vehicle_positions(self, current_time: float):
        """Update vehicles with traffic light awareness and lane changes"""
        for vehicle_id, node in self.app.vehicle_nodes.items():
            config = self.vehicle_configs[vehicle_id]
            x, y = node.location
            speed = node.speed
            direction = node.direction
            
            # LANE CHANGE LOGIC
            config['lane_change_timer'] = max(0, config['lane_change_timer'] - self.timestep)
            
            # Decide if vehicle should change lanes (every 5-15 seconds)
            if config['lane_change_timer'] <= 0 and config['target_lane'] is None:
                # Reasons to change lanes:
                # 1. Random lane change (10% chance)
                # 2. Passing slower vehicle ahead (30% chance if blocked)
                # 3. Emergency vehicles change lanes more aggressively
                
                should_change = False
                
                if config['is_emergency'] and random.random() < 0.3:
                    should_change = True
                elif self._is_blocked_ahead(vehicle_id, x, y, direction):
                    # Check if vehicle ahead is slower
                    if random.random() < 0.3:
                        should_change = True
                elif random.random() < 0.1:  # Random lane change
                    should_change = True
                
                if should_change:
                    # Determine target lane (switch to opposite lane)
                    new_lane = -config['current_lane']
                    
                    # Check if lane change is safe (reduced to 10 pixels per lane)
                    lane_offset = new_lane * 10  # 10 pixels per lane (safer)
                    if self.check_lane_change_safety(vehicle_id, lane_offset, current_time):
                        config['target_lane'] = new_lane
                        config['lane_change_timer'] = random.uniform(5, 15)  # Reset cooldown
                    else:
                        # Lane change not safe, wait longer
                        config['lane_change_timer'] = 2.0
            
            # Execute lane change if in progress
            if config['target_lane'] is not None:
                target_offset = config['target_lane'] * 10  # 10 pixels per lane
                current_offset = node.lane_offset
                
                # Gradually move to target lane
                offset_diff = target_offset - current_offset
                if abs(offset_diff) < 2:
                    # Lane change complete
                    node.lane_offset = target_offset
                    config['current_lane'] = config['target_lane']
                    config['target_lane'] = None
                else:
                    # Continue lane change (smooth transition, slower)
                    node.lane_offset += math.copysign(min(abs(offset_diff), 3), offset_diff)
            
            # Check for nearby intersections and traffic lights
            stopped = False
            for intersection in self.intersections:
                dist_to_intersection = math.sqrt((x - intersection.x)**2 + (y - intersection.y)**2)
                
                # If approaching intersection
                if 30 < dist_to_intersection < 60:
                    # Emergency vehicles ignore lights
                    if not config['is_emergency']:
                        if not intersection.can_enter(x, y, direction):
                            # Red light - stop!
                            stopped = True
                            config['waiting_at_light'] = True
                            node.speed = max(0, node.speed - 5)  # Brake
                            break
                    else:
                        # Emergency vehicle - speed up!
                        node.speed = min(50, node.speed + 2)
                
                elif dist_to_intersection <= 30:
                    # In intersection - go through
                    config['waiting_at_light'] = False
            
            # Update speed if not stopped
            if not stopped and config['waiting_at_light']:
                # Light turned green, accelerate
                node.speed = min(node.speed + 3, 35)
                config['waiting_at_light'] = False
            
            # Calculate movement
            rad = math.radians(direction)
            dx = math.cos(rad) * node.speed * self.timestep
            dy = math.sin(rad) * node.speed * self.timestep
            
            new_x = x + dx
            new_y = y + dy
            
            # Get current road
            current_road = config.get('current_road')
            
            # Check if we're reaching the end of current road
            if current_road:
                # Calculate distance to end of road
                dist_to_end = math.sqrt((new_x - current_road.end_x)**2 + (new_y - current_road.end_y)**2)
                
                # If near end of road, find next road
                if dist_to_end < 40:
                    next_road = None
                    
                    # Try 1: Find nearest intersection
                    nearest_intersection = None
                    min_dist = float('inf')
                    for intersection in self.intersections:
                        d = math.sqrt((current_road.end_x - intersection.x)**2 + 
                                    (current_road.end_y - intersection.y)**2)
                        if d < min_dist and d < 80:
                            min_dist = d
                            nearest_intersection = intersection
                    
                    if nearest_intersection:
                        # Find connecting road from intersection
                        next_road = self.find_connecting_road_at_intersection(nearest_intersection, direction)
                    
                    # Try 2: If no intersection connection, find any nearby road
                    if not next_road:
                        next_road = self.find_nearest_road(current_road.end_x, current_road.end_y, direction, max_distance=150)
                    
                    # Try 3: Find any road in general direction
                    if not next_road:
                        # Look for roads ahead in the direction of travel
                        ahead_x = current_road.end_x + math.cos(rad) * 50
                        ahead_y = current_road.end_y + math.sin(rad) * 50
                        next_road = self.find_nearest_road(ahead_x, ahead_y, direction, max_distance=200)
                    
                    # Try 4: Pick any random road as fallback
                    if not next_road:
                        available_roads = [r for r in self.roads if r != current_road]
                        if available_roads:
                            next_road = random.choice(available_roads)
                    
                    if next_road:
                        config['current_road'] = next_road
                        # Snap to start of new road
                        new_x = next_road.start_x + (next_road.end_x - next_road.start_x) * 0.1
                        new_y = next_road.start_y + (next_road.end_y - next_road.start_y) * 0.1
                        node.direction = next_road.direction
                        direction = next_road.direction
                        # Match road speed
                        node.speed = min(node.speed, next_road.speed_limit)
                else:
                    # Stay on current road - snap to road path if drifting
                    road_dx = current_road.end_x - current_road.start_x
                    road_dy = current_road.end_y - current_road.start_y
                    road_length_sq = road_dx * road_dx + road_dy * road_dy
                    
                    if road_length_sq > 0:
                        # Project position onto road
                        t = ((new_x - current_road.start_x) * road_dx + 
                             (new_y - current_road.start_y) * road_dy) / road_length_sq
                        t = max(0, min(1, t))  # Clamp to road segment
                        
                        # Calculate ideal position on road
                        ideal_x = current_road.start_x + t * road_dx
                        ideal_y = current_road.start_y + t * road_dy
                        
                        # If too far from road, snap back
                        dist_from_road = math.sqrt((new_x - ideal_x)**2 + (new_y - ideal_y)**2)
                        if dist_from_road > 15:
                            # Gradually pull back to road
                            new_x = new_x * 0.7 + ideal_x * 0.3
                            new_y = new_y * 0.7 + ideal_y * 0.3
                        
                        # Apply lane offset perpendicular to road direction (limited to ±10 pixels)
                        if hasattr(node, 'lane_offset') and abs(node.lane_offset) > 0.1:
                            # Limit lane offset to prevent vehicles from going too far off road
                            limited_offset = max(-10, min(10, node.lane_offset))
                            
                            # Calculate perpendicular direction (90 degrees to road)
                            perp_angle = math.radians(current_road.direction + 90)
                            offset_x = limited_offset * math.cos(perp_angle)
                            offset_y = limited_offset * math.sin(perp_angle)
                            
                            # Apply offset and immediately check boundaries
                            test_x = new_x + offset_x
                            test_y = new_y + offset_y
                            
                            # Only apply if it keeps vehicle in bounds
                            if 60 <= test_x <= 3240 and 60 <= test_y <= 3140:
                                new_x = test_x
                                new_y = test_y
                            else:
                                # Reset lane offset if it would push us out of bounds
                                node.lane_offset = 0
                                config['current_lane'] = 0
                                config['target_lane'] = None
            
            # Strict boundary enforcement - keep vehicles well within bounds
            if new_x < 60 or new_x > 3240 or new_y < 60 or new_y > 3140:
                # Force vehicle back onto a road
                nearest_road = self.find_nearest_road(x, y, direction, max_distance=200)
                if nearest_road:
                    config['current_road'] = nearest_road
                    # Snap to middle of road
                    new_x = nearest_road.start_x + (nearest_road.end_x - nearest_road.start_x) * 0.5
                    new_y = nearest_road.start_y + (nearest_road.end_y - nearest_road.start_y) * 0.5
                    node.direction = nearest_road.direction
                    direction = nearest_road.direction
                    # Reset lane offset
                    node.lane_offset = 0
                    config['current_lane'] = 0
                    config['target_lane'] = None
                else:
                    # Hard clamp to safe area
                    new_x = max(60, min(3240, new_x))
                    new_y = max(60, min(3140, new_y))
            
            # Update position
            node.location = (new_x, new_y)
            node.last_update = current_time
            
            # Speed variation (traffic flow)
            if random.random() < 0.02 and not config['is_emergency']:
                node.speed = max(10, min(40, node.speed + random.uniform(-3, 3)))
            
            # Malicious vehicles exhibit erratic behavior
            if config['is_malicious'] and random.random() < 0.1:
                # Erratic speed changes
                node.speed = min(85, node.speed + random.uniform(10, 30))
                if hasattr(node, 'erratic_behavior_count'):
                    node.erratic_behavior_count += 1
                # Degrade trust over time for malicious behavior
                node.trust_score = max(0.05, node.trust_score * 0.95)
        
        # V2V COMMUNICATION - Process after all position updates
        self._process_v2v_communications(current_time)
    
    def _process_v2v_communications(self, current_time: float):
        """
        Process all V2V communications: collision detection, lane change alerts, 
        emergency broadcasts, brake warnings
        """
        # 1. Emergency vehicles broadcast alerts
        for vehicle_id, config in self.vehicle_configs.items():
            if config['is_emergency']:
                # Broadcast every 2 seconds
                if int(current_time * 10) % 20 == 0:
                    self.broadcast_emergency_alert(vehicle_id, current_time)
        
        # 2. Check collision risks for all vehicles
        for vehicle_id in self.app.vehicle_nodes.keys():
            if int(current_time * 10) % 5 == 0:  # Check every 0.5 seconds
                self.check_collision_risk(vehicle_id, current_time)
        
        # 3. Detect hard braking and broadcast warnings
        for vehicle_id, node in self.app.vehicle_nodes.items():
            if hasattr(node, 'speed'):
                # If speed dropped significantly (hard brake)
                if hasattr(node, 'prev_speed'):
                    speed_drop = node.prev_speed - node.speed
                    if speed_drop > 10:  # Hard braking threshold
                        self.broadcast_v2v_message(
                            vehicle_id,
                            'brake_warnings',
                            {
                                'speed': node.speed,
                                'deceleration': speed_drop
                            },
                            current_time
                        )
                node.prev_speed = node.speed
        
        # 4. Detect traffic jams (multiple slow vehicles in proximity)
        slow_vehicle_clusters = self._detect_traffic_jams(current_time)
        for cluster_center, count in slow_vehicle_clusters:
            if count >= 5:  # At least 5 slow vehicles
                # Find a vehicle in the jam to broadcast alert
                for vehicle_id, node in self.app.vehicle_nodes.items():
                    x, y = node.location
                    dist = math.sqrt((x - cluster_center[0])**2 + (y - cluster_center[1])**2)
                    if dist < 100 and node.speed < 15:
                        self.broadcast_v2v_message(
                            vehicle_id,
                            'traffic_jam_alerts',
                            {
                                'location': cluster_center,
                                'severity': count,
                                'average_speed': node.speed
                            },
                            current_time
                        )
                        break
    
    def _detect_traffic_jams(self, current_time: float):
        """Detect clusters of slow-moving vehicles (traffic jams)"""
        slow_vehicles = []
        
        for vehicle_id, node in self.app.vehicle_nodes.items():
            if node.speed < 15:  # Slow speed threshold
                x, y = node.location
                slow_vehicles.append((x, y))
        
        # Simple clustering: find groups of slow vehicles
        clusters = []
        for pos in slow_vehicles:
            # Count nearby slow vehicles
            nearby_count = sum(1 for other_pos in slow_vehicles 
                             if math.sqrt((pos[0] - other_pos[0])**2 + 
                                        (pos[1] - other_pos[1])**2) < 100)
            if nearby_count >= 5:
                clusters.append((pos, nearby_count))
        
        return clusters
    
    def run_simulation(self):
        """Run full simulation with consensus-based cluster elections"""
        print(f"Initializing {self.num_vehicles} vehicles in city network...")
        self.initialize_vehicles()
        
        # Enable consensus for cluster head elections
        print("🗳️  Enabling consensus-based cluster head elections...")
        self.app.consensus_enabled = True
        
        # Initialize consensus for initial cluster heads
        # Select high-trust, non-malicious vehicles as authorities
        authority_candidates = []
        for vehicle_id, node in self.app.vehicle_nodes.items():
            if not node.is_malicious and node.trust_score > 0.7:
                authority_candidates.append(vehicle_id)
                if len(authority_candidates) >= 5:  # Use 5 authority nodes
                    break
        
        if authority_candidates:
            # Initialize consensus with first authority as coordinator
            self.app.initialize_consensus(
                node_id=authority_candidates[0],
                consensus_type="hybrid",  # Use both Raft and PoA
                authority_nodes=authority_candidates
            )
            print(f"   ✓ Initialized consensus with {len(authority_candidates)} authority nodes")
            print(f"   ✓ Authorities: {', '.join(authority_candidates)}")
        
        # Store intersection data
        for intersection in self.intersections:
            self.animation_data['intersections'].append({
                'x': intersection.x,
                'y': intersection.y,
                'name': intersection.name
            })
        
        # Store road data
        for road in self.roads:
            self.animation_data['roads'].append({
                'start_x': road.start_x,
                'start_y': road.start_y,
                'end_x': road.end_x,
                'end_y': road.end_y,
                'direction': road.direction
            })
        
        current_time = 0.0
        frame_count = 0
        
        print(f"Running city simulation for {self.duration} seconds...")
        print(f"🗳️  Leader failure detection enabled (co-leader succession)")
        
        while current_time < self.duration:
            # Update traffic lights
            for intersection in self.intersections:
                intersection.update(self.timestep)
            
            # Update vehicles
            self.update_vehicle_positions(current_time)
            
            # Update clustering
            self.app.handle_timeStep(current_time)
            
            # Merge overlapping clusters to prevent sub-clustering
            if frame_count % 50 == 0:  # Every 5 seconds
                self._merge_overlapping_clusters(current_time)
            
            # Check for leader failures and handle succession/re-election
            self._check_leader_failures(current_time)
            
            # Elect boundary nodes for inter-cluster communication (every 30 seconds)
            if frame_count % 300 == 0:  # 0.1s timestep * 300 = every 30s
                self._elect_boundary_nodes(current_time)
            
            # PoA malicious detection (continuous monitoring)
            if frame_count % 100 == 0:  # Check every 10 seconds (0.1s timestep * 100)
                self._detect_malicious_nodes_poa(current_time)
            
            # Capture frame (every 5 frames to reduce size)
            if frame_count % 5 == 0:
                frame_data = self.capture_frame(current_time)
                self.animation_data['frames'].append(frame_data)
            
            if frame_count % 50 == 0:
                progress = (current_time / self.duration) * 100
                num_clusters = len(self.app.clustering_engine.clusters)
                consensus_msg = ""
                if hasattr(self.app, 'consensus_engine') and self.app.consensus_engine:
                    if hasattr(self.app.consensus_engine, 'raft') and self.app.consensus_engine.raft:
                        consensus_msg = f" - Raft: {self.app.consensus_engine.raft.state.value}"
                print(f"Progress: {progress:.1f}% - Time: {current_time:.1f}s - "
                      f"Clusters: {num_clusters}{consensus_msg}")
            
            current_time += self.timestep
            frame_count += 1
        
        print(f"Simulation complete! Captured {len(self.animation_data['frames'])} frames")
        self._print_consensus_statistics()
        return self.animation_data
    
    def _merge_overlapping_clusters(self, current_time: float):
        """Merge overlapping clusters to prevent sub-clustering"""
        MERGE_DISTANCE_THRESHOLD = 450  # If cluster centers are within 450 pixels, consider merging (matches max_cluster_radius)
        
        clusters_to_merge = []
        processed_clusters = set()
        
        cluster_list = list(self.app.clustering_engine.clusters.items())
        
        for i, (cluster_id_1, cluster_1) in enumerate(cluster_list):
            if cluster_id_1 in processed_clusters:
                continue
            
            if not cluster_1.member_ids or not cluster_1.head_id:
                continue
            
            # Get cluster 1 center (leader position)
            if cluster_1.head_id in self.app.vehicle_nodes:
                c1_x, c1_y = self.app.vehicle_nodes[cluster_1.head_id].location
            else:
                continue
            
            merge_candidates = []
            
            for j, (cluster_id_2, cluster_2) in enumerate(cluster_list[i+1:], start=i+1):
                if cluster_id_2 in processed_clusters:
                    continue
                
                if not cluster_2.member_ids or not cluster_2.head_id:
                    continue
                
                # Get cluster 2 center (leader position)
                if cluster_2.head_id in self.app.vehicle_nodes:
                    c2_x, c2_y = self.app.vehicle_nodes[cluster_2.head_id].location
                else:
                    continue
                
                # Calculate distance between cluster centers
                distance = math.sqrt((c1_x - c2_x)**2 + (c1_y - c2_y)**2)
                
                # Check if clusters overlap significantly
                if distance < MERGE_DISTANCE_THRESHOLD:
                    # Count how many members are shared or very close
                    shared_members = 0
                    for member_id in cluster_2.member_ids:
                        if member_id in cluster_1.member_ids:
                            shared_members += 1
                        elif member_id in self.app.vehicle_nodes:
                            member_x, member_y = self.app.vehicle_nodes[member_id].location
                            dist_to_c1 = math.sqrt((member_x - c1_x)**2 + (member_y - c1_y)**2)
                            if dist_to_c1 < 250:  # Within communication range of cluster 1
                                shared_members += 1
                    
                    # If significant overlap, mark for merging
                    overlap_ratio = shared_members / max(len(cluster_2.member_ids), 1)
                    if overlap_ratio > 0.3 or distance < 350:  # 30% overlap or very close (increased from 200)
                        merge_candidates.append(cluster_id_2)
            
            if merge_candidates:
                clusters_to_merge.append((cluster_id_1, merge_candidates))
                processed_clusters.add(cluster_id_1)
                processed_clusters.update(merge_candidates)
        
        # Perform merges
        for primary_cluster_id, secondary_cluster_ids in clusters_to_merge:
            if primary_cluster_id not in self.app.clustering_engine.clusters:
                continue
            
            primary_cluster = self.app.clustering_engine.clusters[primary_cluster_id]
            
            for secondary_id in secondary_cluster_ids:
                if secondary_id not in self.app.clustering_engine.clusters:
                    continue
                
                secondary_cluster = self.app.clustering_engine.clusters[secondary_id]
                
                # Merge members
                for member_id in secondary_cluster.member_ids:
                    if member_id not in primary_cluster.member_ids:
                        primary_cluster.member_ids.add(member_id)
                        
                        # Update vehicle's cluster assignment
                        if member_id in self.app.vehicle_nodes:
                            self.app.vehicle_nodes[member_id].cluster_id = primary_cluster_id
                
                # Remove the secondary cluster's head from being a head
                if secondary_cluster.head_id and secondary_cluster.head_id in self.app.vehicle_nodes:
                    self.app.vehicle_nodes[secondary_cluster.head_id].is_cluster_head = False
                    # Add to primary cluster as regular member if not already there
                    if secondary_cluster.head_id not in primary_cluster.member_ids:
                        primary_cluster.member_ids.add(secondary_cluster.head_id)
                        self.app.vehicle_nodes[secondary_cluster.head_id].cluster_id = primary_cluster_id
                
                # Delete the secondary cluster
                del self.app.clustering_engine.clusters[secondary_id]
                
            if current_time % 30 < 0.5:  # Log occasionally
                print(f"   🔗  Merged {len(secondary_cluster_ids)} overlapping clusters into {primary_cluster_id}")
    
    def _check_leader_failures(self, current_time: float):
        """Check for leader failures and handle co-leader succession or trigger re-election"""
        for cluster_id, cluster in list(self.app.clustering_engine.clusters.items()):
            if not cluster.head_id:
                continue
            
            # Initialize co-leader if not exists
            if not hasattr(cluster, 'co_leader_id'):
                cluster.co_leader_id = None
                cluster.last_leader_check = current_time
            
            # Check if leader is still valid
            leader_failed = False
            leader_failure_reason = ""
            
            # Check 1: Leader left cluster (out of range)
            if cluster.head_id not in self.app.vehicle_nodes:
                leader_failed = True
                leader_failure_reason = "left network"
            else:
                leader_node = self.app.vehicle_nodes[cluster.head_id]
                
                # Check 2: Leader became malicious
                if leader_node.is_malicious or leader_node.trust_score < 0.4:
                    leader_failed = True
                    leader_failure_reason = "low trust/malicious"
                else:
                    # Check 3: Leader moved out of cluster range
                    x, y = leader_node.location
                    dist_to_center = math.sqrt((x - cluster.centroid_x)**2 + 
                                              (y - cluster.centroid_y)**2)
                    if dist_to_center > 450:  # MAX_CLUSTER_RANGE
                        leader_failed = True
                        leader_failure_reason = "out of range"
            
            if leader_failed:
                if current_time % 30 < 0.5:  # Log occasionally
                    print(f"   ⚠️  Leader failure in {cluster_id}: {cluster.head_id} ({leader_failure_reason})")
                
                # Check if co-leader exists and is valid
                if cluster.co_leader_id and cluster.co_leader_id in self.app.vehicle_nodes:
                    co_leader_node = self.app.vehicle_nodes[cluster.co_leader_id]
                    
                    # Validate co-leader
                    if (not co_leader_node.is_malicious and 
                        co_leader_node.trust_score >= 0.5):
                        # CO-LEADER SUCCESSION: Co-leader takes over
                        old_leader = cluster.head_id
                        cluster.head_id = cluster.co_leader_id
                        cluster.co_leader_id = None  # Will be re-elected
                        
                        # Update node statuses
                        if old_leader in self.app.vehicle_nodes:
                            self.app.vehicle_nodes[old_leader].is_cluster_head = False
                        co_leader_node.is_cluster_head = True
                        
                        # Elect new co-leader
                        self._elect_co_leader(cluster, current_time)
                        
                        if current_time % 30 < 0.5:
                            print(f"   ✅  Co-leader succession: {cluster.co_leader_id} → Leader in {cluster_id}")
                        
                        self.app.statistics['head_elections'] = \
                            self.app.statistics.get('head_elections', 0) + 1
                        continue
                
                # BOTH LEADER AND CO-LEADER FAILED: Trigger full re-election
                if current_time % 30 < 0.5:
                    print(f"   🗳️  Triggering re-election for {cluster_id} (leader & co-leader unavailable)")
                
                self._run_cluster_election(cluster_id, cluster, current_time)
            
            # Elect co-leader if missing
            elif not cluster.co_leader_id:
                self._elect_co_leader(cluster, current_time)
            
            cluster.last_leader_check = current_time
    
    def _elect_co_leader(self, cluster: Cluster, current_time: float):
        """Elect a co-leader for the cluster (second-best candidate)"""
        # Get all members except current leader
        candidates = []
        
        for member_id in cluster.member_ids:
            if member_id == cluster.head_id or member_id not in self.app.vehicle_nodes:
                continue
            
            node = self.app.vehicle_nodes[member_id]
            
            # Skip malicious or low-trust nodes
            if node.is_malicious or node.trust_score < 0.5:
                continue
            
            x, y = node.location
            
            # Calculate composite score (same metrics as leader election)
            trust_metric = node.trust_score
            
            neighbors = len([m for m in cluster.member_ids 
                           if m != member_id and m in self.app.vehicle_nodes])
            connectivity_metric = min(1.0, neighbors / 10.0)
            
            stability_metric = max(0.0, 1.0 - (node.speed / 70.0))
            
            dist_to_center = math.sqrt((x - cluster.centroid_x)**2 + 
                                      (y - cluster.centroid_y)**2)
            centrality_metric = max(0.0, 1.0 - (dist_to_center / 300.0))
            
            tenure_metric = min(1.0, (current_time - cluster.formation_time) / 30.0)
            
            composite_score = (
                trust_metric * 0.30 +
                connectivity_metric * 0.25 +
                stability_metric * 0.20 +
                centrality_metric * 0.15 +
                tenure_metric * 0.10
            )
            
            candidates.append({
                'id': member_id,
                'score': composite_score
            })
        
        if candidates:
            # Select highest scoring candidate as co-leader
            candidates.sort(key=lambda c: c['score'], reverse=True)
            cluster.co_leader_id = candidates[0]['id']
            
            # Also elect relay nodes after co-leader is set
            self._elect_relay_nodes(cluster, current_time)
            
            if current_time % 30 < 0.5:  # Log occasionally
                print(f"   👔  Co-leader elected: {cluster.co_leader_id} in {cluster.id} "
                      f"(score: {candidates[0]['score']:.3f})")
    
    def _run_cluster_election(self, cluster_id: str, cluster: Cluster, current_time: float):
        """Run full leader election for a cluster (called only when leader fails)"""
        if len(cluster.member_ids) < 2:
            return
        
        # Get all valid cluster members
        all_members = list(cluster.member_ids)
        
        # STEP 1: Filter out malicious nodes
        trusted_authorities = []
        candidates = []
        
        for member_id in all_members:
            if member_id not in self.app.vehicle_nodes:
                continue
            
            node = self.app.vehicle_nodes[member_id]
            
            # High-trust nodes are authorities
            if node.trust_score > 0.8 and not node.is_malicious:
                trusted_authorities.append(member_id)
            
            # Eligible candidates
            if not node.is_malicious and node.trust_score >= 0.5:
                x, y = node.location
                
                # Calculate multi-metric score
                trust_metric = node.trust_score
                
                neighbors = len([m for m in all_members 
                               if m != member_id and m in self.app.vehicle_nodes])
                connectivity_metric = min(1.0, neighbors / 10.0)
                
                stability_metric = max(0.0, 1.0 - (node.speed / 70.0))
                
                dist_to_center = math.sqrt((x - cluster.centroid_x)**2 + 
                                          (y - cluster.centroid_y)**2)
                centrality_metric = max(0.0, 1.0 - (dist_to_center / 300.0))
                
                tenure_metric = min(1.0, (current_time - cluster.formation_time) / 30.0)
                
                composite_score = (
                    trust_metric * 0.30 +
                    connectivity_metric * 0.25 +
                    stability_metric * 0.20 +
                    centrality_metric * 0.15 +
                    tenure_metric * 0.10
                )
                
                candidates.append({
                    'id': member_id,
                    'score': composite_score
                })
        
        if not candidates:
            return
        
        # STEP 2: Raft-style voting with trust weighting
        votes = {}
        total_voting_power = sum(
            self.app.vehicle_nodes[c['id']].trust_score 
            for c in candidates if c['id'] in self.app.vehicle_nodes
        )
        
        for candidate in candidates:
            if candidate['id'] not in self.app.vehicle_nodes:
                continue
            node = self.app.vehicle_nodes[candidate['id']]
            vote_weight = node.trust_score / total_voting_power if total_voting_power > 0 else 1.0 / len(candidates)
            votes[candidate['id']] = vote_weight * candidate['score']
        
        # STEP 3: Select winner
        if votes:
            new_leader = max(votes.items(), key=lambda x: x[1])[0]
            old_leader = cluster.head_id
            
            # Update cluster
            cluster.head_id = new_leader
            if old_leader and old_leader in self.app.vehicle_nodes:
                self.app.vehicle_nodes[old_leader].is_cluster_head = False
                if old_leader in cluster.member_ids:
                    cluster.member_ids.remove(old_leader)
            
            if new_leader in cluster.member_ids:
                cluster.member_ids.remove(new_leader)
            
            # Update node status
            self.app.vehicle_nodes[new_leader].is_cluster_head = True
            
            # Elect co-leader
            self._elect_co_leader(cluster, current_time)
            
            # Elect relay nodes for multi-hop communication
            self._elect_relay_nodes(cluster, current_time)
            
            winner_score = votes[new_leader]
            vote_percentage = (winner_score / sum(votes.values())) * 100 if votes else 100
            
            if current_time % 30 < 0.5:
                print(f"   🗳️  Cluster {cluster_id}: Elected {new_leader} "
                      f"(score: {winner_score:.3f}, votes: {vote_percentage:.1f}%)")
            
            self.app.statistics['head_elections'] = \
                self.app.statistics.get('head_elections', 0) + 1
    
    def _elect_relay_nodes(self, cluster: Cluster, current_time: float):
        """Elect relay nodes for members outside direct DSRC range of leader"""
        if not cluster.head_id or cluster.head_id not in self.app.vehicle_nodes:
            return
        
        # Initialize relay nodes list if not exists
        if not hasattr(cluster, 'relay_nodes'):
            cluster.relay_nodes = set()
        
        leader_node = self.app.vehicle_nodes[cluster.head_id]
        leader_x, leader_y = leader_node.location
        
        # Find members outside direct DSRC range
        out_of_range_members = []
        in_range_members = []
        
        for member_id in cluster.member_ids:
            if member_id not in self.app.vehicle_nodes:
                continue
            
            member_node = self.app.vehicle_nodes[member_id]
            member_x, member_y = member_node.location
            
            # Check distance to leader
            dist_to_leader = math.sqrt((leader_x - member_x)**2 + (leader_y - member_y)**2)
            
            if dist_to_leader > self.communication_range:
                out_of_range_members.append({
                    'id': member_id,
                    'x': member_x,
                    'y': member_y,
                    'dist': dist_to_leader
                })
            else:
                in_range_members.append({
                    'id': member_id,
                    'x': member_x,
                    'y': member_y,
                    'node': member_node
                })
        
        # Clear old relay nodes
        cluster.relay_nodes.clear()
        
        if not out_of_range_members:
            # All members in range, no relays needed
            return
        
        # For each out-of-range member, find best relay from in-range members
        relay_count = 0
        for oor_member in out_of_range_members:
            best_relay = None
            best_relay_score = -1
            
            for ir_member in in_range_members:
                # Check if this in-range member can reach the out-of-range member
                dist = math.sqrt((oor_member['x'] - ir_member['x'])**2 + 
                               (oor_member['y'] - ir_member['y'])**2)
                
                if dist <= self.communication_range:
                    # Calculate relay quality score
                    node = ir_member['node']
                    
                    # Factors: trust, centrality, stability
                    trust_score = node.trust_score
                    
                    # Centrality - how well positioned (closer to center is better)
                    dist_to_center = math.sqrt(
                        (ir_member['x'] - cluster.centroid_x)**2 + 
                        (ir_member['y'] - cluster.centroid_y)**2
                    )
                    centrality_score = max(0.0, 1.0 - (dist_to_center / 300.0))
                    
                    # Stability - lower speed is more stable
                    stability_score = max(0.0, 1.0 - (node.speed / 70.0))
                    
                    # Coverage - how many out-of-range members can this relay reach
                    coverage_count = sum(1 for other_oor in out_of_range_members
                                       if math.sqrt((other_oor['x'] - ir_member['x'])**2 + 
                                                  (other_oor['y'] - ir_member['y'])**2) <= self.communication_range)
                    coverage_score = min(1.0, coverage_count / max(1, len(out_of_range_members)))
                    
                    # Composite relay score
                    relay_score = (
                        trust_score * 0.35 +
                        centrality_score * 0.25 +
                        stability_score * 0.20 +
                        coverage_score * 0.20
                    )
                    
                    if relay_score > best_relay_score:
                        best_relay_score = relay_score
                        best_relay = ir_member['id']
            
            if best_relay:
                cluster.relay_nodes.add(best_relay)
                relay_count += 1
        
        if relay_count > 0 and current_time % 30 < 0.5:
            print(f"   📡  Relay nodes elected in {cluster.id}: {relay_count} relays "
                  f"for {len(out_of_range_members)} out-of-range members")
    
    def _forward_message_through_relays(self, cluster: Cluster, message: Dict, 
                                        sender_id: str, current_time: float) -> List[str]:
        """Forward message through relay nodes to reach all cluster members"""
        if not hasattr(cluster, 'relay_nodes'):
            cluster.relay_nodes = set()
        
        # Track which members received the message
        recipients = set()
        
        # Get sender location
        if sender_id not in self.app.vehicle_nodes:
            return list(recipients)
        
        sender_node = self.app.vehicle_nodes[sender_id]
        sender_x, sender_y = sender_node.location
        
        # Direct recipients (in range of sender)
        for member_id in cluster.member_ids:
            if member_id == sender_id or member_id not in self.app.vehicle_nodes:
                continue
            
            member_node = self.app.vehicle_nodes[member_id]
            member_x, member_y = member_node.location
            
            dist = math.sqrt((sender_x - member_x)**2 + (sender_y - member_y)**2)
            if dist <= self.communication_range:
                recipients.add(member_id)
        
        # Relay forwarding for out-of-range members
        relayed_members = set()
        for relay_id in cluster.relay_nodes:
            if relay_id not in self.app.vehicle_nodes or relay_id == sender_id:
                continue
            
            relay_node = self.app.vehicle_nodes[relay_id]
            relay_x, relay_y = relay_node.location
            
            # Check if relay can receive from sender
            dist_to_sender = math.sqrt((sender_x - relay_x)**2 + (sender_y - relay_y)**2)
            if dist_to_sender > self.communication_range:
                continue
            
            # Relay forwards to members in its range
            for member_id in cluster.member_ids:
                if member_id in recipients or member_id == sender_id or member_id not in self.app.vehicle_nodes:
                    continue
                
                member_node = self.app.vehicle_nodes[member_id]
                member_x, member_y = member_node.location
                
                dist = math.sqrt((relay_x - member_x)**2 + (relay_y - member_y)**2)
                if dist <= self.communication_range:
                    relayed_members.add(member_id)
                    
                    # Track relay hop
                    self.v2v_stats['relay_hops'] = self.v2v_stats.get('relay_hops', 0) + 1
        
        recipients.update(relayed_members)
        return list(recipients)
    
    def _elect_boundary_nodes(self, current_time: float):
        """Elect boundary nodes at cluster edges for inter-cluster communication"""
        all_clusters = list(self.app.clustering_engine.clusters.items())
        
        if len(all_clusters) < 2:
            # Need at least 2 clusters for inter-cluster communication
            return
        
        for cluster_id, cluster in all_clusters:
            if not cluster.member_ids or not cluster.head_id:
                continue
            
            # Initialize boundary nodes if not exists
            if not hasattr(cluster, 'boundary_nodes'):
                cluster.boundary_nodes = {}  # {neighbor_cluster_id: boundary_node_id}
            
            # Find neighboring clusters (within extended range)
            INTER_CLUSTER_DETECTION_RANGE = 600  # 2x DSRC range for cluster proximity
            
            cluster_center_x = cluster.centroid_x
            cluster_center_y = cluster.centroid_y
            
            neighboring_clusters = []
            
            for other_cluster_id, other_cluster in all_clusters:
                if other_cluster_id == cluster_id:
                    continue
                
                if not other_cluster.member_ids:
                    continue
                
                # Calculate distance between cluster centers
                other_center_x = other_cluster.centroid_x
                other_center_y = other_cluster.centroid_y
                
                cluster_dist = math.sqrt(
                    (cluster_center_x - other_center_x)**2 + 
                    (cluster_center_y - other_center_y)**2
                )
                
                # Consider as neighbor if centers are within detection range
                if cluster_dist <= INTER_CLUSTER_DETECTION_RANGE:
                    neighboring_clusters.append({
                        'id': other_cluster_id,
                        'cluster': other_cluster,
                        'center_x': other_center_x,
                        'center_y': other_center_y,
                        'distance': cluster_dist
                    })
            
            # Clear old boundary nodes
            cluster.boundary_nodes.clear()
            
            if not neighboring_clusters:
                continue
            
            # For each neighboring cluster, elect the best boundary node
            for neighbor in neighboring_clusters:
                best_boundary_node = None
                best_boundary_score = -1
                
                for member_id in cluster.member_ids:
                    if member_id not in self.app.vehicle_nodes:
                        continue
                    
                    node = self.app.vehicle_nodes[member_id]
                    node_x, node_y = node.location
                    
                    # Calculate distance to neighboring cluster center
                    dist_to_neighbor = math.sqrt(
                        (node_x - neighbor['center_x'])**2 + 
                        (node_y - neighbor['center_y'])**2
                    )
                    
                    # Boundary node quality score
                    # Factors: proximity to neighbor, trust, connectivity, stability
                    
                    # Proximity to neighbor cluster (closer is better)
                    proximity_score = max(0.0, 1.0 - (dist_to_neighbor / INTER_CLUSTER_DETECTION_RANGE))
                    
                    # Trust score
                    trust_score = node.trust_score
                    
                    # Connectivity - how many nodes in own cluster can this node reach
                    own_cluster_connectivity = 0
                    for other_member_id in cluster.member_ids:
                        if other_member_id == member_id or other_member_id not in self.app.vehicle_nodes:
                            continue
                        other_node = self.app.vehicle_nodes[other_member_id]
                        other_x, other_y = other_node.location
                        dist = math.sqrt((node_x - other_x)**2 + (node_y - other_y)**2)
                        if dist <= self.communication_range:
                            own_cluster_connectivity += 1
                    
                    connectivity_score = min(1.0, own_cluster_connectivity / max(1, len(cluster.member_ids)))
                    
                    # Stability - lower speed is more stable
                    stability_score = max(0.0, 1.0 - (node.speed / 70.0))
                    
                    # Composite boundary node score
                    boundary_score = (
                        proximity_score * 0.40 +      # Most important: close to neighbor
                        trust_score * 0.30 +          # Reliable forwarding
                        connectivity_score * 0.20 +   # Well-connected in own cluster
                        stability_score * 0.10        # Stable position
                    )
                    
                    if boundary_score > best_boundary_score:
                        best_boundary_score = boundary_score
                        best_boundary_node = member_id
                
                if best_boundary_node:
                    cluster.boundary_nodes[neighbor['id']] = best_boundary_node
            
            # Log boundary node election
            if cluster.boundary_nodes and current_time % 30 < 0.5:
                print(f"   🔷  Boundary nodes elected in {cluster_id}: "
                      f"{len(cluster.boundary_nodes)} boundary nodes for "
                      f"{len(neighboring_clusters)} neighboring clusters")
    
    def _run_consensus_elections(self, current_time: float):
        """DEPRECATED: Old periodic election method - now using failure-based elections"""
        for cluster_id, cluster in list(self.app.clustering_engine.clusters.items()):
            if len(cluster.member_ids) < 2:
                continue
            
            # Get all cluster members including current head
            all_members = list(cluster.member_ids)
            if cluster.head_id and cluster.head_id not in all_members:
                all_members.append(cluster.head_id)
            
            # STEP 1: PoA-based malicious node detection
            # Authority nodes vote on which nodes are suspicious
            malicious_votes = {}
            trusted_authorities = []
            
            for member_id in all_members:
                if member_id in self.app.vehicle_nodes:
                    node = self.app.vehicle_nodes[member_id]
                    
                    # PoA: High-trust nodes act as authorities
                    if node.trust_score > 0.8 and not node.is_malicious:
                        trusted_authorities.append(member_id)
                    
                    # Detect suspicious behavior
                    if node.is_malicious or node.trust_score < 0.3:
                        malicious_votes[member_id] = malicious_votes.get(member_id, 0) + 1
            
            # Remove nodes flagged as malicious by authorities
            if malicious_votes:
                for suspected_id, vote_count in malicious_votes.items():
                    if vote_count >= len(trusted_authorities) * 0.51:  # Majority vote
                        if suspected_id in all_members:
                            all_members.remove(suspected_id)
                            self.app.statistics['malicious_detected'] = \
                                self.app.statistics.get('malicious_detected', 0) + 1
            
            # STEP 2: Multi-metric Raft-based leader election
            # Calculate composite scores for each candidate
            candidates = []
            for member_id in all_members:
                if member_id not in self.app.vehicle_nodes:
                    continue
                
                node = self.app.vehicle_nodes[member_id]
                if node.is_malicious or node.trust_score < 0.5:
                    continue
                
                # Multi-metric scoring (Raft compatibility)
                x, y = node.location
                
                # Metric 1: Trust score (0-1) - 30%
                trust_metric = node.trust_score
                
                # Metric 2: Connectivity (neighbors count) - 25%
                neighbors = len([m for m in all_members 
                               if m != member_id and m in self.app.vehicle_nodes])
                connectivity_metric = min(1.0, neighbors / 10.0)
                
                # Metric 3: Stability (lower speed variance = more stable) - 20%
                stability_metric = max(0.0, 1.0 - (node.speed / 70.0))  # Normalize by max speed
                
                # Metric 4: Centrality (distance to cluster center) - 15%
                dist_to_center = math.sqrt((x - cluster.centroid_x)**2 + 
                                          (y - cluster.centroid_y)**2)
                centrality_metric = max(0.0, 1.0 - (dist_to_center / 300.0))
                
                # Metric 5: Tenure (how long in cluster) - 10%
                tenure_metric = min(1.0, (current_time - cluster.formation_time) / 30.0)
                
                # Composite Raft score
                composite_score = (
                    trust_metric * 0.30 +
                    connectivity_metric * 0.25 +
                    stability_metric * 0.20 +
                    centrality_metric * 0.15 +
                    tenure_metric * 0.10
                )
                
                candidates.append({
                    'id': member_id,
                    'score': composite_score,
                    'trust': trust_metric,
                    'connectivity': connectivity_metric,
                    'stability': stability_metric,
                    'centrality': centrality_metric,
                    'tenure': tenure_metric
                })
            
            if not candidates:
                continue
            
            # STEP 3: Raft consensus voting
            # Each node votes based on their trust-weighted preference
            votes = {}
            total_voting_power = sum(c['trust'] for c in candidates)
            
            for candidate in candidates:
                # Vote weight based on trust score (PoA influence)
                vote_weight = candidate['trust'] / total_voting_power if total_voting_power > 0 else 1.0
                
                # Raft-style voting: highest composite score gets votes
                best_candidate = max(candidates, key=lambda x: x['score'])
                candidate_id = best_candidate['id']
                
                votes[candidate_id] = votes.get(candidate_id, 0) + vote_weight
            
            # STEP 4: Elect winner with majority
            if votes:
                # Sort by votes and select winner
                sorted_votes = sorted(votes.items(), key=lambda x: x[1], reverse=True)
                new_head = sorted_votes[0][0]
                vote_percentage = sorted_votes[0][1] * 100
                
                # Require majority (>50%) for election
                if vote_percentage >= 50:
                    # Update cluster head if changed
                    if new_head != cluster.head_id:
                        old_head = cluster.head_id
                        cluster.head_id = new_head
                        
                        # Update node properties
                        if old_head and old_head in self.app.vehicle_nodes:
                            self.app.vehicle_nodes[old_head].is_cluster_head = False
                        if new_head in self.app.vehicle_nodes:
                            self.app.vehicle_nodes[new_head].is_cluster_head = True
                        
                        self.app.statistics['head_elections'] = \
                            self.app.statistics.get('head_elections', 0) + 1
                        
                        # Log election details
                        elected = next(c for c in candidates if c['id'] == new_head)
                        if current_time % 30 < 0.5:  # Log every 30 seconds
                            print(f"   🗳️  Cluster {cluster_id[:8]}: Elected {new_head} "
                                  f"(score: {elected['score']:.3f}, votes: {vote_percentage:.1f}%)")
    
    def _detect_malicious_nodes_poa(self, current_time: float):
        """
        Proof of Authority (PoA) based malicious node detection
        Authority nodes monitor and flag suspicious behavior within their cluster
        Requires 30% of cluster authorities to flag a node
        """
        # Identify authority nodes (high trust, non-malicious) globally
        all_authority_nodes = []
        for vehicle_id, node in self.app.vehicle_nodes.items():
            if node.trust_score > 0.8 and not node.is_malicious:
                all_authority_nodes.append(vehicle_id)
        
        if len(all_authority_nodes) < 3:  # Need at least 3 authorities globally
            return
        
        # Cluster-based detection: authorities vote within their cluster
        # BUT also check nodes that aren't in any cluster (isolated/malicious nodes)
        suspicious_reports = {}  # vehicle_id -> {'votes': [...], 'cluster_authorities': count}
        
        # Track which vehicles are in clusters
        vehicles_in_clusters = set()
        for cluster in self.app.clustering_engine.clusters.values():
            vehicles_in_clusters.update(cluster.member_ids)
        
        # Check vehicles NOT in any cluster (likely malicious/isolated)
        isolated_malicious = []
        for vehicle_id, node in self.app.vehicle_nodes.items():
            if vehicle_id not in vehicles_in_clusters and node.is_malicious:
                isolated_malicious.append(vehicle_id)
        
        for cluster_id, cluster in self.app.clustering_engine.clusters.items():
            # Get authorities in this cluster
            cluster_authorities = [vid for vid in cluster.member_ids if vid in all_authority_nodes]
            
            if len(cluster_authorities) == 0:
                continue  # No authorities in this cluster
            
            # Evaluate each member of the cluster
            for vehicle_id in cluster.member_ids:
                if vehicle_id in cluster_authorities:
                    continue  # Don't evaluate authorities
                
                if vehicle_id not in self.app.vehicle_nodes:
                    continue
                
                node = self.app.vehicle_nodes[vehicle_id]
                
                # Calculate suspicion score once per vehicle
                suspicion_score = 0.0
                
                # Check 1: Trust score below threshold
                if node.trust_score < 0.4:
                    suspicion_score += 0.3
                
                # Check 2: Marked as malicious in system
                if node.is_malicious:
                    suspicion_score += 0.5
                
                # Check 3: Erratic behavior (rapid speed changes)
                if hasattr(node, 'speed') and node.speed > 75:  # Abnormally high speed
                    suspicion_score += 0.2
                
                # Check 4: Low message authenticity (if tracked)
                if hasattr(node, 'message_count'):
                    if node.message_count > 100 and node.trust_score < 0.5:
                        suspicion_score += 0.2
                
                # If suspicious, collect authority votes from cluster members
                if suspicion_score >= 0.5:
                    # Authorities in the SAME CLUSTER vote on this suspicious vehicle
                    for auth_id in cluster_authorities:
                        if auth_id not in self.app.vehicle_nodes:
                            continue
                        
                        if vehicle_id not in suspicious_reports:
                            suspicious_reports[vehicle_id] = {
                                'votes': [], 
                                'cluster_authorities': len(cluster_authorities)
                            }
                        suspicious_reports[vehicle_id]['votes'].append({
                            'authority': auth_id,
                            'suspicion': suspicion_score,
                            'timestamp': current_time,
                            'cluster': cluster_id
                        })
        
        # Handle isolated nodes (not in any cluster) - use NEARBY cluster authorities
        for vehicle_id in isolated_malicious:
            if vehicle_id not in self.app.vehicle_nodes:
                continue
            
            node = self.app.vehicle_nodes[vehicle_id]
            x, y = node.location
            
            # Find nearby authorities from ANY cluster
            nearby_authorities = []
            for auth_id in all_authority_nodes:
                if auth_id not in self.app.vehicle_nodes:
                    continue
                auth_node = self.app.vehicle_nodes[auth_id]
                auth_x, auth_y = auth_node.location
                
                # Check if within range (300 pixels)
                distance = ((x - auth_x)**2 + (y - auth_y)**2)**0.5
                if distance < 300:
                    nearby_authorities.append(auth_id)
            
            if len(nearby_authorities) == 0:
                continue  # No nearby authorities
            
            # Calculate suspicion score
            suspicion_score = 0.0
            if node.trust_score < 0.4:
                suspicion_score += 0.3
            if node.is_malicious:
                suspicion_score += 0.5
            if hasattr(node, 'speed') and node.speed > 75:
                suspicion_score += 0.2
            if hasattr(node, 'message_count'):
                if node.message_count > 100 and node.trust_score < 0.5:
                    suspicion_score += 0.2
            
            # If suspicious, collect votes from nearby authorities
            if suspicion_score >= 0.5:
                if vehicle_id not in suspicious_reports:
                    suspicious_reports[vehicle_id] = {
                        'votes': [],
                        'cluster_authorities': len(nearby_authorities)
                    }
                for auth_id in nearby_authorities:
                    suspicious_reports[vehicle_id]['votes'].append({
                        'authority': auth_id,
                        'suspicion': suspicion_score,
                        'timestamp': current_time,
                        'cluster': 'isolated'
                    })
        
        # PoA Consensus: Flag nodes with 30% of CLUSTER authorities voting
        for vehicle_id, report_data in suspicious_reports.items():
            votes = report_data['votes']
            cluster_auth_count = report_data['cluster_authorities']
            majority_threshold = max(1, int(cluster_auth_count * 0.3))  # 30% of cluster authorities
            
            if len(votes) >= majority_threshold:
                node = self.app.vehicle_nodes[vehicle_id]
                
                # Reduce trust score
                old_trust = node.trust_score
                node.trust_score = max(0.05, node.trust_score * 0.7)  # 30% trust penalty
                
                # Mark as detected if not already
                if not hasattr(node, 'flagged_by_poa') or not node.flagged_by_poa:
                    node.flagged_by_poa = True
                    self.app.statistics['malicious_detected'] = \
                        self.app.statistics.get('malicious_detected', 0) + 1
                    
                    if current_time % 30 < 0.5:  # Log detections periodically
                        print(f"   ⚠️  PoA Detection: {vehicle_id} flagged as malicious "
                              f"(trust: {old_trust:.2f} → {node.trust_score:.2f}, "
                              f"cluster votes: {len(votes)}/{cluster_auth_count})")
                
                # Remove from cluster head position if currently head
                if node.is_cluster_head:
                    node.is_cluster_head = False
                    for cluster in self.app.clustering_engine.clusters.values():
                        if cluster.head_id == vehicle_id:
                            cluster.head_id = None  # Force re-election
    
    def _print_consensus_statistics(self):
        """Print consensus and election statistics"""
        print("\n" + "="*70)
        print("🗳️  CONSENSUS-BASED CLUSTER HEAD ELECTION STATISTICS")
        print("="*70)
        print(f"Algorithm: Hybrid (Raft + PoA)")
        print(f"Total head elections: {self.app.statistics.get('head_elections', 0)}")
        print(f"Malicious nodes detected (PoA): {self.app.statistics.get('malicious_detected', 0)}")
        print(f"Trust updates: {self.app.statistics.get('trust_updates', 0)}")
        
        # Raft consensus info
        if hasattr(self.app, 'consensus_engine') and self.app.consensus_engine:
            if hasattr(self.app.consensus_engine, 'raft') and self.app.consensus_engine.raft:
                print(f"\n📊 Raft Consensus:")
                print(f"   State: {self.app.consensus_engine.raft.state.value}")
                print(f"   Current term: {self.app.consensus_engine.raft.current_term}")
                print(f"   Cluster nodes: {len(self.app.consensus_engine.raft.cluster_nodes)}")
        
        # PoA authority info
        authority_count = sum(1 for node in self.app.vehicle_nodes.values() 
                             if node.trust_score > 0.8 and not node.is_malicious)
        print(f"\n🛡️  Proof of Authority (PoA):")
        print(f"   Active authorities: {authority_count}")
        print(f"   Authority threshold: 0.8 trust score")
        
        # Trust distribution
        trust_scores = [node.trust_score for node in self.app.vehicle_nodes.values()]
        if trust_scores:
            avg_trust = sum(trust_scores) / len(trust_scores)
            print(f"\n📈 Trust Distribution:")
            print(f"   Average trust score: {avg_trust:.3f}")
            print(f"   High trust nodes (>0.7): {sum(1 for t in trust_scores if t > 0.7)}")
            print(f"   Medium trust (0.4-0.7): {sum(1 for t in trust_scores if 0.4 <= t <= 0.7)}")
            print(f"   Low trust nodes (<0.4): {sum(1 for t in trust_scores if t < 0.4)}")
            
        # Malicious node stats
        malicious_count = sum(1 for node in self.app.vehicle_nodes.values() if node.is_malicious)
        flagged_count = sum(1 for node in self.app.vehicle_nodes.values() 
                           if hasattr(node, 'flagged_by_poa') and node.flagged_by_poa)
        print(f"\n🚨 Security:")
        print(f"   Known malicious: {malicious_count}")
        print(f"   Flagged by PoA: {flagged_count}")
        print(f"   Detection rate: {(flagged_count/max(1,malicious_count)*100):.1f}%")
        
        # V2V Communication stats
        print(f"\n📡 V2V Communication:")
        print(f"   Total messages: {self.v2v_stats['total_messages']}")
        print(f"   Collision warnings: {self.v2v_stats['collision_warnings']}")
        print(f"   Lane change alerts: {self.v2v_stats['lane_change_alerts']}")
        print(f"   Emergency alerts: {self.v2v_stats['emergency_alerts']}")
        print(f"   Brake warnings: {self.v2v_stats['brake_warnings']}")
        print(f"   Traffic jam alerts: {self.v2v_stats['traffic_jam_alerts']}")
        print(f"   Communication range: {self.communication_range} pixels")
        
        # Relay node stats
        total_relay_nodes = sum(len(c.relay_nodes) if hasattr(c, 'relay_nodes') else 0 
                               for c in self.app.clustering_engine.clusters.values())
        print(f"\n🔁 Multi-Hop Relay System:")
        print(f"   Total relay nodes: {total_relay_nodes}")
        print(f"   Relayed messages: {self.v2v_stats.get('relayed_messages', 0)}")
        print(f"   Relay hops: {self.v2v_stats.get('relay_hops', 0)}")
        if self.v2v_stats.get('relayed_messages', 0) > 0:
            avg_hops = self.v2v_stats.get('relay_hops', 0) / self.v2v_stats.get('relayed_messages', 1)
            print(f"   Average hops per relayed message: {avg_hops:.2f}")
        
        # Boundary node stats (inter-cluster communication)
        total_boundary_nodes = sum(len(c.boundary_nodes) if hasattr(c, 'boundary_nodes') else 0 
                                  for c in self.app.clustering_engine.clusters.values())
        clusters_with_boundary = sum(1 for c in self.app.clustering_engine.clusters.values()
                                     if hasattr(c, 'boundary_nodes') and c.boundary_nodes)
        print(f"\n🔷 Inter-Cluster Boundary Nodes:")
        print(f"   Total boundary nodes: {total_boundary_nodes}")
        print(f"   Clusters with boundary nodes: {clusters_with_boundary}")
        print(f"   Inter-cluster messages: {self.v2v_stats.get('inter_cluster_messages', 0)}")
        if total_boundary_nodes > 0:
            avg_boundary_per_cluster = total_boundary_nodes / max(1, clusters_with_boundary)
            print(f"   Average boundary nodes per cluster: {avg_boundary_per_cluster:.1f}")
        
        print("="*70)
    
    def capture_frame(self, current_time: float) -> Dict:
        """Capture current state"""
        vehicles = []
        clusters = []
        traffic_lights = []
        
        # Capture vehicles with role information
        for vehicle_id, node in self.app.vehicle_nodes.items():
            x, y = node.location
            config = self.vehicle_configs[vehicle_id]
            
            # Determine vehicle role in cluster
            role = 'member'  # default
            is_relay = False
            is_boundary = False
            is_co_leader = False
            
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
            
            vehicles.append({
                'id': vehicle_id,
                'x': x,
                'y': y,
                'speed': node.speed,
                'direction': node.direction,
                'cluster_id': node.cluster_id,
                'is_cluster_head': node.is_cluster_head,
                'is_co_leader': is_co_leader,
                'is_relay': is_relay,
                'is_boundary': is_boundary,
                'role': role,
                'trust_score': node.trust_score,
                'is_malicious': node.is_malicious,
                'is_emergency': config['is_emergency'],
                'waiting': config['waiting_at_light'],
                'type': config['type']
            })
        
        # Capture clusters with limited range (max 3 blocks = 900 pixels)
        # Center clusters on the LEADER position
        MAX_CLUSTER_RANGE = 450  # 1.5 blocks radius (3 blocks diameter)
        
        for cluster_id, cluster in self.app.clustering_engine.clusters.items():
            if cluster.member_ids and cluster.head_id:
                # Get leader position
                if cluster.head_id in self.app.vehicle_nodes:
                    leader_node = self.app.vehicle_nodes[cluster.head_id]
                    center_x, center_y = leader_node.location
                else:
                    # Fallback to geometric center if leader not found
                    member_positions = [
                        self.app.vehicle_nodes[vid].location 
                        for vid in cluster.member_ids 
                        if vid in self.app.vehicle_nodes
                    ]
                    if not member_positions:
                        continue
                    center_x = sum(p[0] for p in member_positions) / len(member_positions)
                    center_y = sum(p[1] for p in member_positions) / len(member_positions)
                
                # Calculate radius from leader position
                member_positions = [
                    self.app.vehicle_nodes[vid].location 
                    for vid in cluster.member_ids 
                    if vid in self.app.vehicle_nodes
                ]
                
                if member_positions:
                    calculated_radius = max(
                        math.sqrt((p[0] - center_x)**2 + (p[1] - center_y)**2)
                        for p in member_positions
                    ) + 40
                    
                    # Enforce maximum cluster range
                    radius = min(calculated_radius, MAX_CLUSTER_RANGE)
                    
                    # Get special node counts
                    relay_count = len(cluster.relay_nodes) if hasattr(cluster, 'relay_nodes') else 0
                    boundary_count = len(cluster.boundary_nodes) if hasattr(cluster, 'boundary_nodes') else 0
                    
                    clusters.append({
                        'id': cluster_id,
                        'center_x': center_x,
                        'center_y': center_y,
                        'radius': radius,
                        'size': len(cluster.member_ids),
                        'leader_id': cluster.head_id,
                        'co_leader_id': cluster.co_leader_id if hasattr(cluster, 'co_leader_id') else None,
                        'relay_count': relay_count,
                        'boundary_count': boundary_count
                    })
        
        # Capture traffic light states
        for intersection in self.intersections:
            for direction, light in intersection.lights.items():
                traffic_lights.append({
                    'x': light.x,
                    'y': light.y,
                    'state': light.state,
                    'direction': direction
                })
        
        # Capture recent V2V messages (last 50 for this frame)
        recent_v2v = [msg for msg in self.v2v_messages 
                     if abs(msg['time'] - current_time) < 1.0][-50:]
        
        return {
            'time': current_time,
            'vehicles': vehicles,
            'clusters': clusters,
            'traffic_lights': traffic_lights,
            'v2v_messages': recent_v2v,  # Include V2V messages in frame
            'stats': {
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
        }
    
    def export_html(self, filename='city_traffic_animation.html'):
        """Export as HTML"""
        # First save JSON data
        with open('city_animation_data.json', 'w') as f:
            json.dump(self.animation_data, f)
        
        print(f"\n✅ Animation data exported to: city_animation_data.json")
        print(f"📊 Total frames: {len(self.animation_data['frames'])}")
        print(f"⏱️  Duration: {self.duration}s")
        print(f"🚦 Intersections: {len(self.intersections)}")
        print(f"🛣️  Roads: {len(self.roads)}")
        print(f"\n✅ HTML file will be: {filename}")


if __name__ == '__main__':
    print("🗽 Times Square NYC-Style VANET Traffic Simulation �")
    print("=" * 70)
    
    simulator = CityVANETSimulator(
        num_vehicles=150,  # Increased to 150 vehicles for 11x11 grid
        duration=120,      # 2 minutes simulation
        timestep=0.1
    )
    
    animation_data = simulator.run_simulation()
    simulator.export_html()
    
    print("\n✅ Done! Now open city_traffic_animation.html to see Times Square traffic!")
