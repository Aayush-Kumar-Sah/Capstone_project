#!/usr/bin/env python3
"""
Consensus Leadership Change Demo
Shows how leadership changes based on trust scores and authority status
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from src.consensus_engine import ConsensusEngine, TrustEvaluationEngine
from src.custom_vanet_appl import CustomVANETApplication
import time

def main():
    print("=== VANET Consensus Leadership Change Demo ===\n")
    
    # Create multiple VANET applications to simulate different nodes
    print("Creating network nodes...")
    
    # Authority nodes
    auth1 = CustomVANETApplication()
    auth1.initialize_consensus("authority_001", "hybrid", ["authority_001", "authority_002", "authority_003"])
    
    auth2 = CustomVANETApplication()
    auth2.initialize_consensus("authority_002", "hybrid", ["authority_001", "authority_002", "authority_003"])
    
    auth3 = CustomVANETApplication()
    auth3.initialize_consensus("authority_003", "hybrid", ["authority_001", "authority_002", "authority_003"])
    
    # Regular node
    regular = CustomVANETApplication()
    regular.initialize_consensus("regular_node", "hybrid", ["authority_001", "authority_002", "authority_003"])
    
    nodes = {"authority_001": auth1, "authority_002": auth2, "authority_003": auth3, "regular_node": regular}
    
    print("\\n1. Initial Network Status:")
    for name, node in nodes.items():
        leader = node.consensus_engine.get_current_leader()
        is_leader = node.consensus_engine.is_leader()
        print(f"   {name}: Leader={leader}, IsLeader={is_leader}")
    
    print("\\n2. Authority Scores (from authority_001 perspective):")
    if auth1.consensus_engine.poa:
        for auth_id, score in auth1.consensus_engine.poa.authority_scores.items():
            leader_marker = " ← LEADER" if auth_id == auth1.consensus_engine.get_current_leader() else ""
            print(f"   {auth_id}: {score:.2f}{leader_marker}")
    
    print("\\n3. Simulating Trust Score Changes...")
    
    # Scenario 1: Lower trust for current leader
    current_leader = auth1.consensus_engine.get_current_leader()
    print(f"   Lowering trust for current leader: {current_leader}")
    
    for node in nodes.values():
        if node.consensus_engine.poa and current_leader in node.consensus_engine.poa.authority_scores:
            node.consensus_engine.poa.authority_scores[current_leader] = 0.3  # Low trust
    
    # Scenario 2: Boost another authority
    new_leader_candidate = "authority_001" if current_leader != "authority_001" else "authority_002"
    print(f"   Boosting trust for: {new_leader_candidate}")
    
    for node in nodes.values():
        if node.consensus_engine.poa and new_leader_candidate in node.consensus_engine.poa.authority_scores:
            node.consensus_engine.poa.authority_scores[new_leader_candidate] = 0.95  # High trust
    
    print("\\n4. After Trust Changes - Forcing Re-election:")
    # Force immediate re-election by resetting the rotation timer
    for name, node in nodes.items():
        if node.consensus_engine.poa:
            # Reset the last leader change time to force immediate re-election
            node.consensus_engine.poa.last_leader_change = 0
            new_leader = node.consensus_engine.poa.select_leader()
            print(f"   {name} sees leader: {new_leader}")
    
    print("\\n5. Updated Authority Scores:")
    if auth1.consensus_engine.poa:
        for auth_id, score in auth1.consensus_engine.poa.authority_scores.items():
            leader_marker = " ← NEW LEADER" if auth_id == auth1.consensus_engine.get_current_leader() else ""
            print(f"   {auth_id}: {score:.2f}{leader_marker}")
    
    print("\\n6. Final Network Status:")
    for name, node in nodes.items():
        leader = node.consensus_engine.get_current_leader()
        is_leader = node.consensus_engine.is_leader()
        trust_score = node.consensus_engine.poa.authority_scores.get(name, 0.0) if node.consensus_engine.poa else 0.0
        print(f"   {name}: Leader={leader}, IsLeader={is_leader}, TrustScore={trust_score:.2f}")
    
    print("\\n7. Explanation of 'Is Leader: False':")
    print("   ✓ 'Is Leader: False' means this node is NOT the current consensus leader")
    print("   ✓ This is completely normal in a distributed consensus system")
    print("   ✓ Only ONE node is the leader at any given time")
    print("   ✓ Leadership rotates based on:")
    print("     - Trust scores and reliability")
    print("     - Network participation")
    print("     - Response to consensus messages")
    print("     - Detection of malicious behavior")
    
    print("\\n8. When Leadership Changes:")
    print("   ✓ Current leader becomes malicious or unreliable")
    print("   ✓ Another authority gains higher trust score")
    print("   ✓ Network partitioning and recovery")
    print("   ✓ Scheduled rotation (in some consensus algorithms)")
    
    print("\\n=== Demo Complete ===")

if __name__ == "__main__":
    main()