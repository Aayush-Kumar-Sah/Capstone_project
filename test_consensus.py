#!/usr/bin/env python3
"""
Test suite for consensus algorithms and trust evaluation in VANET system
"""

import unittest
import time
import logging
from typing import Dict, List

from src.consensus_engine import (
    ConsensusEngine, TrustMetrics, TrustLevel, MaliciousActivity,
    RaftConsensus, PoAConsensus, ConsensusMessage, ConsensusMessageType
)
from src.custom_vanet_appl import CustomVANETApplication
from src.clustering import ClusteringAlgorithm

# Configure logging for tests
logging.basicConfig(level=logging.WARNING)

class TestConsensusEngine(unittest.TestCase):
    """Test cases for consensus engine functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.node_id = "test_node_001"
        self.consensus_engine = ConsensusEngine(self.node_id, "hybrid")
        
        # Test nodes
        self.test_nodes = [f"node_{i:03d}" for i in range(5)]
        self.authority_nodes = self.test_nodes[:2]  # First 2 as authorities
    
    def test_consensus_engine_initialization(self):
        """Test consensus engine initialization"""
        self.assertEqual(self.consensus_engine.node_id, self.node_id)
        self.assertEqual(self.consensus_engine.consensus_type, "hybrid")
        self.assertIsNotNone(self.consensus_engine.trust_engine)
        self.assertFalse(self.consensus_engine.is_running)
    
    def test_raft_initialization(self):
        """Test Raft consensus initialization"""
        self.consensus_engine.initialize_raft(self.test_nodes)
        
        self.assertIsNotNone(self.consensus_engine.raft)
        self.assertEqual(self.consensus_engine.raft.node_id, self.node_id)
        self.assertEqual(len(self.consensus_engine.raft.cluster_nodes), len(self.test_nodes))
    
    def test_poa_initialization(self):
        """Test PoA consensus initialization"""
        self.consensus_engine.initialize_poa(self.authority_nodes)
        
        self.assertIsNotNone(self.consensus_engine.poa)
        self.assertEqual(len(self.consensus_engine.poa.authorities), len(self.authority_nodes))
    
    def test_trust_evaluation(self):
        """Test trust evaluation functionality"""
        # Initialize PoA for trust evaluation
        self.consensus_engine.initialize_poa(self.authority_nodes)
        self.consensus_engine.start()
        
        # Create test trust metrics
        trust_metrics = TrustMetrics(
            node_id="test_target",
            message_authenticity=0.9,
            behavior_consistency=0.8,
            network_participation=0.7,
            response_reliability=0.85,
            location_verification=0.95
        )
        
        # Evaluate trust
        trust_score = self.consensus_engine.evaluate_node_trust("test_target", trust_metrics)
        
        self.assertIsInstance(trust_score, float)
        self.assertGreaterEqual(trust_score, 0.0)
        self.assertLessEqual(trust_score, 1.0)
    
    def test_malicious_node_detection(self):
        """Test malicious node detection"""
        self.consensus_engine.initialize_poa(self.authority_nodes)
        self.consensus_engine.start()
        
        # Simulate malicious behavior
        malicious_behavior = {
            'location': (1000, 1000),
            'previous_location': (0, 0),
            'time_diff': 0.01,  # Impossible speed
            'max_reasonable_speed': 120,
            'message_integrity': 0.1  # Very low integrity
        }
        
        malicious_activity = self.consensus_engine.trust_engine.detect_malicious_behavior(
            "malicious_node", malicious_behavior
        )
        
        self.assertIsNotNone(malicious_activity)
        self.assertEqual(malicious_activity.target_id, "malicious_node")
        self.assertGreater(malicious_activity.severity, 0.0)
    
    def test_trust_levels(self):
        """Test trust level classification"""
        # Test different trust levels
        test_cases = [
            (0.95, TrustLevel.VERY_HIGH),
            (0.8, TrustLevel.HIGH),
            (0.6, TrustLevel.MEDIUM),
            (0.4, TrustLevel.LOW),
            (0.2, TrustLevel.VERY_LOW)
        ]
        
        for trust_score, expected_level in test_cases:
            # Create trust metrics with specific score
            trust_metrics = TrustMetrics(
                node_id="test_node",
                message_authenticity=trust_score,
                behavior_consistency=trust_score,
                network_participation=trust_score,
                response_reliability=trust_score,
                location_verification=trust_score
            )
            
            # Store in trust engine
            self.consensus_engine.trust_engine.trust_scores["test_node"] = trust_metrics
            
            # Check trust level
            level = self.consensus_engine.get_trust_level("test_node")
            self.assertEqual(level, expected_level)

class TestRaftConsensus(unittest.TestCase):
    """Test cases for Raft consensus algorithm"""
    
    def setUp(self):
        """Set up Raft test fixtures"""
        self.node_id = "raft_node_001"
        self.cluster_nodes = [f"raft_node_{i:03d}" for i in range(1, 6)]
        self.raft = RaftConsensus(self.node_id, self.cluster_nodes)
    
    def test_raft_initialization(self):
        """Test Raft node initialization"""
        self.assertEqual(self.raft.node_id, self.node_id)
        self.assertEqual(len(self.raft.cluster_nodes), len(self.cluster_nodes))
        self.assertEqual(self.raft.current_term, 0)
        self.assertIsNone(self.raft.voted_for)
    
    def test_raft_election_start(self):
        """Test Raft election process"""
        vote_requests = self.raft.start_election()
        
        # Check that node became candidate
        from src.consensus_engine import NodeState
        self.assertEqual(self.raft.state, NodeState.CANDIDATE)
        self.assertEqual(self.raft.current_term, 1)
        self.assertEqual(self.raft.voted_for, self.node_id)
        
        # Check vote requests generated
        self.assertEqual(len(vote_requests), len(self.cluster_nodes) - 1)  # Excluding self
        
        for request in vote_requests:
            self.assertEqual(request.msg_type, ConsensusMessageType.REQUEST_VOTE)
            self.assertEqual(request.sender_id, self.node_id)
            self.assertEqual(request.term, 1)

class TestPoAConsensus(unittest.TestCase):
    """Test cases for Proof of Authority consensus algorithm"""
    
    def setUp(self):
        """Set up PoA test fixtures"""
        self.node_id = "poa_node_001"
        self.authorities = [f"authority_{i:03d}" for i in range(3)]
        self.poa = PoAConsensus(self.node_id, self.authorities)
    
    def test_poa_initialization(self):
        """Test PoA initialization"""
        self.assertEqual(self.poa.node_id, self.node_id)
        self.assertEqual(len(self.poa.authorities), len(self.authorities))
        self.assertIsNone(self.poa.current_leader)
    
    def test_leader_selection(self):
        """Test PoA leader selection"""
        # Set some authority scores
        for i, auth_id in enumerate(self.authorities):
            self.poa.authority_scores[auth_id] = 0.5 + (i * 0.1)
        
        leader = self.poa.select_leader()
        
        # Should select authority with highest score
        expected_leader = self.authorities[-1]  # Last one has highest score
        self.assertEqual(leader, expected_leader)
        self.assertEqual(self.poa.current_leader, expected_leader)

class TestVANETConsensusIntegration(unittest.TestCase):
    """Test cases for VANET application consensus integration"""
    
    def setUp(self):
        """Set up VANET consensus integration tests"""
        self.application = CustomVANETApplication(ClusteringAlgorithm.MOBILITY_BASED)
        self.application.initialize()
        
        # Setup test scenario
        self.node_id = "vanet_node_001"
        self.authority_nodes = [f"authority_{i:03d}" for i in range(2)]
        
        # Initialize consensus
        self.application.initialize_consensus(
            self.node_id, "hybrid", self.authority_nodes
        )
    
    def test_consensus_integration(self):
        """Test consensus engine integration with VANET application"""
        self.assertIsNotNone(self.application.consensus_engine)
        self.assertTrue(self.application.trust_enabled)
        self.assertEqual(len(self.application.authority_nodes), len(self.authority_nodes))
    
    def test_authority_management(self):
        """Test authority node management"""
        new_authority = "new_authority_001"
        
        # Add authority
        self.application.add_authority_node(new_authority)
        self.assertIn(new_authority, self.application.authority_nodes)
        
        # Remove authority
        self.application.remove_authority_node(new_authority)
        self.assertNotIn(new_authority, self.application.authority_nodes)
    
    def test_trust_evaluation_integration(self):
        """Test trust evaluation integration"""
        # Add test vehicle
        vehicle_id = "test_vehicle_001"
        self.application.add_vehicle(vehicle_id, 100.0, 100.0, 50.0, 45.0)
        
        # Evaluate trust
        trust_score = self.application.evaluate_node_trust(vehicle_id)
        
        self.assertIsInstance(trust_score, float)
        self.assertGreaterEqual(trust_score, 0.0)
        self.assertLessEqual(trust_score, 1.0)
    
    def test_malicious_activity_reporting(self):
        """Test malicious activity reporting"""
        # Add test vehicles
        reporter_id = "reporter_001"
        target_id = "target_001"
        
        self.application.add_vehicle(reporter_id, 100.0, 100.0, 50.0, 45.0)
        self.application.add_vehicle(target_id, 200.0, 200.0, 60.0, 90.0)
        
        # Report malicious activity
        evidence = {'suspicious_behavior': 'location_spoofing'}
        success = self.application.report_malicious_activity(
            reporter_id, target_id, "location_spoofing", evidence, 0.8
        )
        
        self.assertTrue(success)
    
    def test_trust_statistics(self):
        """Test trust statistics generation"""
        # Add some vehicles
        for i in range(5):
            vehicle_id = f"vehicle_{i:03d}"
            self.application.add_vehicle(vehicle_id, i*100, i*100, 50.0, 45.0)
        
        # Get trust statistics
        trust_stats = self.application.get_trust_statistics()
        
        self.assertIsInstance(trust_stats, dict)
        self.assertTrue(trust_stats['trust_enabled'])
        self.assertIn('total_nodes', trust_stats)
        self.assertIn('trusted_nodes', trust_stats)
        self.assertIn('malicious_nodes', trust_stats)

class TestMaliciousNodeDetection(unittest.TestCase):
    """Test cases for malicious node detection algorithms"""
    
    def setUp(self):
        """Set up malicious node detection tests"""
        from src.consensus_engine import TrustEvaluationEngine
        self.trust_engine = TrustEvaluationEngine("test_node")
    
    def test_location_spoofing_detection(self):
        """Test location spoofing detection"""
        behavior_data = {
            'location': (1000, 1000),
            'previous_location': (0, 0),
            'time_diff': 0.01,  # 10ms for 1000m movement
            'max_reasonable_speed': 120  # km/h
        }
        
        is_spoofing = self.trust_engine._detect_location_spoofing("test_node", behavior_data)
        self.assertTrue(is_spoofing)
    
    def test_message_tampering_detection(self):
        """Test message tampering detection"""
        behavior_data = {
            'message_integrity': 0.8  # Below threshold of 0.95
        }
        
        is_tampering = self.trust_engine._detect_message_tampering(behavior_data)
        self.assertTrue(is_tampering)
    
    def test_timing_attack_detection(self):
        """Test timing attack detection"""
        behavior_data = {
            'response_times': [0.005, 0.003, 0.007, 0.004, 0.006]  # Very fast responses
        }
        
        is_timing_attack = self.trust_engine._detect_timing_attacks(behavior_data)
        self.assertTrue(is_timing_attack)

def run_consensus_tests():
    """Run all consensus-related tests"""
    print("Running VANET Consensus and Trust Evaluation Tests...")
    
    test_suites = [
        unittest.TestLoader().loadTestsFromTestCase(TestConsensusEngine),
        unittest.TestLoader().loadTestsFromTestCase(TestRaftConsensus),
        unittest.TestLoader().loadTestsFromTestCase(TestPoAConsensus),
        unittest.TestLoader().loadTestsFromTestCase(TestVANETConsensusIntegration),
        unittest.TestLoader().loadTestsFromTestCase(TestMaliciousNodeDetection),
    ]
    
    combined_suite = unittest.TestSuite(test_suites)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(combined_suite)
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_consensus_tests()
    if success:
        print("\n✅ All consensus tests passed!")
    else:
        print("\n❌ Some consensus tests failed!")
        exit(1)