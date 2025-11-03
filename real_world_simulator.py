#!/usr/bin/env python3
"""
Real-World Location-Based VANET Simulation

Uses OpenStreetMap data to simulate VANET clustering on actual city streets.
Supports any location worldwide!

Examples:
- Times Square, New York: "Times Square, Manhattan, New York, USA"
- Shibuya Crossing, Tokyo: "Shibuya Crossing, Tokyo, Japan"
- Connaught Place, Delhi: "Connaught Place, New Delhi, India"
- Piccadilly Circus, London: "Piccadilly Circus, London, UK"
"""

import json
import random
import math
import sys
import os
from typing import List, Dict, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

# Add src to path
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    import osmnx as ox
    import networkx as nx
    import folium
    OSM_AVAILABLE = True
except ImportError:
    print("Warning: OSMnx not available. Using preset locations.")
    OSM_AVAILABLE = False

from src.custom_vanet_appl import CustomVANETApplication
from src.clustering import ClusteringAlgorithm


# Preset famous locations if OSMnx not available
PRESET_LOCATIONS = {
    'times_square': {
        'name': 'Times Square, New York',
        'center': (40.758, -73.985),
        'nodes': [
            (40.758, -73.985), (40.759, -73.985), (40.758, -73.986),
            (40.757, -73.985), (40.758, -73.984)
        ],
        'edges': [
            ((40.758, -73.985), (40.759, -73.985)),
            ((40.758, -73.985), (40.757, -73.985)),
            ((40.758, -73.985), (40.758, -73.986)),
            ((40.758, -73.985), (40.758, -73.984)),
        ]
    },
    'connaught_place': {
        'name': 'Connaught Place, New Delhi',
        'center': (28.6315, 77.2167),
        'nodes': [
            (28.6315, 77.2167), (28.6325, 77.2167), (28.6315, 77.2177),
            (28.6305, 77.2167), (28.6315, 77.2157)
        ],
        'edges': [
            ((28.6315, 77.2167), (28.6325, 77.2167)),
            ((28.6315, 77.2167), (28.6305, 77.2167)),
            ((28.6315, 77.2167), (28.6315, 77.2177)),
            ((28.6315, 77.2167), (28.6315, 77.2157)),
        ]
    }
}


class RealWorldVANETSimulator:
    """VANET simulation using real-world map data"""
    
    def __init__(self, location: str = 'times_square', num_vehicles: int = 25, 
                 duration: float = 60, timestep: float = 0.2):
        self.location_query = location
        self.num_vehicles = num_vehicles
        self.duration = duration
        self.timestep = timestep
        
        self.app = CustomVANETApplication(ClusteringAlgorithm.MOBILITY_BASED)
        self.app.trust_enabled = True
        
        # Load map data
        self.load_map_data()
        
        # Coordinate scaling (lat/lon to pixels)
        self.scale_x = 50000  # Adjust based on location
        self.scale_y = 50000
        self.offset_x = 600
        self.offset_y = 350
        
        self.animation_data = {
            'frames': [],
            'vehicles': {},
            'roads': [],
            'intersections': [],
            'metadata': {
                'location': location,
                'duration': duration,
                'timestep': timestep,
                'num_vehicles': num_vehicles
            }
        }
    
    def load_map_data(self):
        """Load real map data from OpenStreetMap"""
        print(f"\n🗺️  Loading map data for: {self.location_query}")
        
        if OSM_AVAILABLE and self.location_query not in PRESET_LOCATIONS:
            try:
                # Download street network
                print("Downloading from OpenStreetMap...")
                G = ox.graph_from_place(
                    self.location_query,
                    network_type='drive',
                    simplify=True
                )
                
                # Convert to undirected for simplicity
                G = ox.convert.to_undirected(G)
                
                self.graph = G
                self.nodes = list(G.nodes(data=True))
                self.edges = list(G.edges(data=True))
                
                print(f"✅ Loaded {len(self.nodes)} nodes and {len(self.edges)} edges")
                
                # Get bounding box
                lats = [data['y'] for _, data in self.nodes]
                lons = [data['x'] for _, data in self.nodes]
                self.center_lat = sum(lats) / len(lats)
                self.center_lon = sum(lons) / len(lons)
                
                print(f"Center: ({self.center_lat:.4f}, {self.center_lon:.4f})")
                
            except Exception as e:
                print(f"⚠️  Error loading OSM data: {e}")
                print("Using preset location instead...")
                self._load_preset()
        else:
            self._load_preset()
    
    def _load_preset(self):
        """Load preset location data"""
        if self.location_query in PRESET_LOCATIONS:
            preset = PRESET_LOCATIONS[self.location_query]
        else:
            print(f"Unknown location '{self.location_query}', using Times Square")
            preset = PRESET_LOCATIONS['times_square']
        
        print(f"📍 Using preset: {preset['name']}")
        
        self.center_lat, self.center_lon = preset['center']
        self.nodes = [(i, {'y': lat, 'x': lon}) for i, (lat, lon) in enumerate(preset['nodes'])]
        self.edges = [
            (preset['nodes'].index(e[0]), preset['nodes'].index(e[1]), {})
            for e in preset['edges']
        ]
        
        print(f"✅ Loaded {len(self.nodes)} nodes and {len(self.edges)} edges")
    
    def lat_lon_to_pixel(self, lat: float, lon: float) -> Tuple[float, float]:
        """Convert lat/lon to pixel coordinates"""
        x = (lon - self.center_lon) * self.scale_x + self.offset_x
        y = (self.center_lat - lat) * self.scale_y + self.offset_y  # Flip Y
        return (x, y)
    
    def initialize_vehicles(self):
        """Place vehicles on real roads"""
        print("\n🚗 Initializing vehicles on real roads...")
        
        vehicle_configs = []
        
        for i in range(self.num_vehicles):
            # Choose random edge (road segment)
            if len(self.edges) == 0:
                print("⚠️  No edges available!")
                return
            
            edge = random.choice(self.edges)
            u, v = edge[0], edge[1]
            
            # Get node coordinates
            u_data = next(data for node, data in self.nodes if node == u)
            v_data = next(data for node, data in self.nodes if node == v)
            
            # Position along edge
            progress = random.random()
            lat = u_data['y'] + (v_data['y'] - u_data['y']) * progress
            lon = u_data['x'] + (v_data['x'] - u_data['x']) * progress
            
            # Convert to pixel coordinates
            x, y = self.lat_lon_to_pixel(lat, lon)
            
            # Calculate direction
            dx = v_data['x'] - u_data['x']
            dy = v_data['y'] - u_data['y']
            direction = math.degrees(math.atan2(dy, dx))
            
            # Speed variation
            speed = random.uniform(20, 35)
            
            # Vehicle types
            vehicle_type = random.choice(['car'] * 8 + ['truck'] + ['emergency'])
            is_emergency = (vehicle_type == 'emergency')
            is_malicious = (i % 7 == 0) and not is_emergency
            
            vehicle_id = f'v{i}'
            self.app.add_vehicle(
                vehicle_id=vehicle_id,
                x=x, y=y,
                speed=speed,
                direction=direction,
                lane_id=f'edge_{self.edges.index(edge)}'
            )
            
            vehicle_configs.append({
                'id': vehicle_id,
                'type': vehicle_type,
                'is_emergency': is_emergency,
                'is_malicious': is_malicious,
                'current_edge': edge,
                'target_node': v
            })
            
            # Configure node
            node = self.app.vehicle_nodes[vehicle_id]
            node.vehicle_type = vehicle_type
            
            if is_malicious:
                node.is_malicious = True
                node.trust_score = 0.25
            elif is_emergency:
                node.trust_score = 1.0
        
        self.vehicle_configs = {vc['id']: vc for vc in vehicle_configs}
        print(f"✅ Placed {len(vehicle_configs)} vehicles on road network")
    
    def update_vehicle_positions(self, current_time: float):
        """Update vehicles following real road network"""
        for vehicle_id, node in self.app.vehicle_nodes.items():
            config = self.vehicle_configs[vehicle_id]
            x, y = node.location
            speed = node.speed
            direction = node.direction
            
            # Move along current direction
            rad = math.radians(direction)
            dx = math.cos(rad) * speed * self.timestep * 0.01  # Scale for lat/lon
            dy = math.sin(rad) * speed * self.timestep * 0.01
            
            new_x = x + dx
            new_y = y + dy
            
            # Check if reached end of road segment
            target_data = next((data for n, data in self.nodes if n == config['target_node']), None)
            if target_data:
                target_x, target_y = self.lat_lon_to_pixel(target_data['y'], target_data['x'])
                dist_to_target = math.sqrt((new_x - target_x)**2 + (new_y - target_y)**2)
                
                # If close to target node, choose new edge
                if dist_to_target < 20:
                    # Find connected edges
                    connected_edges = [e for e in self.edges if e[0] == config['target_node']]
                    if connected_edges:
                        new_edge = random.choice(connected_edges)
                        config['current_edge'] = new_edge
                        config['target_node'] = new_edge[1]
                        
                        # Update direction
                        u_data = next(data for n, data in self.nodes if n == new_edge[0])
                        v_data = next(data for n, data in self.nodes if n == new_edge[1])
                        dx_new = v_data['x'] - u_data['x']
                        dy_new = v_data['y'] - u_data['y']
                        node.direction = math.degrees(math.atan2(dy_new, dx_new))
            
            # Update position
            node.location = (new_x, new_y)
            node.last_update = current_time
            
            # Speed variation
            if random.random() < 0.03:
                if config['is_emergency']:
                    node.speed = min(50, node.speed + random.uniform(-2, 3))
                else:
                    node.speed = max(15, min(40, node.speed + random.uniform(-2, 2)))
    
    def run_simulation(self):
        """Run full simulation"""
        print(f"\n▶️  Running simulation for {self.duration}s...")
        
        self.initialize_vehicles()
        
        # Store road network for visualization
        for edge in self.edges[:50]:  # Limit to 50 edges for performance
            u, v = edge[0], edge[1]
            u_data = next((data for node, data in self.nodes if node == u), None)
            v_data = next((data for node, data in self.nodes if node == v), None)
            
            if u_data and v_data:
                x1, y1 = self.lat_lon_to_pixel(u_data['y'], u_data['x'])
                x2, y2 = self.lat_lon_to_pixel(v_data['y'], v_data['x'])
                
                self.animation_data['roads'].append({
                    'x1': x1, 'y1': y1,
                    'x2': x2, 'y2': y2
                })
        
        # Store intersections
        for node, data in self.nodes[:20]:  # Limit to 20 nodes
            x, y = self.lat_lon_to_pixel(data['y'], data['x'])
            self.animation_data['intersections'].append({
                'x': x, 'y': y,
                'id': str(node)
            })
        
        current_time = 0.0
        frame_count = 0
        
        while current_time < self.duration:
            # Update vehicles
            self.update_vehicle_positions(current_time)
            
            # Update clustering
            self.app.handle_timeStep(current_time)
            
            # Capture frame
            if frame_count % 5 == 0:
                frame_data = self.capture_frame(current_time)
                self.animation_data['frames'].append(frame_data)
            
            if frame_count % 50 == 0:
                progress = (current_time / self.duration) * 100
                clusters = len(self.app.clustering_engine.clusters)
                print(f"  {progress:5.1f}% | Time: {current_time:5.1f}s | Clusters: {clusters}")
            
            current_time += self.timestep
            frame_count += 1
        
        print(f"\n✅ Simulation complete! {len(self.animation_data['frames'])} frames captured")
        return self.animation_data
    
    def capture_frame(self, current_time: float) -> Dict:
        """Capture current simulation state"""
        vehicles = []
        clusters = []
        
        for vehicle_id, node in self.app.vehicle_nodes.items():
            x, y = node.location
            config = self.vehicle_configs[vehicle_id]
            
            vehicles.append({
                'id': vehicle_id,
                'x': x, 'y': y,
                'speed': node.speed,
                'direction': node.direction,
                'cluster_id': node.cluster_id,
                'is_cluster_head': node.is_cluster_head,
                'trust_score': node.trust_score,
                'is_malicious': node.is_malicious,
                'is_emergency': config['is_emergency'],
                'type': config['type']
            })
        
        for cluster_id, cluster in self.app.clustering_engine.clusters.items():
            if cluster.member_ids:
                positions = [
                    self.app.vehicle_nodes[vid].location 
                    for vid in cluster.member_ids 
                    if vid in self.app.vehicle_nodes
                ]
                
                if positions:
                    cx = sum(p[0] for p in positions) / len(positions)
                    cy = sum(p[1] for p in positions) / len(positions)
                    radius = max(
                        math.sqrt((p[0] - cx)**2 + (p[1] - cy)**2)
                        for p in positions
                    ) + 30
                    
                    clusters.append({
                        'id': cluster_id,
                        'center_x': cx,
                        'center_y': cy,
                        'radius': radius,
                        'size': len(cluster.member_ids)
                    })
        
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
    
    def export_data(self, filename='real_location_animation.json'):
        """Export animation data"""
        with open(filename, 'w') as f:
            json.dump(self.animation_data, f)
        
        print(f"\n💾 Data exported to: {filename}")
        print(f"   📍 Location: {self.location_query}")
        print(f"   🛣️  Roads: {len(self.animation_data['roads'])}")
        print(f"   🚦 Intersections: {len(self.animation_data['intersections'])}")
        print(f"   🎬 Frames: {len(self.animation_data['frames'])}")
        
        return filename


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Real-World VANET Simulation')
    parser.add_argument('--location', type=str, default='times_square',
                       help='Location (e.g., "Times Square, New York" or preset: times_square, connaught_place)')
    parser.add_argument('--vehicles', type=int, default=25,
                       help='Number of vehicles')
    parser.add_argument('--duration', type=float, default=60,
                       help='Simulation duration (seconds)')
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("🌍 REAL-WORLD LOCATION-BASED VANET SIMULATION")
    print("=" * 70)
    
    simulator = RealWorldVANETSimulator(
        location=args.location,
        num_vehicles=args.vehicles,
        duration=args.duration
    )
    
    simulator.run_simulation()
    simulator.export_data('real_location_animation.json')
    
    print("\n✅ All done! Use the HTML viewer to see the animation.")


if __name__ == '__main__':
    main()
