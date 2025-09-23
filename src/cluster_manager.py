"""
Cluster Management System for VANET

This module provides cluster management functionality including cluster head election,
cluster maintenance, merging/splitting decisions, and overall cluster lifecycle management.
"""

import time
import logging
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
import math
import statistics

from .clustering import Vehicle, Cluster, VehicleClustering, ClusteringAlgorithm

class ClusterState(Enum):
    FORMING = "forming"
    STABLE = "stable"
    MERGING = "merging"
    SPLITTING = "splitting"
    DISSOLVING = "dissolving"

class ClusterHeadElectionMethod(Enum):
    HIGHEST_CONNECTIVITY = "highest_connectivity"
    LOWEST_MOBILITY = "lowest_mobility"
    WEIGHTED_COMPOSITE = "weighted_composite"
    CENTRAL_POSITION = "central_position"
    TRUST_BASED = "trust_based"  # New trust-based election

@dataclass
class ClusterMetrics:
    """Metrics for cluster quality assessment"""
    stability_score: float = 0.0
    connectivity_degree: int = 0
    mobility_variance: float = 0.0
    spatial_density: float = 0.0
    lifetime: float = 0.0
    message_overhead: int = 0
    
    def calculate_quality_score(self) -> float:
        """Calculate overall cluster quality score (0-1)"""
        # Weighted combination of normalized metrics
        weights = {
            'stability': 0.3,
            'connectivity': 0.25,
            'mobility': 0.2,
            'density': 0.15,
            'lifetime': 0.1
        }
        
        # Normalize metrics (assuming ranges)
        norm_stability = min(1.0, self.stability_score)
        norm_connectivity = min(1.0, self.connectivity_degree / 10.0)
        norm_mobility = max(0.0, 1.0 - (self.mobility_variance / 100.0))
        norm_density = min(1.0, self.spatial_density / 1000.0)
        norm_lifetime = min(1.0, self.lifetime / 300.0)  # 5 minutes max
        
        quality = (weights['stability'] * norm_stability +
                  weights['connectivity'] * norm_connectivity +
                  weights['mobility'] * norm_mobility +
                  weights['density'] * norm_density +
                  weights['lifetime'] * norm_lifetime)
        
        return quality

@dataclass
class ClusterEvent:
    """Represents a cluster-related event"""
    timestamp: float
    event_type: str
    cluster_id: str
    vehicle_id: Optional[str] = None
    details: Dict = field(default_factory=dict)

class ClusterManager:
    """Advanced cluster management system for VANET"""
    
    def __init__(self, clustering_engine: VehicleClustering, trust_evaluator=None):
        self.clustering_engine = clustering_engine
        self.trust_evaluator = trust_evaluator  # Optional trust evaluation engine
        self.cluster_metrics: Dict[str, ClusterMetrics] = {}
        self.cluster_states: Dict[str, ClusterState] = {}
        self.cluster_formation_times: Dict[str, float] = {}
        self.cluster_events: List[ClusterEvent] = []
        self.logger = logging.getLogger(__name__)
        
        # Management parameters
        self.head_election_method = ClusterHeadElectionMethod.TRUST_BASED if trust_evaluator else ClusterHeadElectionMethod.WEIGHTED_COMPOSITE
        self.stability_threshold = 0.7
        self.merge_threshold = 0.8
        self.split_threshold = 0.3
        self.reelection_interval = 30.0  # seconds
        self.max_cluster_lifetime = 300.0  # 5 minutes
        
        # Connectivity and mobility tracking
        self.vehicle_neighbors: Dict[str, Set[str]] = {}
        self.vehicle_mobility_history: Dict[str, List[Tuple[float, float, float]]] = {}  # (time, x, y)
        self.cluster_head_election_times: Dict[str, float] = {}
    
    def update_cluster_management(self, vehicles: List[Vehicle], current_time: float) -> Dict[str, any]:
        """Main cluster management update function"""
        self.logger.debug(f"Cluster manager updating with {len(vehicles)} vehicles at time {current_time}")
        
        # Update clustering
        clusters = self.clustering_engine.update_vehicles(vehicles)
        
        self.logger.debug(f"Clustering engine returned {len(clusters)} clusters")
        
        # Update vehicle tracking
        self._update_vehicle_tracking(vehicles, current_time)
        
        # Manage cluster states and lifecycle
        management_actions = {}
        
        for cluster_id, cluster in clusters.items():
            # Initialize cluster tracking if new
            if cluster_id not in self.cluster_states:
                self._initialize_cluster_tracking(cluster_id, current_time)
            
            # Update cluster metrics
            self._update_cluster_metrics(cluster_id, cluster, vehicles, current_time)
            
            # Perform cluster head election if needed
            if self._should_reelect_head(cluster_id, current_time):
                new_head = self._elect_cluster_head(cluster, vehicles)
                if new_head and new_head != cluster.head_id:
                    management_actions[cluster_id] = {
                        'action': 'head_change',
                        'old_head': cluster.head_id,
                        'new_head': new_head
                    }
                    self._change_cluster_head(cluster_id, new_head, current_time)
            
            # Check for cluster merging opportunities
            merge_candidates = self._find_merge_candidates(cluster_id, clusters, current_time)
            if merge_candidates:
                management_actions[cluster_id] = {
                    'action': 'merge_candidates',
                    'candidates': merge_candidates
                }
            
            # Check for cluster splitting needs
            if self._should_split_cluster(cluster_id, cluster, vehicles):
                split_plan = self._plan_cluster_split(cluster_id, cluster, vehicles)
                if split_plan:
                    management_actions[cluster_id] = {
                        'action': 'split_plan',
                        'plan': split_plan
                    }
            
            # Update cluster state
            self._update_cluster_state(cluster_id, current_time)
        
        # Clean up dissolved clusters
        self._cleanup_dissolved_clusters(clusters, current_time)
        
        return {
            'clusters': clusters,
            'management_actions': management_actions,
            'cluster_metrics': self.cluster_metrics,
            'cluster_states': self.cluster_states
        }
    
    def _initialize_cluster_tracking(self, cluster_id: str, current_time: float):
        """Initialize tracking for a new cluster"""
        self.cluster_states[cluster_id] = ClusterState.FORMING
        self.cluster_formation_times[cluster_id] = current_time
        self.cluster_metrics[cluster_id] = ClusterMetrics()
        self.cluster_head_election_times[cluster_id] = current_time
        
        event = ClusterEvent(
            timestamp=current_time,
            event_type="cluster_formed",
            cluster_id=cluster_id
        )
        self.cluster_events.append(event)
        self.logger.info(f"Initialized tracking for cluster {cluster_id}")
    
    def _update_vehicle_tracking(self, vehicles: List[Vehicle], current_time: float):
        """Update vehicle position history and neighbor relationships"""
        vehicle_dict = {v.id: v for v in vehicles}
        
        # Update position history
        for vehicle in vehicles:
            if vehicle.id not in self.vehicle_mobility_history:
                self.vehicle_mobility_history[vehicle.id] = []
            
            history = self.vehicle_mobility_history[vehicle.id]
            history.append((current_time, vehicle.x, vehicle.y))
            
            # Keep only recent history (last 60 seconds)
            cutoff_time = current_time - 60.0
            self.vehicle_mobility_history[vehicle.id] = [
                (t, x, y) for t, x, y in history if t >= cutoff_time
            ]
        
        # Update neighbor relationships
        communication_range = 300.0  # meters
        for i, vehicle1 in enumerate(vehicles):
            neighbors = set()
            for j, vehicle2 in enumerate(vehicles):
                if i != j and vehicle1.distance_to(vehicle2) <= communication_range:
                    neighbors.add(vehicle2.id)
            self.vehicle_neighbors[vehicle1.id] = neighbors
    
    def _update_cluster_metrics(self, cluster_id: str, cluster: Cluster, 
                               all_vehicles: List[Vehicle], current_time: float):
        """Update metrics for a cluster"""
        metrics = self.cluster_metrics[cluster_id]
        vehicle_dict = {v.id: v for v in all_vehicles}
        
        # Get cluster vehicles
        cluster_vehicles = []
        if cluster.head_id in vehicle_dict:
            cluster_vehicles.append(vehicle_dict[cluster.head_id])
        for member_id in cluster.member_ids:
            if member_id in vehicle_dict:
                cluster_vehicles.append(vehicle_dict[member_id])
        
        if not cluster_vehicles:
            return
        
        # Calculate stability score
        metrics.stability_score = self._calculate_stability_score(cluster_id, cluster_vehicles)
        
        # Calculate connectivity degree
        metrics.connectivity_degree = self._calculate_connectivity_degree(cluster_vehicles)
        
        # Calculate mobility variance
        metrics.mobility_variance = self._calculate_mobility_variance(cluster_vehicles)
        
        # Calculate spatial density
        metrics.spatial_density = self._calculate_spatial_density(cluster_vehicles)
        
        # Update lifetime
        formation_time = self.cluster_formation_times.get(cluster_id, current_time)
        metrics.lifetime = current_time - formation_time
        
        self.logger.debug(f"Updated metrics for cluster {cluster_id}: "
                         f"stability={metrics.stability_score:.2f}, "
                         f"connectivity={metrics.connectivity_degree}, "
                         f"mobility_var={metrics.mobility_variance:.2f}")
    
    def _calculate_stability_score(self, cluster_id: str, vehicles: List[Vehicle]) -> float:
        """Calculate cluster stability based on member retention"""
        if not hasattr(self, '_previous_cluster_members'):
            self._previous_cluster_members = {}
        
        current_members = set(v.id for v in vehicles)
        previous_members = self._previous_cluster_members.get(cluster_id, set())
        
        if not previous_members:
            self._previous_cluster_members[cluster_id] = current_members
            return 1.0  # New cluster is considered stable initially
        
        # Calculate retention rate
        retained_members = current_members & previous_members
        total_previous = len(previous_members)
        
        if total_previous == 0:
            stability = 1.0
        else:
            stability = len(retained_members) / total_previous
        
        self._previous_cluster_members[cluster_id] = current_members
        return stability
    
    def _calculate_connectivity_degree(self, vehicles: List[Vehicle]) -> int:
        """Calculate average connectivity degree within cluster"""
        if len(vehicles) < 2:
            return 0
        
        total_connections = 0
        for vehicle in vehicles:
            neighbors = self.vehicle_neighbors.get(vehicle.id, set())
            cluster_neighbors = [v for v in vehicles if v.id in neighbors]
            total_connections += len(cluster_neighbors)
        
        return total_connections // len(vehicles)
    
    def _calculate_mobility_variance(self, vehicles: List[Vehicle]) -> float:
        """Calculate mobility variance within cluster"""
        if len(vehicles) < 2:
            return 0.0
        
        speeds = [v.speed for v in vehicles]
        return statistics.variance(speeds) if len(speeds) > 1 else 0.0
    
    def _calculate_spatial_density(self, vehicles: List[Vehicle]) -> float:
        """Calculate spatial density of cluster"""
        if len(vehicles) < 2:
            return 0.0
        
        # Calculate cluster area (convex hull approximation)
        x_coords = [v.x for v in vehicles]
        y_coords = [v.y for v in vehicles]
        
        width = max(x_coords) - min(x_coords)
        height = max(y_coords) - min(y_coords)
        area = width * height
        
        if area == 0:
            return float('inf')  # All vehicles at same position
        
        return len(vehicles) / area
    
    def _should_reelect_head(self, cluster_id: str, current_time: float) -> bool:
        """Determine if cluster head should be re-elected"""
        last_election = self.cluster_head_election_times.get(cluster_id, 0)
        
        # Re-elect periodically
        if current_time - last_election >= self.reelection_interval:
            return True
        
        # Re-elect if cluster quality is poor
        metrics = self.cluster_metrics.get(cluster_id)
        if metrics and metrics.calculate_quality_score() < self.stability_threshold:
            return True
        
        return False
    
    def _elect_cluster_head(self, cluster: Cluster, all_vehicles: List[Vehicle]) -> Optional[str]:
        """Elect the best cluster head based on configured method"""
        vehicle_dict = {v.id: v for v in all_vehicles}
        
        # Get candidate vehicles
        candidates = []
        if cluster.head_id in vehicle_dict:
            candidates.append(vehicle_dict[cluster.head_id])
        for member_id in cluster.member_ids:
            if member_id in vehicle_dict:
                candidates.append(vehicle_dict[member_id])
        
        if not candidates:
            return None
        
        if self.head_election_method == ClusterHeadElectionMethod.HIGHEST_CONNECTIVITY:
            return self._elect_by_connectivity(candidates)
        elif self.head_election_method == ClusterHeadElectionMethod.LOWEST_MOBILITY:
            return self._elect_by_mobility(candidates)
        elif self.head_election_method == ClusterHeadElectionMethod.CENTRAL_POSITION:
            return self._elect_by_position(candidates, cluster)
        else:  # WEIGHTED_COMPOSITE
            return self._elect_by_composite_score(candidates, cluster)
    
    def _elect_by_connectivity(self, candidates: List[Vehicle]) -> str:
        """Elect head based on highest connectivity"""
        best_vehicle = None
        max_connectivity = -1
        
        for vehicle in candidates:
            neighbors = self.vehicle_neighbors.get(vehicle.id, set())
            connectivity = len(neighbors)
            
            if connectivity > max_connectivity:
                max_connectivity = connectivity
                best_vehicle = vehicle
        
        return best_vehicle.id if best_vehicle else candidates[0].id
    
    def _elect_by_mobility(self, candidates: List[Vehicle]) -> str:
        """Elect head based on lowest mobility (most stable)"""
        best_vehicle = None
        min_mobility = float('inf')
        
        for vehicle in candidates:
            mobility = self._calculate_vehicle_mobility(vehicle.id)
            
            if mobility < min_mobility:
                min_mobility = mobility
                best_vehicle = vehicle
        
        return best_vehicle.id if best_vehicle else candidates[0].id
    
    def _elect_by_position(self, candidates: List[Vehicle], cluster: Cluster) -> str:
        """Elect head based on position closest to cluster centroid"""
        best_vehicle = None
        min_distance = float('inf')
        
        for vehicle in candidates:
            distance = math.sqrt(
                (vehicle.x - cluster.centroid_x)**2 + 
                (vehicle.y - cluster.centroid_y)**2
            )
            
            if distance < min_distance:
                min_distance = distance
                best_vehicle = vehicle
        
        return best_vehicle.id if best_vehicle else candidates[0].id
    
    def _elect_by_composite_score(self, candidates: List[Vehicle], cluster: Cluster) -> str:
        """Elect head based on weighted composite score"""
        best_vehicle = None
        best_score = -1
        
        for vehicle in candidates:
            # Connectivity score (0-1)
            neighbors = len(self.vehicle_neighbors.get(vehicle.id, set()))
            connectivity_score = min(1.0, neighbors / 10.0)
            
            # Stability score (0-1) - lower mobility is better
            mobility = self._calculate_vehicle_mobility(vehicle.id)
            stability_score = max(0.0, 1.0 - (mobility / 50.0))
            
            # Position score (0-1) - closer to centroid is better
            distance = math.sqrt(
                (vehicle.x - cluster.centroid_x)**2 + 
                (vehicle.y - cluster.centroid_y)**2
            )
            position_score = max(0.0, 1.0 - (distance / 300.0))
            
            # Weighted composite
            composite_score = (0.4 * connectivity_score + 
                             0.4 * stability_score + 
                             0.2 * position_score)
            
            if composite_score > best_score:
                best_score = composite_score
                best_vehicle = vehicle
        
        return best_vehicle.id if best_vehicle else candidates[0].id
    
    def _calculate_vehicle_mobility(self, vehicle_id: str) -> float:
        """Calculate vehicle mobility based on position history"""
        history = self.vehicle_mobility_history.get(vehicle_id, [])
        
        if len(history) < 2:
            return 0.0
        
        # Calculate total distance traveled over time
        total_distance = 0.0
        for i in range(1, len(history)):
            prev_time, prev_x, prev_y = history[i-1]
            curr_time, curr_x, curr_y = history[i]
            
            distance = math.sqrt((curr_x - prev_x)**2 + (curr_y - prev_y)**2)
            total_distance += distance
        
        total_time = history[-1][0] - history[0][0]
        
        if total_time == 0:
            return 0.0
        
        return total_distance / total_time  # Average speed
    
    def _change_cluster_head(self, cluster_id: str, new_head_id: str, current_time: float):
        """Change cluster head and update tracking"""
        cluster = self.clustering_engine.clusters.get(cluster_id)
        if not cluster:
            return
        
        old_head = cluster.head_id
        
        # Update cluster head
        if old_head in cluster.member_ids:
            cluster.member_ids.remove(old_head)
        cluster.member_ids.add(cluster.head_id)
        cluster.head_id = new_head_id
        if new_head_id in cluster.member_ids:
            cluster.member_ids.remove(new_head_id)
        
        # Update tracking
        self.cluster_head_election_times[cluster_id] = current_time
        
        # Log event
        event = ClusterEvent(
            timestamp=current_time,
            event_type="head_change",
            cluster_id=cluster_id,
            vehicle_id=new_head_id,
            details={'old_head': old_head, 'new_head': new_head_id}
        )
        self.cluster_events.append(event)
        
        self.logger.info(f"Changed head of cluster {cluster_id} from {old_head} to {new_head_id}")
    
    def _find_merge_candidates(self, cluster_id: str, all_clusters: Dict[str, Cluster], 
                              current_time: float) -> List[str]:
        """Find clusters that could be merged with the given cluster"""
        target_cluster = all_clusters[cluster_id]
        candidates = []
        
        for other_id, other_cluster in all_clusters.items():
            if other_id == cluster_id:
                continue
            
            # Check if clusters are close enough
            distance = math.sqrt(
                (target_cluster.centroid_x - other_cluster.centroid_x)**2 + 
                (target_cluster.centroid_y - other_cluster.centroid_y)**2
            )
            
            if distance > self.clustering_engine.max_cluster_radius * 1.5:
                continue
            
            # Check if merge would improve overall quality
            merge_quality = self._calculate_merge_quality(target_cluster, other_cluster)
            
            if merge_quality > self.merge_threshold:
                candidates.append(other_id)
        
        return candidates
    
    def _calculate_merge_quality(self, cluster1: Cluster, cluster2: Cluster) -> float:
        """Calculate quality score for merging two clusters"""
        # Consider size constraints
        combined_size = cluster1.size() + cluster2.size()
        if combined_size > self.clustering_engine.max_cluster_size:
            return 0.0
        
        # Calculate compatibility
        speed_diff = abs(cluster1.avg_speed - cluster2.avg_speed)
        direction_diff = abs(cluster1.avg_direction - cluster2.avg_direction)
        direction_diff = min(direction_diff, 2*math.pi - direction_diff)
        
        speed_compatibility = max(0, 1 - (speed_diff / self.clustering_engine.speed_threshold))
        direction_compatibility = max(0, 1 - (direction_diff / self.clustering_engine.direction_threshold))
        
        # Distance factor
        distance = math.sqrt(
            (cluster1.centroid_x - cluster2.centroid_x)**2 + 
            (cluster1.centroid_y - cluster2.centroid_y)**2
        )
        distance_score = max(0, 1 - (distance / self.clustering_engine.max_cluster_radius))
        
        # Size efficiency (prefer balanced sizes)
        size_balance = 1 - abs(cluster1.size() - cluster2.size()) / max(cluster1.size(), cluster2.size())
        
        # Weighted score
        quality = (0.3 * speed_compatibility + 
                  0.3 * direction_compatibility + 
                  0.25 * distance_score + 
                  0.15 * size_balance)
        
        return quality
    
    def _should_split_cluster(self, cluster_id: str, cluster: Cluster, 
                             all_vehicles: List[Vehicle]) -> bool:
        """Determine if a cluster should be split"""
        # Check if cluster is too large
        if cluster.size() >= self.clustering_engine.max_cluster_size:
            return True
        
        # Check if cluster quality is poor
        metrics = self.cluster_metrics.get(cluster_id)
        if metrics and metrics.calculate_quality_score() < self.split_threshold:
            return True
        
        # Check for spatial fragmentation
        vehicle_dict = {v.id: v for v in all_vehicles}
        cluster_vehicles = []
        if cluster.head_id in vehicle_dict:
            cluster_vehicles.append(vehicle_dict[cluster.head_id])
        for member_id in cluster.member_ids:
            if member_id in vehicle_dict:
                cluster_vehicles.append(vehicle_dict[member_id])
        
        if len(cluster_vehicles) >= 4:  # Need minimum vehicles to split
            fragmentation = self._calculate_spatial_fragmentation(cluster_vehicles)
            if fragmentation > 0.7:  # High fragmentation
                return True
        
        return False
    
    def _calculate_spatial_fragmentation(self, vehicles: List[Vehicle]) -> float:
        """Calculate how spatially fragmented a cluster is"""
        if len(vehicles) < 2:
            return 0.0
        
        # Calculate pairwise distances
        distances = []
        for i, v1 in enumerate(vehicles):
            for j, v2 in enumerate(vehicles[i+1:], i+1):
                distances.append(v1.distance_to(v2))
        
        if not distances:
            return 0.0
        
        # Fragmentation based on distance variance
        avg_distance = statistics.mean(distances)
        if avg_distance == 0:
            return 0.0
        
        distance_variance = statistics.variance(distances)
        fragmentation = min(1.0, distance_variance / (avg_distance ** 2))
        
        return fragmentation
    
    def _plan_cluster_split(self, cluster_id: str, cluster: Cluster, 
                           all_vehicles: List[Vehicle]) -> Optional[Dict]:
        """Plan how to split a cluster into smaller clusters"""
        vehicle_dict = {v.id: v for v in all_vehicles}
        cluster_vehicles = []
        
        if cluster.head_id in vehicle_dict:
            cluster_vehicles.append(vehicle_dict[cluster.head_id])
        for member_id in cluster.member_ids:
            if member_id in vehicle_dict:
                cluster_vehicles.append(vehicle_dict[member_id])
        
        if len(cluster_vehicles) < 4:
            return None  # Can't split meaningfully
        
        # Simple split: divide based on spatial clustering
        # Use K-means with k=2 to split into two groups
        positions = [[v.x, v.y] for v in cluster_vehicles]
        
        # Calculate two centroids (simple approach)
        min_x = min(pos[0] for pos in positions)
        max_x = max(pos[0] for pos in positions)
        min_y = min(pos[1] for pos in positions)
        max_y = max(pos[1] for pos in positions)
        
        centroid1 = [(min_x + max_x) * 0.25 + min_x * 0.5, (min_y + max_y) * 0.5]
        centroid2 = [(min_x + max_x) * 0.75 + min_x * 0.5, (min_y + max_y) * 0.5]
        
        # Assign vehicles to closest centroid
        group1 = []
        group2 = []
        
        for vehicle in cluster_vehicles:
            dist1 = math.sqrt((vehicle.x - centroid1[0])**2 + (vehicle.y - centroid1[1])**2)
            dist2 = math.sqrt((vehicle.x - centroid2[0])**2 + (vehicle.y - centroid2[1])**2)
            
            if dist1 < dist2:
                group1.append(vehicle.id)
            else:
                group2.append(vehicle.id)
        
        # Ensure both groups have minimum size
        min_size = self.clustering_engine.min_cluster_size
        if len(group1) < min_size or len(group2) < min_size:
            return None
        
        return {
            'original_cluster': cluster_id,
            'group1': group1,
            'group2': group2,
            'split_reason': 'spatial_fragmentation'
        }
    
    def _update_cluster_state(self, cluster_id: str, current_time: float):
        """Update cluster state based on current conditions"""
        metrics = self.cluster_metrics.get(cluster_id)
        if not metrics:
            return
        
        current_state = self.cluster_states.get(cluster_id, ClusterState.FORMING)
        formation_time = self.cluster_formation_times.get(cluster_id, current_time)
        
        # State transition logic
        if current_state == ClusterState.FORMING:
            # Transition to stable if quality is good and some time has passed
            if (current_time - formation_time) > 10.0 and metrics.calculate_quality_score() > 0.6:
                self.cluster_states[cluster_id] = ClusterState.STABLE
                
        elif current_state == ClusterState.STABLE:
            # Check if cluster is degrading
            if metrics.calculate_quality_score() < 0.4:
                self.cluster_states[cluster_id] = ClusterState.DISSOLVING
            elif metrics.stability_score < 0.5:
                self.cluster_states[cluster_id] = ClusterState.SPLITTING
        
        # Check for dissolution due to age
        if (current_time - formation_time) > self.max_cluster_lifetime:
            self.cluster_states[cluster_id] = ClusterState.DISSOLVING
    
    def _cleanup_dissolved_clusters(self, active_clusters: Dict[str, Cluster], current_time: float):
        """Remove tracking for clusters that no longer exist"""
        active_cluster_ids = set(active_clusters.keys())
        tracked_cluster_ids = set(self.cluster_states.keys())
        
        dissolved_ids = tracked_cluster_ids - active_cluster_ids
        
        for cluster_id in dissolved_ids:
            # Log dissolution event
            event = ClusterEvent(
                timestamp=current_time,
                event_type="cluster_dissolved",
                cluster_id=cluster_id
            )
            self.cluster_events.append(event)
            
            # Clean up tracking
            self.cluster_states.pop(cluster_id, None)
            self.cluster_metrics.pop(cluster_id, None)
            self.cluster_formation_times.pop(cluster_id, None)
            self.cluster_head_election_times.pop(cluster_id, None)
            
            if hasattr(self, '_previous_cluster_members'):
                self._previous_cluster_members.pop(cluster_id, None)
            
            self.logger.info(f"Cleaned up dissolved cluster {cluster_id}")
    
    def get_cluster_management_statistics(self) -> Dict:
        """Get comprehensive cluster management statistics"""
        total_events = len(self.cluster_events)
        recent_events = [e for e in self.cluster_events if time.time() - e.timestamp <= 300]  # Last 5 minutes
        
        event_types = {}
        for event in recent_events:
            event_types[event.event_type] = event_types.get(event.event_type, 0) + 1
        
        # Calculate average cluster quality
        if self.cluster_metrics:
            avg_quality = statistics.mean(m.calculate_quality_score() for m in self.cluster_metrics.values())
            avg_lifetime = statistics.mean(m.lifetime for m in self.cluster_metrics.values())
        else:
            avg_quality = 0.0
            avg_lifetime = 0.0
        
        # State distribution
        state_distribution = {}
        for state in self.cluster_states.values():
            state_distribution[state.value] = state_distribution.get(state.value, 0) + 1
        
        return {
            'total_managed_clusters': len(self.cluster_states),
            'average_cluster_quality': avg_quality,
            'average_cluster_lifetime': avg_lifetime,
            'state_distribution': state_distribution,
            'total_events': total_events,
            'recent_events': len(recent_events),
            'event_type_distribution': event_types,
            'head_election_method': self.head_election_method.value
        }