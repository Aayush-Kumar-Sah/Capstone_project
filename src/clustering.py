"""
Vehicle Clustering Algorithms for VANET

This module implements various clustering algorithms specifically designed
for Vehicular Ad-hoc Networks (VANETs), taking into account vehicle mobility,
direction, speed, and proximity.
"""

import math
import statistics
from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass
from enum import Enum
import logging
import random

class ClusteringAlgorithm(Enum):
    KMEANS = "kmeans"
    DBSCAN = "dbscan"
    MOBILITY_BASED = "mobility_based"
    DIRECTION_BASED = "direction_based"

@dataclass
class Vehicle:
    """Represents a vehicle in the VANET"""
    id: str
    x: float
    y: float
    speed: float
    direction: float  # in radians
    lane_id: str
    timestamp: float
    
    def distance_to(self, other: 'Vehicle') -> float:
        """Calculate Euclidean distance to another vehicle"""
        return math.sqrt((self.x - other.x)**2 + (self.y - other.y)**2)
    
    def speed_similarity(self, other: 'Vehicle') -> float:
        """Calculate speed similarity (0-1, where 1 is identical speed)"""
        max_speed_diff = 50.0  # m/s, adjust based on scenario
        speed_diff = abs(self.speed - other.speed)
        return max(0, 1 - (speed_diff / max_speed_diff))
    
    def direction_similarity(self, other: 'Vehicle') -> float:
        """Calculate direction similarity (0-1, where 1 is same direction)"""
        angle_diff = abs(self.direction - other.direction)
        angle_diff = min(angle_diff, 2*math.pi - angle_diff)  # Handle wraparound
        return max(0, 1 - (angle_diff / math.pi))

@dataclass
class Cluster:
    """Represents a vehicle cluster"""
    id: str
    head_id: str
    member_ids: Set[str]
    centroid_x: float
    centroid_y: float
    avg_speed: float
    avg_direction: float
    formation_time: float
    last_update: float
    
    def add_member(self, vehicle_id: str):
        """Add a vehicle to the cluster"""
        self.member_ids.add(vehicle_id)
    
    def remove_member(self, vehicle_id: str):
        """Remove a vehicle from the cluster"""
        self.member_ids.discard(vehicle_id)
    
    def size(self) -> int:
        """Return cluster size including head"""
        return len(self.member_ids) + (1 if self.head_id else 0)

class VehicleClustering:
    """Main clustering engine for VANET vehicles"""
    
    def __init__(self, algorithm: ClusteringAlgorithm = ClusteringAlgorithm.MOBILITY_BASED):
        self.algorithm = algorithm
        self.clusters: Dict[str, Cluster] = {}
        self.vehicle_to_cluster: Dict[str, str] = {}
        self.logger = logging.getLogger(__name__)
        
        # Clustering parameters
        self.max_cluster_radius = 300.0  # meters
        self.min_cluster_size = 2
        self.max_cluster_size = 10
        self.speed_threshold = 5.0  # m/s difference
        self.direction_threshold = 0.5  # radians difference
        self.cluster_lifetime_threshold = 30.0  # seconds
    
    def update_vehicles(self, vehicles: List[Vehicle]) -> Dict[str, Cluster]:
        """Update clustering based on current vehicle positions"""
        if self.algorithm == ClusteringAlgorithm.MOBILITY_BASED:
            return self._mobility_based_clustering(vehicles)
        elif self.algorithm == ClusteringAlgorithm.DIRECTION_BASED:
            return self._direction_based_clustering(vehicles)
        elif self.algorithm == ClusteringAlgorithm.KMEANS:
            return self._kmeans_clustering(vehicles)
        elif self.algorithm == ClusteringAlgorithm.DBSCAN:
            return self._dbscan_clustering(vehicles)
        else:
            raise ValueError(f"Unknown clustering algorithm: {self.algorithm}")
    
    def _mobility_based_clustering(self, vehicles: List[Vehicle]) -> Dict[str, Cluster]:
        """
        Cluster vehicles based on mobility patterns (speed, direction, proximity)
        This is the recommended algorithm for VANET scenarios
        """
        current_time = vehicles[0].timestamp if vehicles else 0.0
        
        # Debug logging
        self.logger.debug(f"Starting mobility-based clustering with {len(vehicles)} vehicles")
        
        # Remove outdated clusters
        self._cleanup_clusters(current_time)
        
        # Create vehicle lookup
        vehicle_dict = {v.id: v for v in vehicles}
        
        # Process each vehicle
        for vehicle in vehicles:
            current_cluster_id = self.vehicle_to_cluster.get(vehicle.id)
            
            if current_cluster_id and current_cluster_id in self.clusters:
                # Check if vehicle should stay in current cluster
                if self._should_stay_in_cluster(vehicle, vehicle_dict, current_cluster_id):
                    self._update_cluster_with_vehicle(vehicle, current_cluster_id, current_time)
                    continue
                else:
                    # Remove from current cluster
                    self._remove_vehicle_from_cluster(vehicle.id, current_cluster_id)
            
            # Find best cluster to join or create new one
            best_cluster_id = self._find_best_cluster(vehicle, vehicle_dict)
            
            if best_cluster_id:
                self._add_vehicle_to_cluster(vehicle, best_cluster_id, current_time)
            else:
                # Create new cluster if we have nearby vehicles
                nearby_vehicles = self._find_nearby_vehicles(vehicle, vehicles)
                self.logger.debug(f"Vehicle {vehicle.id} found {len(nearby_vehicles)} nearby vehicles")
                
                if len(nearby_vehicles) >= self.min_cluster_size - 1:
                    self.logger.info(f"Creating new cluster for vehicle {vehicle.id} with {len(nearby_vehicles)} nearby vehicles")
                    self._create_new_cluster(vehicle, nearby_vehicles, current_time)
        
        self.logger.debug(f"Mobility clustering completed: {len(self.clusters)} clusters formed")
        return self.clusters
    
    def _direction_based_clustering(self, vehicles: List[Vehicle]) -> Dict[str, Cluster]:
        """Cluster vehicles primarily based on direction and lane"""
        # Group vehicles by similar direction first
        direction_groups = {}
        direction_tolerance = 0.3  # radians
        
        for vehicle in vehicles:
            direction_key = round(vehicle.direction / direction_tolerance)
            if direction_key not in direction_groups:
                direction_groups[direction_key] = []
            direction_groups[direction_key].append(vehicle)
        
        # Within each direction group, cluster by proximity
        current_time = vehicles[0].timestamp if vehicles else 0.0
        self.clusters.clear()
        self.vehicle_to_cluster.clear()
        
        cluster_counter = 0
        for direction_key, group_vehicles in direction_groups.items():
            if len(group_vehicles) < self.min_cluster_size:
                continue
                
            # Simple proximity clustering within direction group
            used_vehicles = set()
            for i, vehicle in enumerate(group_vehicles):
                if vehicle.id in used_vehicles:
                    continue
                    
                cluster_vehicles = [vehicle]
                used_vehicles.add(vehicle.id)
                
                for j, other_vehicle in enumerate(group_vehicles[i+1:], i+1):
                    if other_vehicle.id in used_vehicles:
                        continue
                    
                    if (vehicle.distance_to(other_vehicle) <= self.max_cluster_radius and
                        len(cluster_vehicles) < self.max_cluster_size):
                        cluster_vehicles.append(other_vehicle)
                        used_vehicles.add(other_vehicle.id)
                
                if len(cluster_vehicles) >= self.min_cluster_size:
                    cluster_id = f"cluster_{cluster_counter}"
                    self._create_cluster_from_vehicles(cluster_id, cluster_vehicles, current_time)
                    cluster_counter += 1
        
        return self.clusters
    
    def _find_nearby_vehicles(self, target_vehicle: Vehicle, all_vehicles: List[Vehicle]) -> List[Vehicle]:
        """Find vehicles within clustering radius that are mobility-compatible"""
        nearby = []
        
        for vehicle in all_vehicles:
            if vehicle.id == target_vehicle.id:
                continue
                
            distance = target_vehicle.distance_to(vehicle)
            if distance > self.max_cluster_radius:
                continue
                
            speed_diff = abs(target_vehicle.speed - vehicle.speed)
            if speed_diff > self.speed_threshold:
                continue
                
            direction_diff = abs(target_vehicle.direction - vehicle.direction)
            direction_diff = min(direction_diff, 2*math.pi - direction_diff)
            if direction_diff > self.direction_threshold:
                continue
                
            nearby.append(vehicle)
        
        return nearby
    
    def _should_stay_in_cluster(self, vehicle: Vehicle, vehicle_dict: Dict[str, Vehicle], 
                               cluster_id: str) -> bool:
        """Check if vehicle should remain in its current cluster"""
        cluster = self.clusters.get(cluster_id)
        if not cluster:
            return False
        
        # Check if still within radius of cluster centroid
        distance_to_centroid = math.sqrt(
            (vehicle.x - cluster.centroid_x)**2 + 
            (vehicle.y - cluster.centroid_y)**2
        )
        
        if distance_to_centroid > self.max_cluster_radius * 1.2:  # Allow some tolerance
            return False
        
        # Check mobility compatibility with cluster
        speed_diff = abs(vehicle.speed - cluster.avg_speed)
        if speed_diff > self.speed_threshold * 1.5:  # Allow some tolerance
            return False
        
        direction_diff = abs(vehicle.direction - cluster.avg_direction)
        direction_diff = min(direction_diff, 2*math.pi - direction_diff)
        if direction_diff > self.direction_threshold * 1.5:  # Allow some tolerance
            return False
        
        return True
    
    def _find_best_cluster(self, vehicle: Vehicle, vehicle_dict: Dict[str, Vehicle]) -> Optional[str]:
        """Find the best existing cluster for a vehicle to join"""
        best_cluster_id = None
        best_score = float('-inf')
        
        for cluster_id, cluster in self.clusters.items():
            if cluster.size() >= self.max_cluster_size:
                continue
            
            # Calculate distance to cluster centroid
            distance = math.sqrt(
                (vehicle.x - cluster.centroid_x)**2 + 
                (vehicle.y - cluster.centroid_y)**2
            )
            
            if distance > self.max_cluster_radius:
                continue
            
            # Calculate compatibility score
            score = self._calculate_cluster_compatibility(vehicle, cluster)
            
            if score > best_score:
                best_score = score
                best_cluster_id = cluster_id
        
        return best_cluster_id if best_score > 0.5 else None
    
    def _calculate_cluster_compatibility(self, vehicle: Vehicle, cluster: Cluster) -> float:
        """Calculate how compatible a vehicle is with a cluster (0-1)"""
        # Distance factor (closer is better)
        distance = math.sqrt(
            (vehicle.x - cluster.centroid_x)**2 + 
            (vehicle.y - cluster.centroid_y)**2
        )
        distance_score = max(0, 1 - (distance / self.max_cluster_radius))
        
        # Speed similarity
        speed_diff = abs(vehicle.speed - cluster.avg_speed)
        speed_score = max(0, 1 - (speed_diff / self.speed_threshold))
        
        # Direction similarity
        direction_diff = abs(vehicle.direction - cluster.avg_direction)
        direction_diff = min(direction_diff, 2*math.pi - direction_diff)
        direction_score = max(0, 1 - (direction_diff / self.direction_threshold))
        
        # Weighted combination
        total_score = (0.4 * distance_score + 0.3 * speed_score + 0.3 * direction_score)
        return total_score
    
    def _create_new_cluster(self, head_vehicle: Vehicle, member_vehicles: List[Vehicle], 
                           current_time: float):
        """Create a new cluster with the given vehicles"""
        cluster_id = f"cluster_{len(self.clusters)}"
        all_vehicles = [head_vehicle] + member_vehicles
        self._create_cluster_from_vehicles(cluster_id, all_vehicles, current_time)
    
    def _create_cluster_from_vehicles(self, cluster_id: str, vehicles: List[Vehicle], 
                                    current_time: float):
        """Create a cluster from a list of vehicles"""
        if not vehicles:
            return
        
        # Select cluster head (vehicle with highest speed or central position)
        head_vehicle = max(vehicles, key=lambda v: v.speed)
        member_vehicles = [v for v in vehicles if v.id != head_vehicle.id]
        
        # Calculate cluster properties
        centroid_x = sum(v.x for v in vehicles) / len(vehicles)
        centroid_y = sum(v.y for v in vehicles) / len(vehicles)
        avg_speed = sum(v.speed for v in vehicles) / len(vehicles)
        avg_direction = self._calculate_average_direction([v.direction for v in vehicles])
        
        # Create cluster
        cluster = Cluster(
            id=cluster_id,
            head_id=head_vehicle.id,
            member_ids=set(v.id for v in member_vehicles),
            centroid_x=centroid_x,
            centroid_y=centroid_y,
            avg_speed=avg_speed,
            avg_direction=avg_direction,
            formation_time=current_time,
            last_update=current_time
        )
        
        self.clusters[cluster_id] = cluster
        
        # Update vehicle-to-cluster mapping
        for vehicle in vehicles:
            self.vehicle_to_cluster[vehicle.id] = cluster_id
        
        self.logger.info(f"Created cluster {cluster_id} with {len(vehicles)} vehicles")
    
    def _calculate_average_direction(self, directions: List[float]) -> float:
        """Calculate average direction handling circular nature of angles"""
        if not directions:
            return 0.0
        
        sin_sum = sum(math.sin(d) for d in directions)
        cos_sum = sum(math.cos(d) for d in directions)
        
        return math.atan2(sin_sum, cos_sum)
    
    def _add_vehicle_to_cluster(self, vehicle: Vehicle, cluster_id: str, current_time: float):
        """Add a vehicle to an existing cluster"""
        cluster = self.clusters[cluster_id]
        cluster.add_member(vehicle.id)
        self.vehicle_to_cluster[vehicle.id] = cluster_id
        self._update_cluster_with_vehicle(vehicle, cluster_id, current_time)
        
        self.logger.debug(f"Added vehicle {vehicle.id} to cluster {cluster_id}")
    
    def _remove_vehicle_from_cluster(self, vehicle_id: str, cluster_id: str):
        """Remove a vehicle from its cluster"""
        if cluster_id not in self.clusters:
            return
        
        cluster = self.clusters[cluster_id]
        
        if cluster.head_id == vehicle_id:
            # If head is leaving, promote a member or dissolve cluster
            if cluster.member_ids:
                new_head = cluster.member_ids.pop()
                cluster.head_id = new_head
                self.logger.info(f"Promoted vehicle {new_head} to head of cluster {cluster_id}")
            else:
                # Dissolve cluster
                del self.clusters[cluster_id]
                self.logger.info(f"Dissolved cluster {cluster_id}")
        else:
            cluster.remove_member(vehicle_id)
        
        if vehicle_id in self.vehicle_to_cluster:
            del self.vehicle_to_cluster[vehicle_id]
        
        # Check if cluster is too small
        if cluster_id in self.clusters and cluster.size() < self.min_cluster_size:
            self._dissolve_cluster(cluster_id)
    
    def _update_cluster_with_vehicle(self, vehicle: Vehicle, cluster_id: str, current_time: float):
        """Update cluster properties when a vehicle updates its state"""
        cluster = self.clusters[cluster_id]
        cluster.last_update = current_time
        
        # Recalculate cluster properties (simplified - could be optimized)
        # In a real implementation, you'd incrementally update these
        cluster.centroid_x = (cluster.centroid_x + vehicle.x) / 2
        cluster.centroid_y = (cluster.centroid_y + vehicle.y) / 2
        cluster.avg_speed = (cluster.avg_speed + vehicle.speed) / 2
    
    def _dissolve_cluster(self, cluster_id: str):
        """Dissolve a cluster and remove all vehicle mappings"""
        if cluster_id not in self.clusters:
            return
        
        cluster = self.clusters[cluster_id]
        
        # Remove all vehicle mappings
        if cluster.head_id in self.vehicle_to_cluster:
            del self.vehicle_to_cluster[cluster.head_id]
        
        for member_id in cluster.member_ids:
            if member_id in self.vehicle_to_cluster:
                del self.vehicle_to_cluster[member_id]
        
        del self.clusters[cluster_id]
        self.logger.info(f"Dissolved cluster {cluster_id}")
    
    def _cleanup_clusters(self, current_time: float):
        """Remove old or invalid clusters"""
        clusters_to_remove = []
        
        for cluster_id, cluster in self.clusters.items():
            # Remove clusters that haven't been updated recently
            if (current_time - cluster.last_update) > self.cluster_lifetime_threshold:
                clusters_to_remove.append(cluster_id)
        
        for cluster_id in clusters_to_remove:
            self._dissolve_cluster(cluster_id)
    
    def get_cluster_for_vehicle(self, vehicle_id: str) -> Optional[Cluster]:
        """Get the cluster that a vehicle belongs to"""
        cluster_id = self.vehicle_to_cluster.get(vehicle_id)
        return self.clusters.get(cluster_id) if cluster_id else None
    
    def get_cluster_statistics(self) -> Dict:
        """Get clustering statistics"""
        if not self.clusters:
            return {
                'total_clusters': 0,
                'total_clustered_vehicles': 0,
                'avg_cluster_size': 0,
                'largest_cluster_size': 0
            }
        
        cluster_sizes = [cluster.size() for cluster in self.clusters.values()]
        total_vehicles = sum(cluster_sizes)
        
        return {
            'total_clusters': len(self.clusters),
            'total_clustered_vehicles': total_vehicles,
            'avg_cluster_size': total_vehicles / len(self.clusters),
            'largest_cluster_size': max(cluster_sizes),
            'smallest_cluster_size': min(cluster_sizes)
        }

    # Additional clustering algorithms (K-means and DBSCAN)
    def _kmeans_clustering(self, vehicles: List[Vehicle]) -> Dict[str, Cluster]:
        """K-means clustering implementation for vehicles (pure Python)"""
        if len(vehicles) < self.min_cluster_size:
            return {}
        
        # Simple K-means implementation without NumPy
        k = max(2, len(vehicles) // 5)  # Adjust K based on vehicle count
        
        # Initialize centroids randomly
        positions = [[v.x, v.y] for v in vehicles]
        centroids = []
        
        # Select random initial centroids
        for i in range(k):
            idx = random.randint(0, len(positions) - 1)
            centroids.append([positions[idx][0], positions[idx][1]])
        
        # K-means iterations
        for iteration in range(10):  # Max iterations
            # Assign vehicles to closest centroid
            assignments = []
            for pos in positions:
                min_dist = float('inf')
                closest_centroid = 0
                
                for c_idx, centroid in enumerate(centroids):
                    dist = math.sqrt((pos[0] - centroid[0])**2 + (pos[1] - centroid[1])**2)
                    if dist < min_dist:
                        min_dist = dist
                        closest_centroid = c_idx
                
                assignments.append(closest_centroid)
            
            # Update centroids
            new_centroids = []
            for c_idx in range(k):
                # Find all points assigned to this centroid
                cluster_points = [positions[i] for i in range(len(positions)) if assignments[i] == c_idx]
                
                if cluster_points:
                    # Calculate mean position
                    mean_x = sum(p[0] for p in cluster_points) / len(cluster_points)
                    mean_y = sum(p[1] for p in cluster_points) / len(cluster_points)
                    new_centroids.append([mean_x, mean_y])
                else:
                    # Keep old centroid if no points assigned
                    new_centroids.append(centroids[c_idx])
            
            centroids = new_centroids
        
        # Create clusters from assignments
        self.clusters.clear()
        self.vehicle_to_cluster.clear()
        current_time = vehicles[0].timestamp if vehicles else 0.0
        
        for i in range(k):
            cluster_vehicles = [vehicles[j] for j in range(len(vehicles)) if assignments[j] == i]
            if len(cluster_vehicles) >= self.min_cluster_size:
                cluster_id = f"kmeans_cluster_{i}"
                self._create_cluster_from_vehicles(cluster_id, cluster_vehicles, current_time)
        
        return self.clusters
    
    def _dbscan_clustering(self, vehicles: List[Vehicle]) -> Dict[str, Cluster]:
        """DBSCAN clustering implementation for vehicles (pure Python)"""
        if len(vehicles) < self.min_cluster_size:
            return {}
        
        # Simple DBSCAN implementation without NumPy
        eps = self.max_cluster_radius
        min_pts = self.min_cluster_size
        
        positions = [[v.x, v.y] for v in vehicles]
        labels = [-1] * len(vehicles)  # -1 means noise
        cluster_id = 0
        
        for i, vehicle in enumerate(vehicles):
            if labels[i] != -1:  # Already processed
                continue
            
            # Find neighbors
            neighbors = []
            for j, other_pos in enumerate(positions):
                dist = math.sqrt((positions[i][0] - other_pos[0])**2 + 
                               (positions[i][1] - other_pos[1])**2)
                if dist <= eps:
                    neighbors.append(j)
            
            if len(neighbors) < min_pts:
                continue  # Noise point
            
            # Start new cluster
            labels[i] = cluster_id
            seed_set = neighbors[:]
            
            j = 0
            while j < len(seed_set):
                point_idx = seed_set[j]
                
                if labels[point_idx] == -1:  # Noise point
                    labels[point_idx] = cluster_id
                elif labels[point_idx] != -1:  # Already in another cluster
                    j += 1
                    continue
                
                labels[point_idx] = cluster_id
                
                # Find neighbors of this point
                point_neighbors = []
                for k, other_pos in enumerate(positions):
                    dist = math.sqrt((positions[point_idx][0] - other_pos[0])**2 + 
                                   (positions[point_idx][1] - other_pos[1])**2)
                    if dist <= eps:
                        point_neighbors.append(k)
                
                if len(point_neighbors) >= min_pts:
                    for neighbor_idx in point_neighbors:
                        if neighbor_idx not in seed_set:
                            seed_set.append(neighbor_idx)
                
                j += 1
            
            cluster_id += 1
        
        # Create clusters from labels
        self.clusters.clear()
        self.vehicle_to_cluster.clear()
        current_time = vehicles[0].timestamp if vehicles else 0.0
        
        for cid in range(cluster_id):
            cluster_vehicles = [vehicles[i] for i in range(len(vehicles)) if labels[i] == cid]
            if len(cluster_vehicles) >= self.min_cluster_size:
                cluster_name = f"dbscan_cluster_{cid}"
                self._create_cluster_from_vehicles(cluster_name, cluster_vehicles, current_time)
        
        return self.clusters