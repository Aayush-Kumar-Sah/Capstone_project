"""
Enhanced Trust-Aware Cluster Manager
Extends the existing cluster manager to fully integrate trust evaluation
"""

from src.cluster_manager import ClusterManager, ClusterHeadElectionMethod
from src.clustering import Vehicle, Cluster
from typing import List, Dict, Optional, Callable
import logging

class TrustAwareClusterManager(ClusterManager):
    """Enhanced cluster manager with trust-aware features"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Trust-related configuration
        self.min_trust_threshold = 0.6  # Minimum trust for cluster heads
        self.trust_weight = 0.4  # Weight of trust in composite scoring
        self.exclude_malicious = True  # Exclude malicious nodes from clusters
        self.trust_provider: Optional[Callable[[str], float]] = None
        self.malicious_checker: Optional[Callable[[str], bool]] = None
        
        self.logger = logging.getLogger(__name__)
    
    def set_trust_provider(self, trust_provider: Callable[[str], float]):
        """Set trust score provider function"""
        self.trust_provider = trust_provider
    
    def set_malicious_checker(self, malicious_checker: Callable[[str], bool]):
        """Set malicious node checker function"""
        self.malicious_checker = malicious_checker
    
    def get_trust_score(self, vehicle_id: str) -> float:
        """Get trust score for a vehicle"""
        if self.trust_provider:
            return self.trust_provider(vehicle_id)
        return 1.0  # Default high trust if no provider
    
    def is_malicious(self, vehicle_id: str) -> bool:
        """Check if vehicle is malicious"""
        if self.malicious_checker:
            return self.malicious_checker(vehicle_id)
        return False  # Default not malicious if no checker
    
    def _elect_cluster_head(self, cluster: Cluster, all_vehicles: List[Vehicle]) -> Optional[str]:
        """Elect the best cluster head with trust consideration"""
        vehicle_dict = {v.id: v for v in all_vehicles}
        
        # Get candidate vehicles (exclude malicious if configured)
        candidates = []
        if cluster.head_id in vehicle_dict:
            if not (self.exclude_malicious and self.is_malicious(cluster.head_id)):
                candidates.append(vehicle_dict[cluster.head_id])
        
        for member_id in cluster.member_ids:
            if member_id in vehicle_dict:
                if not (self.exclude_malicious and self.is_malicious(member_id)):
                    candidates.append(vehicle_dict[member_id])
        
        if not candidates:
            return None
        
        # Filter candidates by minimum trust threshold
        trusted_candidates = []
        for candidate in candidates:
            trust_score = self.get_trust_score(candidate.id)
            if trust_score >= self.min_trust_threshold:
                trusted_candidates.append(candidate)
        
        # If no trusted candidates, use all candidates but warn
        if not trusted_candidates:
            self.logger.warning(f"No candidates meet trust threshold {self.min_trust_threshold} for cluster {cluster.id}")
            trusted_candidates = candidates
        
        # Use trust-aware election
        if self.head_election_method == ClusterHeadElectionMethod.WEIGHTED_COMPOSITE:
            return self._elect_by_trust_aware_composite(trusted_candidates, cluster)
        else:
            # Fall back to original methods for other election types
            return super()._elect_cluster_head(cluster, all_vehicles)
    
    def _elect_by_trust_aware_composite(self, candidates: List[Vehicle], cluster: Cluster) -> str:
        """Elect head based on trust-aware weighted composite score"""
        best_vehicle = None
        best_score = -1
        
        for vehicle in candidates:
            # Trust score (0-1)
            trust_score = self.get_trust_score(vehicle.id)
            
            # Connectivity score (0-1)
            neighbors = len(self.vehicle_neighbors.get(vehicle.id, set()))
            connectivity_score = min(1.0, neighbors / 10.0)
            
            # Stability score (0-1) - lower mobility is better
            mobility = self._calculate_vehicle_mobility(vehicle.id)
            stability_score = max(0.0, 1.0 - (mobility / 50.0))
            
            # Position score (0-1) - closer to centroid is better
            distance = ((vehicle.x - cluster.centroid_x)**2 + 
                       (vehicle.y - cluster.centroid_y)**2)**0.5
            position_score = max(0.0, 1.0 - (distance / 300.0))
            
            # Reliability score (0-1) - not malicious
            reliability_score = 0.0 if self.is_malicious(vehicle.id) else 1.0
            
            # Trust-aware weighted composite
            composite_score = (
                self.trust_weight * trust_score +
                0.25 * connectivity_score + 
                0.20 * stability_score + 
                0.10 * position_score +
                0.05 * reliability_score
            )
            
            self.logger.debug(
                f"Candidate {vehicle.id}: Trust={trust_score:.2f}, "
                f"Connectivity={connectivity_score:.2f}, Stability={stability_score:.2f}, "
                f"Position={position_score:.2f}, Reliability={reliability_score:.2f}, "
                f"Composite={composite_score:.2f}"
            )
            
            if composite_score > best_score:
                best_score = composite_score
                best_vehicle = vehicle
        
        selected_id = best_vehicle.id if best_vehicle else candidates[0].id
        self.logger.info(f"Trust-aware head election: {selected_id} (score: {best_score:.2f})")
        return selected_id
    
    def _should_reelect_head(self, cluster_id: str, current_time: float) -> bool:
        """Enhanced re-election logic considering trust changes"""
        # Original periodic and quality-based checks
        if super()._should_reelect_head(cluster_id, current_time):
            return True
        
        # Trust-based re-election triggers
        # Get the cluster from clustering engine
        cluster = self.clustering_engine.clusters.get(cluster_id)
        if not cluster:
            return False
        
        current_head = cluster.head_id
        if not current_head:
            return True
        
        # Re-elect if current head becomes malicious
        if self.is_malicious(current_head):
            self.logger.warning(f"Re-electing head for cluster {cluster_id}: current head {current_head} is malicious")
            return True
        
        # Re-elect if current head trust drops below threshold
        head_trust = self.get_trust_score(current_head)
        if head_trust < self.min_trust_threshold:
            self.logger.warning(f"Re-electing head for cluster {cluster_id}: head trust {head_trust:.2f} below threshold {self.min_trust_threshold}")
            return True
        
        return False
    
    def get_trust_statistics(self) -> Dict[str, float]:
        """Get trust-related clustering statistics"""
        if not self.cluster_states:
            return {}
        
        total_heads = 0
        trusted_heads = 0
        head_trust_scores = []
        malicious_heads = 0
        
        for cluster_state in self.cluster_states.values():
            if cluster_state.cluster and cluster_state.cluster.head_id:
                head_id = cluster_state.cluster.head_id
                total_heads += 1
                
                trust_score = self.get_trust_score(head_id)
                head_trust_scores.append(trust_score)
                
                if trust_score >= self.min_trust_threshold:
                    trusted_heads += 1
                
                if self.is_malicious(head_id):
                    malicious_heads += 1
        
        avg_head_trust = sum(head_trust_scores) / len(head_trust_scores) if head_trust_scores else 0.0
        
        return {
            'total_cluster_heads': total_heads,
            'trusted_cluster_heads': trusted_heads,
            'malicious_cluster_heads': malicious_heads,
            'average_head_trust': avg_head_trust,
            'trust_threshold': self.min_trust_threshold,
            'trust_compliance_rate': trusted_heads / total_heads if total_heads > 0 else 0.0
        }