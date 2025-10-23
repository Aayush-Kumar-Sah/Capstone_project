#!/usr/bin/env python3
"""
Trust-Based Clustering Demo for VANET

This script demonstrates the trust-aware clustering system including:
- Trust evaluation and scoring
- Malicious node detection and exclusion
- Trust-based cluster head election
- Dynamic trust updates based on behavior
- Trust decay and recovery mechanisms

Usage:
    python3 trust_based_clustering_test.py [options]

Options:
    --duration SECONDS      Simulation duration (default: 60)
    --vehicles COUNT        Number of vehicles (default: 40)
    --malicious COUNT       Number of malicious vehicles (default: 5)
    --algorithm NAME        Clustering algorithm (default: mobility_based)
    --trust-threshold FLOAT Minimum trust for cluster heads (default: 0.6)
    --verbose              Enable verbose logging
"""

import sys
import time
import random
import math
import argparse
import logging
import json
from typing import Dict, List, Tuple
from dataclasses import dataclass

# Import VANET modules
from src.custom_vanet_appl import CustomVANETApplication
from src.clustering import ClusteringAlgorithm

@dataclass
class VehicleState:
    """Tracks vehicle state for simulation"""
    vehicle_id: str
    x: float
    y: float
    speed: float
    direction: float
    lane_id: str
    is_malicious: bool = False
    malicious_behavior_rate: float = 0.0  # 0-1, how often they misbehave
    cooperation_level: float = 1.0  # 0-1, how cooperative they are

class TrustClusteringDemo:
    """Demonstration of trust-based clustering in VANET"""
    
    def __init__(self, num_vehicles: int = 40, num_malicious: int = 5, 
                 algorithm: str = 'mobility_based', trust_threshold: float = 0.6):
        self.num_vehicles = num_vehicles
        self.num_malicious = num_malicious
        self.trust_threshold = trust_threshold
        
        # Initialize VANET application
        algo_map = {
            'mobility_based': ClusteringAlgorithm.MOBILITY_BASED,
            'direction_based': ClusteringAlgorithm.DIRECTION_BASED,
            'kmeans': ClusteringAlgorithm.KMEANS,
            'dbscan': ClusteringAlgorithm.DBSCAN
        }
        
        self.app = CustomVANETApplication(algo_map.get(algorithm, ClusteringAlgorithm.MOBILITY_BASED))
        self.app.trust_enabled = True
        self.app.cluster_manager.min_trust_threshold = trust_threshold
        
        # Enable trust filtering in clustering engine
        self.app.clustering_engine.trust_filtering_enabled = True
        
        # Simulation state
        self.vehicles: Dict[str, VehicleState] = {}
        self.simulation_time = 0.0
        self.time_step = 0.5  # 500ms steps
        
        # Tracking
        self.trust_history = []
        self.cluster_history = []
        self.malicious_detections = []
        self.head_changes = []
        
        self.logger = logging.getLogger(__name__)
    
    def setup_simulation(self):
        """Initialize vehicles with varied trust profiles"""
        print("Setting up trust-based clustering simulation...")
        print(f"Total vehicles: {self.num_vehicles}")
        print(f"Malicious vehicles: {self.num_malicious}")
        print(f"Trust threshold for heads: {self.trust_threshold}")
        print()
        
        # Create normal vehicles
        normal_count = self.num_vehicles - self.num_malicious
        
        # Highway scenario: 2 lanes, vehicles moving in same general direction
        for i in range(normal_count):
            vehicle_id = f"v{i}"
            
            # Distribute on two lanes
            lane_id = f"lane_{i % 2}"
            lane_offset = (i % 2) * 3.5  # 3.5m lane width
            
            # Position along highway (spread out)
            position_offset = (i // 2) * 50.0
            x = 100.0 + position_offset + random.uniform(-20, 20)
            y = 50.0 + lane_offset + random.uniform(-1, 1)
            
            # Similar speeds with some variance
            base_speed = 25.0  # ~90 km/h
            speed = base_speed + random.uniform(-3, 3)
            
            # Direction: mostly eastward with slight variations
            direction = random.uniform(-0.1, 0.1)  # Slight angle variation
            
            # Create vehicle with high initial trust
            vehicle = VehicleState(
                vehicle_id=vehicle_id,
                x=x, y=y,
                speed=speed,
                direction=direction,
                lane_id=lane_id,
                is_malicious=False,
                cooperation_level=random.uniform(0.8, 1.0)
            )
            
            self.vehicles[vehicle_id] = vehicle
            
            # Add to application with good initial trust
            self.app.add_vehicle(vehicle_id, x, y, speed, direction, lane_id)
            
            # Set good initial trust scores
            if vehicle_id in self.app.vehicle_nodes:
                node = self.app.vehicle_nodes[vehicle_id]
                node.trust_score = random.uniform(0.75, 0.95)
                node.message_authenticity_score = random.uniform(0.8, 1.0)
                node.behavior_consistency_score = random.uniform(0.8, 1.0)
        
        # Create malicious vehicles
        for i in range(self.num_malicious):
            vehicle_id = f"m{i}"
            
            # Distribute on lanes
            lane_id = f"lane_{i % 2}"
            lane_offset = (i % 2) * 3.5
            
            # Position among normal vehicles
            position_offset = (i * normal_count // self.num_malicious) * 50.0
            x = 100.0 + position_offset + random.uniform(-20, 20)
            y = 50.0 + lane_offset + random.uniform(-1, 1)
            
            # Speed similar to others (to blend in initially)
            speed = 25.0 + random.uniform(-3, 3)
            direction = random.uniform(-0.1, 0.1)
            
            # Create malicious vehicle
            vehicle = VehicleState(
                vehicle_id=vehicle_id,
                x=x, y=y,
                speed=speed,
                direction=direction,
                lane_id=lane_id,
                is_malicious=True,
                malicious_behavior_rate=random.uniform(0.3, 0.7),
                cooperation_level=random.uniform(0.2, 0.5)
            )
            
            self.vehicles[vehicle_id] = vehicle
            
            # Add to application with neutral initial trust (they start hidden)
            self.app.add_vehicle(vehicle_id, x, y, speed, direction, lane_id)
            
            # Set moderate initial trust (not detected yet)
            if vehicle_id in self.app.vehicle_nodes:
                node = self.app.vehicle_nodes[vehicle_id]
                node.trust_score = random.uniform(0.6, 0.8)  # Start hidden
                node.message_authenticity_score = random.uniform(0.6, 0.8)
                node.behavior_consistency_score = random.uniform(0.5, 0.7)
        
        print(f"Created {len(self.vehicles)} vehicles ({normal_count} normal, {self.num_malicious} malicious)")
        print()
    
    def run_simulation(self, duration: float):
        """Run the trust-based clustering simulation"""
        print(f"Running simulation for {duration} seconds...")
        print("=" * 80)
        
        steps = int(duration / self.time_step)
        start_time = time.time()
        
        for step in range(steps):
            self.simulation_time = step * self.time_step
            
            # Update vehicle positions
            self._update_vehicle_positions()
            
            # Simulate malicious behavior
            self._simulate_malicious_behavior()
            
            # Update VANET application
            self.app.handle_timeStep(self.simulation_time)
            
            # Collect statistics
            self._collect_statistics()
            
            # Print progress every 10 seconds
            if step % 20 == 0:
                self._print_status()
        
        end_time = time.time()
        elapsed = end_time - start_time
        
        print("=" * 80)
        print(f"Simulation completed in {elapsed:.2f} seconds")
        print(f"Simulation speed: {duration/elapsed:.1f}x real-time")
        print()
    
    def _update_vehicle_positions(self):
        """Update vehicle positions and speeds"""
        for vehicle_id, vehicle in self.vehicles.items():
            # Update position based on velocity
            vehicle.x += vehicle.speed * self.time_step * math.cos(vehicle.direction)
            vehicle.y += vehicle.speed * self.time_step * math.sin(vehicle.direction)
            
            # Add some random motion
            vehicle.speed += random.uniform(-0.5, 0.5)
            vehicle.speed = max(15.0, min(35.0, vehicle.speed))  # Keep reasonable
            
            vehicle.direction += random.uniform(-0.05, 0.05)
            vehicle.direction = (vehicle.direction + math.pi) % (2 * math.pi) - math.pi
            
            # Update in application
            if vehicle_id in self.app.vehicle_nodes:
                self.app.update_vehicle(
                    vehicle_id, vehicle.x, vehicle.y, 
                    vehicle.speed, vehicle.direction, vehicle.lane_id
                )
    
    def _simulate_malicious_behavior(self):
        """Simulate malicious vehicle behaviors"""
        for vehicle_id, vehicle in self.vehicles.items():
            if not vehicle.is_malicious:
                continue
            
            # Randomly perform malicious actions based on behavior rate
            if random.random() < vehicle.malicious_behavior_rate * self.time_step:
                # Types of malicious behavior
                behavior_type = random.choice([
                    'drop_messages',
                    'false_position',
                    'deny_service',
                    'sybil_attack'
                ])
                
                # Penalize trust
                self.app.penalize_malicious_behavior(vehicle_id, severity=0.5)
                
                # Track detection
                if vehicle_id in self.app.vehicle_nodes:
                    node = self.app.vehicle_nodes[vehicle_id]
                    if node.is_malicious:
                        self.malicious_detections.append({
                            'time': self.simulation_time,
                            'vehicle_id': vehicle_id,
                            'behavior': behavior_type,
                            'trust_score': node.trust_score
                        })
                        self.logger.warning(
                            f"Malicious behavior detected: {vehicle_id} - {behavior_type} "
                            f"(trust: {node.trust_score:.3f})"
                        )
    
    def _collect_statistics(self):
        """Collect simulation statistics"""
        # Collect trust scores
        trust_data = {
            'time': self.simulation_time,
            'trust_scores': {},
            'malicious_status': {}
        }
        
        for vehicle_id in self.vehicles:
            if vehicle_id in self.app.vehicle_nodes:
                node = self.app.vehicle_nodes[vehicle_id]
                trust_data['trust_scores'][vehicle_id] = node.trust_score
                trust_data['malicious_status'][vehicle_id] = node.is_malicious
        
        self.trust_history.append(trust_data)
        
        # Collect cluster information
        cluster_data = {
            'time': self.simulation_time,
            'clusters': {},
            'cluster_heads': {},
            'head_trust_scores': {}
        }
        
        for cluster_id, cluster in self.app.clustering_engine.clusters.items():
            cluster_data['clusters'][cluster_id] = {
                'size': cluster.size(),
                'head': cluster.head_id,
                'members': list(cluster.member_ids)
            }
            
            if cluster.head_id in self.app.vehicle_nodes:
                head_node = self.app.vehicle_nodes[cluster.head_id]
                cluster_data['cluster_heads'][cluster_id] = cluster.head_id
                cluster_data['head_trust_scores'][cluster_id] = head_node.trust_score
        
        self.cluster_history.append(cluster_data)
    
    def _print_status(self):
        """Print current simulation status"""
        clusters = self.app.clustering_engine.clusters
        stats = self.app.get_application_statistics()
        
        print(f"\n[Time: {self.simulation_time:.1f}s]")
        print(f"Clusters: {len(clusters)}")
        print(f"Malicious detected: {stats['application']['malicious_nodes_detected']}")
        print(f"Trust evaluations: {stats['application']['trust_evaluations']}")
        
        # Show cluster heads and their trust scores
        if clusters:
            print("\nCluster Heads (Trust Scores):")
            for cluster_id, cluster in list(clusters.items())[:5]:  # Show first 5
                if cluster.head_id in self.app.vehicle_nodes:
                    head_node = self.app.vehicle_nodes[cluster.head_id]
                    is_mal = " [MALICIOUS]" if head_node.is_malicious else ""
                    print(f"  {cluster_id}: {cluster.head_id} "
                          f"(trust: {head_node.trust_score:.3f}, "
                          f"size: {cluster.size()}){is_mal}")
    
    def generate_report(self) -> Dict:
        """Generate comprehensive simulation report"""
        stats = self.app.get_application_statistics()
        
        # Calculate trust statistics
        final_trust_data = self.trust_history[-1] if self.trust_history else {}
        trust_scores = final_trust_data.get('trust_scores', {})
        
        normal_vehicles = [v for v in self.vehicles.values() if not v.is_malicious]
        malicious_vehicles = [v for v in self.vehicles.values() if v.is_malicious]
        
        normal_trust_avg = 0.0
        malicious_trust_avg = 0.0
        
        if normal_vehicles:
            normal_scores = [trust_scores.get(v.vehicle_id, 0.0) for v in normal_vehicles]
            normal_trust_avg = sum(normal_scores) / len(normal_scores) if normal_scores else 0.0
        
        if malicious_vehicles:
            mal_scores = [trust_scores.get(v.vehicle_id, 0.0) for v in malicious_vehicles]
            malicious_trust_avg = sum(mal_scores) / len(mal_scores) if mal_scores else 0.0
        
        # Malicious detection rate
        detected_count = sum(1 for v in malicious_vehicles 
                            if self.app.vehicle_nodes.get(v.vehicle_id, None) and 
                            self.app.vehicle_nodes[v.vehicle_id].is_malicious)
        detection_rate = detected_count / len(malicious_vehicles) if malicious_vehicles else 0.0
        
        # Cluster head trust compliance
        final_cluster_data = self.cluster_history[-1] if self.cluster_history else {}
        head_trust_scores = final_cluster_data.get('head_trust_scores', {})
        compliant_heads = sum(1 for score in head_trust_scores.values() 
                             if score >= self.trust_threshold)
        compliance_rate = (compliant_heads / len(head_trust_scores) 
                          if head_trust_scores else 0.0)
        
        report = {
            'configuration': {
                'num_vehicles': self.num_vehicles,
                'num_malicious': self.num_malicious,
                'trust_threshold': self.trust_threshold,
                'simulation_duration': self.simulation_time
            },
            'trust_statistics': {
                'average_trust_normal_vehicles': normal_trust_avg,
                'average_trust_malicious_vehicles': malicious_trust_avg,
                'malicious_detection_rate': detection_rate,
                'detected_malicious_count': detected_count,
                'total_malicious_count': len(malicious_vehicles)
            },
            'cluster_statistics': {
                'final_cluster_count': len(self.app.clustering_engine.clusters),
                'cluster_head_trust_compliance': compliance_rate,
                'compliant_heads': compliant_heads,
                'total_heads': len(head_trust_scores)
            },
            'application_statistics': stats,
            'malicious_detections': len(self.malicious_detections),
            'detection_events': self.malicious_detections[:10]  # First 10 events
        }
        
        return report
    
    def print_report(self):
        """Print simulation report"""
        report = self.generate_report()
        
        print("\n" + "=" * 80)
        print("TRUST-BASED CLUSTERING SIMULATION REPORT")
        print("=" * 80)
        
        print("\n## Configuration")
        print(f"Total Vehicles: {report['configuration']['num_vehicles']}")
        print(f"Malicious Vehicles: {report['configuration']['num_malicious']}")
        print(f"Trust Threshold: {report['configuration']['trust_threshold']}")
        print(f"Duration: {report['configuration']['simulation_duration']:.1f}s")
        
        print("\n## Trust Statistics")
        trust_stats = report['trust_statistics']
        print(f"Average Trust (Normal):    {trust_stats['average_trust_normal_vehicles']:.3f}")
        print(f"Average Trust (Malicious): {trust_stats['average_trust_malicious_vehicles']:.3f}")
        print(f"Malicious Detection Rate:  {trust_stats['malicious_detection_rate']*100:.1f}%")
        print(f"Detected: {trust_stats['detected_malicious_count']}/{trust_stats['total_malicious_count']}")
        
        print("\n## Cluster Statistics")
        cluster_stats = report['cluster_statistics']
        print(f"Final Cluster Count: {cluster_stats['final_cluster_count']}")
        print(f"Cluster Head Trust Compliance: {cluster_stats['cluster_head_trust_compliance']*100:.1f}%")
        print(f"Compliant Heads: {cluster_stats['compliant_heads']}/{cluster_stats['total_heads']}")
        
        print("\n## Application Metrics")
        app_stats = report['application_statistics']['application']
        print(f"Messages Sent:     {app_stats['messages_sent']}")
        print(f"Messages Received: {app_stats['messages_received']}")
        print(f"Clusters Formed:   {app_stats['clusters_formed']}")
        print(f"Trust Evaluations: {app_stats['trust_evaluations']}")
        print(f"Trust Updates:     {app_stats['trust_updates']}")
        
        print("\n## Key Findings")
        if trust_stats['malicious_detection_rate'] > 0.7:
            print("✓ EXCELLENT: High malicious detection rate (>70%)")
        elif trust_stats['malicious_detection_rate'] > 0.5:
            print("✓ GOOD: Moderate malicious detection rate (>50%)")
        else:
            print("⚠ WARNING: Low malicious detection rate (<50%)")
        
        if cluster_stats['cluster_head_trust_compliance'] > 0.9:
            print("✓ EXCELLENT: Very high trust compliance for cluster heads (>90%)")
        elif cluster_stats['cluster_head_trust_compliance'] > 0.7:
            print("✓ GOOD: Good trust compliance for cluster heads (>70%)")
        else:
            print("⚠ WARNING: Low trust compliance for cluster heads")
        
        trust_separation = (trust_stats['average_trust_normal_vehicles'] - 
                          trust_stats['average_trust_malicious_vehicles'])
        if trust_separation > 0.3:
            print(f"✓ EXCELLENT: Strong trust score separation ({trust_separation:.3f})")
        elif trust_separation > 0.15:
            print(f"✓ GOOD: Moderate trust score separation ({trust_separation:.3f})")
        else:
            print(f"⚠ WARNING: Weak trust score separation ({trust_separation:.3f})")
        
        print("\n" + "=" * 80)
        print()

def main():
    parser = argparse.ArgumentParser(
        description='Trust-Based Clustering Demo for VANET',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--duration', type=float, default=60.0,
                       help='Simulation duration in seconds (default: 60)')
    parser.add_argument('--vehicles', type=int, default=40,
                       help='Number of vehicles (default: 40)')
    parser.add_argument('--malicious', type=int, default=5,
                       help='Number of malicious vehicles (default: 5)')
    parser.add_argument('--algorithm', type=str, default='mobility_based',
                       choices=['mobility_based', 'direction_based', 'kmeans', 'dbscan'],
                       help='Clustering algorithm (default: mobility_based)')
    parser.add_argument('--trust-threshold', type=float, default=0.6,
                       help='Minimum trust for cluster heads (default: 0.6)')
    parser.add_argument('--verbose', action='store_true',
                       help='Enable verbose logging')
    parser.add_argument('--save-results', action='store_true',
                       help='Save results to JSON file')
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run simulation
    demo = TrustClusteringDemo(
        num_vehicles=args.vehicles,
        num_malicious=args.malicious,
        algorithm=args.algorithm,
        trust_threshold=args.trust_threshold
    )
    
    demo.setup_simulation()
    demo.run_simulation(args.duration)
    demo.print_report()
    
    # Save results if requested
    if args.save_results:
        report = demo.generate_report()
        filename = f"trust_clustering_results_{int(time.time())}.json"
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        print(f"Results saved to: {filename}")

if __name__ == '__main__':
    main()
