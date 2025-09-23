#!/usr/bin/env python3
"""
VANET Consensus and Trust Evaluation Demonstration

This script demonstrates the Raft and Proof of Authority (PoA) consensus algorithms
for trust evaluation and malicious node detection in VANET environments.
"""

import time
import logging
import random
import json
from typing import Dict, List, Any

from src.custom_vanet_appl import CustomVANETApplication
from src.clustering import ClusteringAlgorithm
from src.consensus_engine import TrustLevel

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ConsensusDemo:
    """Demonstration of consensus algorithms for VANET trust evaluation"""
    
    def __init__(self):
        self.application = CustomVANETApplication(ClusteringAlgorithm.MOBILITY_BASED)
        self.simulation_time = 0.0
        self.demo_duration = 30.0  # seconds
        self.time_step = 0.1
        self.node_id = "demo_authority_001"
        
        # Demo configuration
        self.num_vehicles = 20
        self.num_authorities = 3
        self.malicious_probability = 0.1  # 10% chance of malicious behavior
        
        logger.info("Consensus demo initialized")
    
    def setup_demo_scenario(self):
        """Set up demo scenario with vehicles and authorities"""
        logger.info("Setting up demo scenario...")
        
        # Initialize the application
        self.application.initialize()
        
        # Set up authority nodes
        authority_nodes = [f"authority_{i:03d}" for i in range(self.num_authorities)]
        
        # Initialize consensus engine
        self.application.initialize_consensus(
            self.node_id, 
            consensus_type="hybrid",
            authority_nodes=authority_nodes
        )
        
        # Add authority nodes to network
        for i, auth_id in enumerate(authority_nodes):
            x = random.uniform(0, 1000)
            y = random.uniform(0, 1000)
            self.application.add_vehicle(auth_id, x, y, 60.0, random.uniform(0, 360))
            self.application.add_authority_node(auth_id)
        
        # Add regular vehicles
        for i in range(self.num_vehicles):
            vehicle_id = f"vehicle_{i:03d}"
            x = random.uniform(0, 1000)
            y = random.uniform(0, 1000)
            speed = random.uniform(30, 80)  # km/h
            direction = random.uniform(0, 360)
            
            self.application.add_vehicle(vehicle_id, x, y, speed, direction)
        
        logger.info(f"Created scenario with {self.num_vehicles} vehicles and {self.num_authorities} authorities")
    
    def simulate_vehicle_behavior(self):
        """Simulate vehicle behavior including malicious activities"""
        for vehicle_id, node in self.application.vehicle_nodes.items():
            if "authority" in vehicle_id:
                continue  # Skip authorities
            
            # Update vehicle position (simple movement simulation)
            x, y = node.location
            speed_ms = node.speed / 3.6  # Convert km/h to m/s
            
            # Simple straight-line movement
            direction_rad = node.direction * (3.14159 / 180)
            dx = speed_ms * self.time_step * 1.414  # cos approximation
            dy = speed_ms * self.time_step * 1.414  # sin approximation
            
            new_x = max(0, min(1000, x + dx))
            new_y = max(0, min(1000, y + dy))
            
            self.application.update_vehicle(vehicle_id, new_x, new_y, node.speed, node.direction)
            
            # Simulate potential malicious behavior
            if random.random() < self.malicious_probability:
                self._simulate_malicious_behavior(vehicle_id)
    
    def _simulate_malicious_behavior(self, vehicle_id: str):
        """Simulate various types of malicious behavior"""
        malicious_types = [
            "location_spoofing",
            "message_tampering", 
            "timing_attack",
            "inconsistent_behavior"
        ]
        
        behavior_type = random.choice(malicious_types)
        
        if behavior_type == "location_spoofing":
            # Simulate impossible location jump
            node = self.application.vehicle_nodes[vehicle_id]
            impossible_x = random.uniform(0, 1000)
            impossible_y = random.uniform(0, 1000)
            
            behavior_data = {
                'location': (impossible_x, impossible_y),
                'previous_location': node.location,
                'time_diff': 0.1,  # Very short time
                'max_reasonable_speed': 120
            }
            
        elif behavior_type == "message_tampering":
            behavior_data = {
                'message_integrity': random.uniform(0.3, 0.8)  # Low integrity
            }
            
        elif behavior_type == "timing_attack":
            behavior_data = {
                'response_times': [0.001, 0.002, 0.001, 0.002]  # Suspiciously fast
            }
            
        else:  # inconsistent_behavior
            behavior_data = {
                'activity_timestamp': time.time(),
                'consistency_score': random.uniform(0.2, 0.6)
            }
        
        # Report to consensus engine
        self.application.report_malicious_activity(
            self.node_id,
            vehicle_id,
            behavior_type,
            behavior_data,
            random.uniform(0.6, 0.9)
        )
        
        logger.warning(f"Simulated malicious behavior: {vehicle_id} - {behavior_type}")
    
    def run_simulation_step(self):
        """Run one simulation step"""
        self.simulation_time += self.time_step
        
        # Update application time
        self.application.handle_timeStep(self.simulation_time)
        
        # Simulate vehicle behavior
        self.simulate_vehicle_behavior()
        
        # Evaluate trust for random vehicles (simulate ongoing trust evaluation)
        if random.random() < 0.3:  # 30% chance per step
            vehicle_ids = [vid for vid in self.application.vehicle_nodes.keys() 
                          if not vid.startswith("authority")]
            if vehicle_ids:
                target_vehicle = random.choice(vehicle_ids)
                trust_score = self.application.evaluate_node_trust(target_vehicle)
                
                if trust_score < 0.5:
                    logger.info(f"Low trust detected for {target_vehicle}: {trust_score:.2f}")
    
    def print_status(self):
        """Print current simulation status"""
        stats = self.application.get_application_statistics()
        trust_stats = stats.get('trust_and_security', {})
        
        print(f"\n=== Consensus Demo Status (Time: {self.simulation_time:.1f}s) ===")
        print(f"Total Vehicles: {stats['application']['total_vehicles']}")
        print(f"Messages Sent: {stats['application']['messages_sent']}")
        print(f"Clusters Formed: {stats['application']['clusters_formed']}")
        
        if trust_stats.get('trust_enabled', False):
            print(f"Trust Evaluations: {trust_stats['trust_evaluations']}")
            print(f"Malicious Nodes Detected: {trust_stats['malicious_nodes']}")
            print(f"Average Trust Score: {trust_stats['average_trust_score']:.2f}")
            print(f"Trusted Nodes: {trust_stats['trusted_nodes']}")
            print(f"Authority Nodes: {trust_stats['authority_nodes']}")
            
            if trust_stats.get('consensus_stats'):
                consensus = trust_stats['consensus_stats']
                print(f"Consensus Type: {consensus['consensus_type']}")
                print(f"Current Leader: {consensus.get('current_leader', 'None')}")
                print(f"Is Leader: {consensus['is_leader']}")
        
        print("=" * 50)
    
    def demonstrate_consensus_features(self):
        """Demonstrate specific consensus features"""
        logger.info("Demonstrating consensus features...")
        
        # Demonstrate trust evaluation
        print("\n=== Trust Evaluation Demo ===")
        vehicle_ids = [vid for vid in self.application.vehicle_nodes.keys() 
                      if not vid.startswith("authority")]
        
        for vehicle_id in vehicle_ids[:5]:  # Evaluate first 5 vehicles
            trust_score = self.application.evaluate_node_trust(vehicle_id)
            is_trusted = self.application.is_node_trusted(vehicle_id)
            is_malicious = self.application.is_node_malicious(vehicle_id)
            
            print(f"Vehicle {vehicle_id}: Trust={trust_score:.2f}, "
                  f"Trusted={is_trusted}, Malicious={is_malicious}")
        
        # Demonstrate malicious node detection
        print("\n=== Malicious Node Detection Demo ===")
        if vehicle_ids:
            test_vehicle = vehicle_ids[0]
            
            # Simulate clear malicious behavior
            severe_behavior_data = {
                'location': (999, 999),
                'previous_location': (0, 0),
                'time_diff': 0.01,  # Impossible: 1000m in 0.01s
                'max_reasonable_speed': 120,
                'message_integrity': 0.1,  # Very low integrity
                'response_times': [0.001] * 10  # Consistently too fast
            }
            
            success = self.application.report_malicious_activity(
                self.node_id,
                test_vehicle,
                "multiple_violations",
                severe_behavior_data,
                0.95
            )
            
            if success:
                print(f"Reported malicious activity for {test_vehicle}")
                
                # Check if node is now marked as malicious
                if self.application.is_node_malicious(test_vehicle):
                    print(f"✓ Node {test_vehicle} successfully identified as malicious")
                else:
                    print(f"⚠ Node {test_vehicle} not yet marked as malicious")
        
        # Demonstrate leader election
        print("\n=== Consensus Leader Election ===")
        if self.application.consensus_engine:
            current_leader = self.application.consensus_engine.get_current_leader()
            print(f"Current Consensus Leader: {current_leader}")
            
            # Display authority scores
            if self.application.consensus_engine.poa:
                poa = self.application.consensus_engine.poa
                print("Authority Scores:")
                for auth_id, score in poa.authority_scores.items():
                    print(f"  {auth_id}: {score:.2f}")
    
    def save_results(self):
        """Save demonstration results"""
        stats = self.application.get_application_statistics()
        
        results = {
            'demo_config': {
                'duration': self.demo_duration,
                'num_vehicles': self.num_vehicles,
                'num_authorities': self.num_authorities,
                'malicious_probability': self.malicious_probability
            },
            'final_statistics': stats,
            'timestamp': time.time()
        }
        
        filename = f"consensus_demo_results_{int(time.time())}.json"
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"Results saved to {filename}")
        return filename
    
    def run(self):
        """Run the complete consensus demonstration"""
        logger.info("Starting VANET Consensus and Trust Evaluation Demo")
        
        # Setup
        self.setup_demo_scenario()
        
        # Initial status
        self.print_status()
        
        # Run simulation
        step_count = 0
        status_interval = int(5.0 / self.time_step)  # Print status every 5 seconds
        
        while self.simulation_time < self.demo_duration:
            self.run_simulation_step()
            step_count += 1
            
            # Print periodic status
            if step_count % status_interval == 0:
                self.print_status()
        
        # Final demonstrations
        self.demonstrate_consensus_features()
        
        # Final status and results
        print("\n=== Final Demo Results ===")
        self.print_status()
        
        # Save results
        results_file = self.save_results()
        
        logger.info("Consensus demo completed successfully")
        return results_file

def main():
    """Main function to run the consensus demonstration"""
    try:
        demo = ConsensusDemo()
        results_file = demo.run()
        
        print(f"\n✅ Demo completed successfully!")
        print(f"📄 Results saved to: {results_file}")
        print(f"🔍 Check the logs above for detailed consensus and trust evaluation activity")
        
    except Exception as e:
        logger.error(f"Demo failed with error: {e}")
        raise

if __name__ == "__main__":
    main()