#!/usr/bin/env python3
"""
Trust-Aware Clustering Enhancement
Enhances the existing clustering system to fully integrate trust evaluation
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from src.consensus_engine import ConsensusEngine, TrustEvaluationEngine
from src.custom_vanet_appl import CustomVANETApplication
from src.cluster_manager import ClusterHeadElectionMethod
from src.clustering import ClusteringAlgorithm
import time

def main():
    print("=== Trust-Aware Clustering Analysis ===\n")
    
    # Create VANET application with trust-enabled clustering
    app = CustomVANETApplication()
    app.initialize_consensus("main_node", "hybrid", ["authority_001", "authority_002", "authority_003"])
    
    print("1. Current Clustering Configuration:")
    clustering_algo = app.clustering_engine.algorithm if hasattr(app.clustering_engine, 'algorithm') else "Unknown"
    print(f"   Clustering Algorithm: {clustering_algo}")
    print(f"   Head Election Method: {app.cluster_manager.head_election_method}")
    print(f"   Trust Enabled: {app.trust_enabled}")
    
    # Add some test vehicles with different trust levels
    print("\n2. Adding Test Vehicles with Different Trust Levels:")
    
    # High trust vehicles
    app.add_vehicle("vehicle_trusted_001", 100.0, 200.0, 25.0, 0.0, "lane_1")
    app.add_vehicle("vehicle_trusted_002", 120.0, 200.0, 24.0, 0.0, "lane_1")
    
    # Medium trust vehicles  
    app.add_vehicle("vehicle_medium_001", 140.0, 200.0, 26.0, 0.0, "lane_1")
    app.add_vehicle("vehicle_medium_002", 160.0, 200.0, 25.0, 0.0, "lane_1")
    
    # Low trust vehicles
    app.add_vehicle("vehicle_untrusted_001", 180.0, 200.0, 27.0, 0.0, "lane_1")
    app.add_vehicle("vehicle_untrusted_002", 200.0, 200.0, 25.0, 0.0, "lane_1")
    
    # Set different trust scores
    if app.trust_enabled:
        # High trust
        app.vehicle_nodes["vehicle_trusted_001"].trust_score = 0.95
        app.vehicle_nodes["vehicle_trusted_002"].trust_score = 0.90
        
        # Medium trust
        app.vehicle_nodes["vehicle_medium_001"].trust_score = 0.70
        app.vehicle_nodes["vehicle_medium_002"].trust_score = 0.65
        
        # Low trust
        app.vehicle_nodes["vehicle_untrusted_001"].trust_score = 0.30
        app.vehicle_nodes["vehicle_untrusted_002"].trust_score = 0.25
        app.vehicle_nodes["vehicle_untrusted_002"].is_malicious = True  # Mark as malicious
    
    print("   Vehicle Trust Scores:")
    for vehicle_id, node in app.vehicle_nodes.items():
        status = "MALICIOUS" if node.is_malicious else "TRUSTED" if node.trust_score >= 0.8 else "MEDIUM" if node.trust_score >= 0.5 else "LOW"
        print(f"     {vehicle_id}: {node.trust_score:.2f} ({status})")
    
    print("\n3. Performing Clustering Update:")
    app.handle_timeStep(1.0)  # Trigger clustering
    
    print("   Clusters Formed:")
    for cluster_id, cluster in app.clustering_engine.clusters.items():
        head_trust = app.vehicle_nodes[cluster.head_id].trust_score if cluster.head_id in app.vehicle_nodes else 0.0
        print(f"     {cluster_id}: Head={cluster.head_id} (Trust: {head_trust:.2f}), Members={len(cluster.member_ids)}")
        for member_id in cluster.member_ids:
            if member_id != cluster.head_id:
                member_trust = app.vehicle_nodes[member_id].trust_score if member_id in app.vehicle_nodes else 0.0
                print(f"       └─ {member_id} (Trust: {member_trust:.2f})")
    
    print("\n4. Current Trust Integration in Clustering:")
    print("   ✓ Emergency head election uses trust scores")
    print("   ✓ Malicious cluster heads are automatically replaced")
    print("   ✓ Trust evaluation affects cluster head selection during emergencies")
    print("   ✗ Regular head election doesn't consider trust (uses connectivity/mobility)")
    print("   ✗ Cluster formation doesn't exclude low-trust nodes")
    print("   ✗ No trust-based cluster quality metrics")
    
    print("\n5. Proposed Trust-Aware Clustering Enhancements:")
    print("   1. Trust-based cluster head election method")
    print("   2. Trust-weighted composite scoring")
    print("   3. Minimum trust threshold for cluster heads")
    print("   4. Trust-based cluster member acceptance")
    print("   5. Dynamic trust monitoring and re-clustering")
    
    print("\n6. Simulating Trust-Based Head Election:")
    
    # Simulate what trust-based election would look like
    if app.clustering_engine.clusters:
        cluster_id = list(app.clustering_engine.clusters.keys())[0]
        cluster = app.clustering_engine.clusters[cluster_id]
        
        print(f"   Current head of {cluster_id}: {cluster.head_id}")
        
        # Find best candidate based on trust
        best_candidate = None
        best_score = 0.0
        
        all_candidates = [cluster.head_id] + list(cluster.member_ids)
        for candidate_id in all_candidates:
            if candidate_id in app.vehicle_nodes:
                node = app.vehicle_nodes[candidate_id]
                # Composite score: trust (60%) + other factors (40%)
                trust_score = node.trust_score
                reliability_score = 1.0 if not node.is_malicious else 0.0
                
                # Get connectivity (simplified)
                connectivity = len(app.cluster_manager.vehicle_neighbors.get(candidate_id, set()))
                connectivity_score = min(1.0, connectivity / 5.0)
                
                composite_score = (0.6 * trust_score + 
                                 0.2 * reliability_score + 
                                 0.2 * connectivity_score)
                
                print(f"     {candidate_id}: Trust={trust_score:.2f}, Composite={composite_score:.2f}")
                
                if composite_score > best_score and not node.is_malicious:
                    best_score = composite_score
                    best_candidate = candidate_id
        
        print(f"   Best trust-based candidate: {best_candidate} (score: {best_score:.2f})")
    
    print("\n7. Trust Impact on Clustering:")
    print("   Current Implementation:")
    print("   - Trust affects emergency head elections only")
    print("   - Malicious nodes can still be regular cluster members")
    print("   - Regular head elections ignore trust completely")
    print("   ")
    print("   Recommended Enhancement:")
    print("   - Add TRUST_BASED election method to ClusterHeadElectionMethod")
    print("   - Modify composite scoring to include trust weight")
    print("   - Implement minimum trust threshold for cluster heads")
    print("   - Add trust-based cluster quality metrics")
    
    print("\n=== Analysis Complete ===")

if __name__ == "__main__":
    main()