#!/usr/bin/env python3
"""
Consensus Leadership Status Checker
Demonstrates how to check and interact with consensus leadership
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from src.consensus_engine import ConsensusEngine, TrustEvaluationEngine
from src.custom_vanet_appl import CustomVANETApplication
import time

def main():
    print("=== Consensus Leadership Status Demo ===\n")
    
    # Create a VANET application with consensus
    app = CustomVANETApplication()
    
    # Initialize consensus with multiple authorities
    node_id = "demo_checker"
    authorities = ["authority_001", "authority_002", "authority_003"]
    app.initialize_consensus(node_id, "hybrid", authorities)
    
    print("1. Initial Leadership Status:")
    current_leader = app.consensus_engine.get_current_leader() if app.consensus_engine else "None"
    is_leader = app.consensus_engine.is_leader() if app.consensus_engine else False
    consensus_node_id = app.consensus_engine.node_id if app.consensus_engine else "None"
    
    print(f"   Current Leader: {current_leader}")
    print(f"   Is this node leader: {is_leader}")
    print(f"   Node ID: {consensus_node_id}")
    
    if not app.consensus_engine:
        print("   ERROR: Consensus engine not initialized!")
        return
    
    # Get consensus statistics
    stats = app.consensus_engine.get_consensus_statistics()
    print(f"\n2. Consensus Statistics:")
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    # Demonstrate authority scoring
    print(f"\n3. Authority Scores:")
    if hasattr(app.consensus_engine, 'poa') and app.consensus_engine.poa and hasattr(app.consensus_engine.poa, 'authority_scores'):
        for auth_id, score in app.consensus_engine.poa.authority_scores.items():
            leader_marker = " ← CURRENT LEADER" if auth_id == current_leader else ""
            print(f"   {auth_id}: {score:.2f}{leader_marker}")
    else:
        print("   Authority scores not available")
    
    # Simulate leadership change by updating authority scores
    print(f"\n4. Simulating Leadership Change...")
    if app.consensus_engine.poa and hasattr(app.consensus_engine.poa, 'authority_scores'):
        # Show current leader
        old_leader = app.consensus_engine.get_current_leader()
        print(f"   Current leader: {old_leader}")
        
        # Boost our node's score to become leader
        app.consensus_engine.poa.authority_scores[consensus_node_id] = 0.95
        
        # Trigger leader re-election
        new_leader = app.consensus_engine.poa.select_leader()
        print(f"   New leader selected: {new_leader}")
        print(f"   Is this node now leader: {app.consensus_engine.is_leader()}")
        
        # Show updated authority scores
        print(f"   Updated Authority Scores:")
        for auth_id, score in app.consensus_engine.poa.authority_scores.items():
            leader_marker = " ← CURRENT LEADER" if auth_id == new_leader else ""
            print(f"     {auth_id}: {score:.2f}{leader_marker}")
    else:
        print("   Cannot simulate leadership change - PoA not available")
    
    # Demonstrate trust-based leadership
    print(f"\n5. Trust-Based Leadership Explanation:")
    print("   In the VANET consensus system:")
    print("   - Leaders are selected based on trust scores")
    print("   - Malicious nodes are automatically excluded from leadership")
    print("   - Leadership can change dynamically based on network conditions")
    print("   - The 'Is Leader: False' status means this node is NOT the current leader")
    print("   - This is normal in a distributed system with multiple authority nodes")
    
    print(f"\n6. Leadership Responsibilities:")
    final_leader = app.consensus_engine.get_current_leader()
    if final_leader:
        print(f"   Current leader ({final_leader}) responsibilities:")
        print("   - Coordinate trust evaluations across the network")
        print("   - Process malicious node reports")
        print("   - Maintain consensus state")
        print("   - Handle cluster head elections")
    
    print(f"\n7. Understanding 'Is Leader: False':")
    print("   - This means the current node is NOT the network leader")
    print("   - Only ONE node can be leader at a time in the consensus")
    print("   - Other nodes participate as followers/validators")
    print("   - Leadership can transfer if the current leader fails or has low trust")
    
    print(f"\n=== Demo Complete ===")

if __name__ == "__main__":
    main()