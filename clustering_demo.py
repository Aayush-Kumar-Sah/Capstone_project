#!/usr/bin/env python3
"""
VANET Clustering Integration Script

This script demonstrates how to integrate the clustering system with the existing
VANET simulation, showing cluster formation, maintenance, and visualization.
"""

import sys
import os
import time
import logging
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from src.custom_vanet_appl import CustomVANETApplication
from src.clustering import ClusteringAlgorithm
from src.clustering_visualization import ClusterVisualizer, VisualizationConfig
from src.message_processor import MessageType

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Changed to DEBUG for troubleshooting
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('clustering_demo.log'),
        logging.StreamHandler()
    ]
)

class ClusteringDemo:
    """Demonstrates VANET clustering functionality"""
    
    def __init__(self, algorithm: ClusteringAlgorithm = ClusteringAlgorithm.MOBILITY_BASED):
        self.logger = logging.getLogger(__name__)
        
        # Initialize VANET application with clustering
        self.vanet_app = CustomVANETApplication(algorithm)
        self.vanet_app.initialize()
        
        # Configure clustering parameters for better cluster formation
        self.vanet_app.set_configuration({
            'enable_clustering': True,
            'cluster_announcement_interval': 2.0,
            'heartbeat_interval': 1.5
        })
        
        # Adjust clustering algorithm parameters for demo
        clustering_engine = self.vanet_app.clustering_engine
        clustering_engine.max_cluster_radius = 150.0  # Reduced from 300.0
        clustering_engine.speed_threshold = 8.0       # Increased from 5.0
        clustering_engine.direction_threshold = 1.0   # Increased from 0.5
        
        # Initialize visualization
        viz_config = VisualizationConfig()
        viz_config.show_performance_overlay = True
        self.visualizer = ClusterVisualizer(self.vanet_app, viz_config)
        
        # Demo parameters
        self.simulation_time = 0.0
        self.step_size = 0.1  # 100ms steps
        self.demo_duration = 120.0  # 2 minutes
        
        self.logger.info(f"Clustering demo initialized with {algorithm.value} algorithm")
    
    def create_demo_scenario(self):
        """Create a demonstration scenario with multiple vehicles"""
        self.logger.info("Creating demo scenario with vehicles")
        
        # Highway scenario: vehicles in multiple lanes with different speeds
        scenarios = [
            # Lane 1: Fast vehicles going east (closer spacing for clustering)
            {"lane": "lane1", "base_speed": 25.0, "direction": 0.0, "count": 15, "spacing": 25.0},
            # Lane 2: Medium speed vehicles going east (closer spacing)
            {"lane": "lane2", "base_speed": 20.0, "direction": 0.0, "count": 12, "spacing": 20.0},
            # Lane 3: Slower vehicles going west (closer spacing)
            {"lane": "lane3", "base_speed": 18.0, "direction": 3.14159, "count": 10, "spacing": 30.0},
            # Intersection area: mixed directions (closer spacing)
            {"lane": "intersection", "base_speed": 15.0, "direction": 1.57, "count": 8, "spacing": 15.0}
        ]
        
        vehicle_id = 0
        for scenario in scenarios:
            for i in range(scenario["count"]):
                vehicle_id += 1
                vid = f"vehicle_{vehicle_id:03d}"
                
                # Calculate position based on lane and spacing
                if scenario["lane"] == "lane1":
                    x = i * scenario["spacing"]
                    y = 0.0
                elif scenario["lane"] == "lane2":
                    x = i * scenario["spacing"] + 20.0
                    y = 3.2
                elif scenario["lane"] == "lane3":
                    x = 800.0 - i * scenario["spacing"]
                    y = 6.4
                else:  # intersection
                    x = 400.0 + i * 20.0
                    y = 100.0 + i * 15.0
                
                # Add some randomness to speed and position (reduced for better clustering)
                import random
                speed_variation = random.uniform(-1.0, 1.0)  # Reduced variation
                pos_variation = random.uniform(-2.0, 2.0)    # Reduced variation
                
                speed = max(5.0, scenario["base_speed"] + speed_variation)
                x += pos_variation
                
                self.vanet_app.add_vehicle(
                    vehicle_id=vid,
                    x=x,
                    y=y,
                    speed=speed,
                    direction=scenario["direction"],
                    lane_id=scenario["lane"]
                )
        
        self.logger.info(f"Created demo scenario with {vehicle_id} vehicles")
    
    def simulate_vehicle_mobility(self):
        """Simulate vehicle movement and behavior"""
        import random
        import math
        
        for vehicle_id, node in self.vanet_app.vehicle_nodes.items():
            # Update position based on speed and direction
            x, y = node.location
            
            # Basic movement simulation
            new_x = x + node.speed * self.step_size * math.cos(node.direction)
            new_y = y + node.speed * self.step_size * math.sin(node.direction)
            
            # Add some random variation
            new_x += random.uniform(-0.5, 0.5)
            new_y += random.uniform(-0.2, 0.2)
            
            # Boundary conditions (loop back)
            if new_x > 1000.0:
                new_x = 0.0
            elif new_x < 0.0:
                new_x = 1000.0
            
            if new_y > 200.0:
                new_y = 0.0
            elif new_y < 0.0:
                new_y = 200.0
            
            # Occasional speed changes
            if random.random() < 0.01:  # 1% chance per step
                speed_change = random.uniform(-2.0, 2.0)
                new_speed = max(5.0, min(30.0, node.speed + speed_change))
            else:
                new_speed = node.speed
            
            # Update vehicle
            self.vanet_app.update_vehicle(
                vehicle_id=vehicle_id,
                x=new_x,
                y=new_y,
                speed=new_speed,
                direction=node.direction,
                lane_id=node.lane_id
            )
    
    def simulate_traffic_events(self):
        """Simulate traffic events like lane changes, accidents, etc."""
        import random
        
        # Occasional emergency messages
        if random.random() < 0.001:  # 0.1% chance per step
            vehicles = list(self.vanet_app.vehicle_nodes.keys())
            if vehicles:
                emergency_vehicle = random.choice(vehicles)
                emergency_data = "Traffic accident ahead - reduce speed"
                self.vanet_app.send_emergency(emergency_vehicle, emergency_data)
                self.logger.warning(f"Emergency message sent by {emergency_vehicle}")
        
        # Random data broadcasts
        if random.random() < 0.005:  # 0.5% chance per step
            vehicles = list(self.vanet_app.vehicle_nodes.keys())
            if vehicles:
                sender = random.choice(vehicles)
                data_messages = [
                    "Weather update: Rain expected",
                    "Traffic congestion on main route",
                    "Fuel station 2km ahead",
                    "Construction zone - lane closure",
                    "Speed camera ahead"
                ]
                data = random.choice(data_messages)
                self.vanet_app.send_data(sender, data, "traffic_info", priority=3)
    
    def run_demo(self, save_results: bool = True):
        """Run the complete clustering demonstration"""
        self.logger.info("Starting VANET clustering demonstration")
        
        # Create initial scenario
        self.create_demo_scenario()
        
        # Main simulation loop
        step = 0
        start_time = time.time()
        
        while self.simulation_time < self.demo_duration:
            step_start = time.time()
            
            # Simulate vehicle mobility
            self.simulate_vehicle_mobility()
            
            # Simulate traffic events
            self.simulate_traffic_events()
            
            # Update VANET application
            self.vanet_app.handle_timeStep(self.simulation_time)
            
            # Update visualization
            self.visualizer.update_visualization(self.simulation_time)
            
            # Log progress and debug clustering
            if step % 50 == 0:  # Every 5 seconds
                stats = self.vanet_app.get_application_statistics()
                app_stats = stats['application']
                cluster_stats = stats['clustering']
                
                # Debug: Check vehicle positions and clustering attempts
                if step == 50:  # After 5 seconds, check why clustering isn't working
                    self.logger.info("=== CLUSTERING DEBUG INFO ===")
                    sample_vehicles = list(self.vanet_app.vehicle_nodes.items())[:5]
                    for vid, node in sample_vehicles:
                        self.logger.info(f"Vehicle {vid}: pos=({node.location[0]:.1f}, {node.location[1]:.1f}), "
                                       f"speed={node.speed:.1f}, cluster_id='{node.cluster_id}'")
                    
                    clustering_engine = self.vanet_app.clustering_engine
                    self.logger.info(f"Clustering params: radius={clustering_engine.max_cluster_radius}, "
                                   f"min_size={clustering_engine.min_cluster_size}, "
                                   f"speed_thresh={clustering_engine.speed_threshold}")
                
                self.logger.info(
                    f"Step {step}: Time {self.simulation_time:.1f}s | "
                    f"Vehicles: {app_stats['total_vehicles']} | "
                    f"Clusters: {cluster_stats['total_clusters']} | "
                    f"Clustered: {cluster_stats['total_clustered_vehicles']}"
                )
            
            # Advance simulation time
            self.simulation_time += self.step_size
            step += 1
            
            # Maintain real-time factor (optional)
            step_duration = time.time() - step_start
            if step_duration < self.step_size:
                time.sleep(self.step_size - step_duration)
        
        # Save results
        if save_results:
            self.save_demo_results()
        
        # Cleanup
        self.visualizer.cleanup()
        
        total_time = time.time() - start_time
        self.logger.info(f"Demo completed in {total_time:.2f} seconds ({step} steps)")
    
    def save_demo_results(self):
        """Save demonstration results to files"""
        self.logger.info("Saving demonstration results")
        
        # Get comprehensive statistics
        stats = self.vanet_app.get_application_statistics()
        viz_stats = self.visualizer.get_visualization_statistics()
        
        # Combine all results
        results = {
            'demo_info': {
                'duration': self.demo_duration,
                'total_steps': int(self.demo_duration / self.step_size),
                'algorithm': self.vanet_app.clustering_engine.algorithm.value,
                'timestamp': time.time()
            },
            'application_statistics': stats,
            'visualization_statistics': viz_stats,
            'final_cluster_state': self._get_cluster_snapshot()
        }
        
        # Save to JSON file
        results_file = f"clustering_demo_results_{int(time.time())}.json"
        try:
            with open(results_file, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            self.logger.info(f"Results saved to {results_file}")
        except Exception as e:
            self.logger.error(f"Could not save results: {e}")
        
        # Export visualization data
        viz_file = f"clustering_visualization_{int(time.time())}.json"
        self.visualizer.export_visualization_data(viz_file)
        
        # Create summary report
        self._create_summary_report(results)
    
    def _get_cluster_snapshot(self) -> dict:
        """Get current cluster state snapshot"""
        clusters = {}
        
        for cluster_id, cluster in self.vanet_app.clustering_engine.clusters.items():
            clusters[cluster_id] = {
                'head_id': cluster.head_id,
                'member_ids': list(cluster.member_ids),
                'size': cluster.size(),
                'centroid': (cluster.centroid_x, cluster.centroid_y),
                'avg_speed': cluster.avg_speed,
                'avg_direction': cluster.avg_direction,
                'formation_time': cluster.formation_time,
                'last_update': cluster.last_update
            }
        
        return clusters
    
    def _create_summary_report(self, results: dict):
        """Create human-readable summary report"""
        app_stats = results['application_statistics']['application']
        cluster_stats = results['application_statistics']['clustering']
        
        report_content = f"""
VANET Clustering Demonstration Summary Report
============================================

Simulation Configuration:
- Algorithm: {results['demo_info']['algorithm']}
- Duration: {results['demo_info']['duration']} seconds
- Total Steps: {results['demo_info']['total_steps']}

Vehicle Statistics:
- Total Vehicles: {app_stats['total_vehicles']}
- Messages Sent: {app_stats['messages_sent']}
- Messages Received: {app_stats['messages_received']}

Clustering Performance:
- Total Clusters Formed: {cluster_stats['total_clusters']}
- Currently Clustered Vehicles: {cluster_stats['total_clustered_vehicles']}
- Average Cluster Size: {cluster_stats.get('avg_cluster_size', 0):.2f}
- Largest Cluster Size: {cluster_stats.get('largest_cluster_size', 0)}

Cluster Management Events:
- Cluster Joins: {app_stats['cluster_joins']}
- Cluster Leaves: {app_stats['cluster_leaves']}
- Head Elections: {app_stats['head_elections']}

Final State:
- Active Clusters: {len(results['final_cluster_state'])}
- Clustering Efficiency: {(cluster_stats['total_clustered_vehicles'] / max(app_stats['total_vehicles'], 1) * 100):.1f}%

Report generated at: {time.strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        report_file = f"clustering_demo_report_{int(time.time())}.txt"
        try:
            with open(report_file, 'w') as f:
                f.write(report_content)
            self.logger.info(f"Summary report saved to {report_file}")
            print(report_content)  # Also print to console
        except Exception as e:
            self.logger.error(f"Could not save summary report: {e}")

def main():
    """Main demonstration function"""
    print("VANET Clustering System Demonstration")
    print("=" * 50)
    
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description="VANET Clustering Demonstration")
    parser.add_argument('--algorithm', choices=['mobility_based', 'direction_based', 'kmeans', 'dbscan'],
                       default='mobility_based', help="Clustering algorithm to use")
    parser.add_argument('--duration', type=float, default=120.0, help="Simulation duration in seconds")
    parser.add_argument('--no-save', action='store_true', help="Don't save results to files")
    
    args = parser.parse_args()
    
    # Map algorithm names
    algorithm_map = {
        'mobility_based': ClusteringAlgorithm.MOBILITY_BASED,
        'direction_based': ClusteringAlgorithm.DIRECTION_BASED,
        'kmeans': ClusteringAlgorithm.KMEANS,
        'dbscan': ClusteringAlgorithm.DBSCAN
    }
    
    algorithm = algorithm_map[args.algorithm]
    
    # Create and run demonstration
    demo = ClusteringDemo(algorithm)
    demo.demo_duration = args.duration
    
    try:
        demo.run_demo(save_results=not args.no_save)
        print("\nDemonstration completed successfully!")
        
    except KeyboardInterrupt:
        print("\nDemonstration interrupted by user")
        demo.visualizer.cleanup()
        
    except Exception as e:
        print(f"\nError during demonstration: {e}")
        demo.visualizer.cleanup()
        raise

if __name__ == "__main__":
    main()