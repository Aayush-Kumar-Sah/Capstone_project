#!/usr/bin/env python3
"""
Trust-Aware Clustering Demo
Demonstrates clustering with full trust integration
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from src.custom_vanet_appl import CustomVANETApplication
from src.trust_aware_cluster_manager import TrustAwareClusterManager
from src.cluster_manager import ClusterHeadElectionMethod
import time

def main():
    print("=== Trust-Aware Clustering Demo ===\n")
    
    # Create VANET application with enhanced trust-aware clustering
    app = CustomVANETApplication()
    app.initialize_consensus("main_node", "hybrid", ["authority_001", "authority_002", "authority_003"])
    
    # Replace cluster manager with trust-aware version
    trust_cluster_manager = TrustAwareClusterManager(app.clustering_engine)
    trust_cluster_manager.head_election_method = ClusterHeadElectionMethod.WEIGHTED_COMPOSITE
    trust_cluster_manager.min_trust_threshold = 0.7  # High trust requirement
    trust_cluster_manager.trust_weight = 0.5  # Give trust high importance
    
    # Set trust provider functions
    def get_vehicle_trust(vehicle_id: str) -> float:
        if vehicle_id in app.vehicle_nodes:
            return app.vehicle_nodes[vehicle_id].trust_score
        return 1.0
    
    def is_vehicle_malicious(vehicle_id: str) -> bool:
        if vehicle_id in app.vehicle_nodes:
            return app.vehicle_nodes[vehicle_id].is_malicious
        return False
    
    trust_cluster_manager.set_trust_provider(get_vehicle_trust)
    trust_cluster_manager.set_malicious_checker(is_vehicle_malicious)
    
    # Replace the cluster manager
    app.cluster_manager = trust_cluster_manager
    
    print("1. Enhanced Clustering Configuration:")
    print(f"   Trust Threshold: {trust_cluster_manager.min_trust_threshold}")
    print(f"   Trust Weight: {trust_cluster_manager.trust_weight}")
    print(f"   Exclude Malicious: {trust_cluster_manager.exclude_malicious}")
    
    print("\n2. Adding Vehicles with Different Trust Profiles:")
    
    # Cluster 1: High-trust vehicles (close together)
    app.add_vehicle("vehicle_A1", 100.0, 100.0, 25.0, 0.0, "lane_1")  # High trust leader candidate
    app.add_vehicle("vehicle_A2", 120.0, 100.0, 25.0, 0.0, "lane_1")  # High trust member
    app.add_vehicle("vehicle_A3", 140.0, 100.0, 25.0, 0.0, "lane_1")  # Medium trust member
    
    # Cluster 2: Mixed trust vehicles (close together)
    app.add_vehicle("vehicle_B1", 500.0, 100.0, 25.0, 0.0, "lane_1")  # Medium trust
    app.add_vehicle("vehicle_B2", 520.0, 100.0, 25.0, 0.0, "lane_1")  # Low trust
    app.add_vehicle("vehicle_B3", 540.0, 100.0, 25.0, 0.0, "lane_1")  # Malicious
    
    # Set trust scores
    app.vehicle_nodes["vehicle_A1"].trust_score = 0.95  # Excellent
    app.vehicle_nodes["vehicle_A2"].trust_score = 0.85  # High
    app.vehicle_nodes["vehicle_A3"].trust_score = 0.75  # Good
    
    app.vehicle_nodes["vehicle_B1"].trust_score = 0.65  # Medium (below threshold)
    app.vehicle_nodes["vehicle_B2"].trust_score = 0.45  # Low
    app.vehicle_nodes["vehicle_B3"].trust_score = 0.20  # Very low
    app.vehicle_nodes["vehicle_B3"].is_malicious = True  # Mark as malicious
    
    print("   Vehicle Trust Profiles:")
    for vehicle_id, node in app.vehicle_nodes.items():
        status = "MALICIOUS" if node.is_malicious else "EXCELLENT" if node.trust_score >= 0.9 else "HIGH" if node.trust_score >= 0.8 else "GOOD" if node.trust_score >= 0.7 else "MEDIUM" if node.trust_score >= 0.5 else "LOW"
        meets_threshold = "✓" if node.trust_score >= trust_cluster_manager.min_trust_threshold and not node.is_malicious else "✗"
        print(f"     {vehicle_id}: Trust={node.trust_score:.2f} ({status}) {meets_threshold}")
    
    print("\n3. Performing Trust-Aware Clustering:")
    print(f"   Vehicles added: {len(app.vehicle_nodes)}")
    print(f"   Available vehicles for clustering:")
    for vid, node in app.vehicle_nodes.items():
        print(f"     {vid}: pos=({node.location[0]:.1f}, {node.location[1]:.1f})")
    
    app.handle_timeStep(1.0)  # Trigger clustering
    
    print(f"   Clusters after timeStep: {len(app.clustering_engine.clusters)}")
    print("   Clusters Formed:")
    trust_stats = trust_cluster_manager.get_trust_statistics()
    
    for cluster_id, cluster in app.clustering_engine.clusters.items():
        head_trust = get_vehicle_trust(cluster.head_id)
        head_malicious = is_vehicle_malicious(cluster.head_id)
        head_status = "MALICIOUS" if head_malicious else "TRUSTED" if head_trust >= 0.7 else "UNTRUSTED"
        
        print(f"     {cluster_id}:")
        print(f"       Head: {cluster.head_id} (Trust: {head_trust:.2f}, {head_status})")
        print(f"       Members: {len(cluster.member_ids)}")
        
        for member_id in cluster.member_ids:
            if member_id != cluster.head_id:
                member_trust = get_vehicle_trust(member_id)
                member_malicious = is_vehicle_malicious(member_id)
                member_status = "MALICIOUS" if member_malicious else "TRUSTED" if member_trust >= 0.7 else "UNTRUSTED"
                print(f"         └─ {member_id} (Trust: {member_trust:.2f}, {member_status})")
    
    print("\n4. Trust Statistics:")
    for key, value in trust_stats.items():
        if isinstance(value, float):
            print(f"   {key.replace('_', ' ').title()}: {value:.2f}")
        else:
            print(f"   {key.replace('_', ' ').title()}: {value}")
    
    print("\n5. Simulating Trust Changes:")
    print("   Scenario: vehicle_A1 becomes malicious...")
    
    # Make the current head malicious
    app.vehicle_nodes["vehicle_A1"].is_malicious = True
    app.vehicle_nodes["vehicle_A1"].trust_score = 0.15
    
    # Trigger re-clustering
    app.handle_timeStep(2.0)
    
    print("   After trust change:")
    for cluster_id, cluster in app.clustering_engine.clusters.items():
        head_trust = get_vehicle_trust(cluster.head_id)
        head_malicious = is_vehicle_malicious(cluster.head_id)
        head_status = "MALICIOUS" if head_malicious else "TRUSTED" if head_trust >= 0.7 else "UNTRUSTED"
        print(f"     {cluster_id}: Head={cluster.head_id} (Trust: {head_trust:.2f}, {head_status})")
    
    print("\n6. Trust-Aware Clustering Benefits:")
    print("   ✓ Cluster heads must meet minimum trust threshold")
    print("   ✓ Trust score heavily weighted in head selection")
    print("   ✓ Malicious nodes automatically excluded from leadership")
    print("   ✓ Dynamic re-election when head trust drops")
    print("   ✓ Trust statistics for network monitoring")
    print("   ✓ Configurable trust policies")
    
    print("\n7. Integration with Consensus System:")
    print("   ✓ Trust scores from consensus engine used in clustering")
    print("   ✓ Malicious node detection triggers cluster reorganization")
    print("   ✓ Authority nodes can override cluster decisions if needed")
    print("   ✓ Cross-validation between consensus and clustering trust metrics")
    
    print("\n=== Trust-Aware Clustering Complete ===")

if __name__ == "__main__":
    main()