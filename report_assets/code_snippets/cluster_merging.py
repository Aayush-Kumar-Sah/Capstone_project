# Cluster Merging Algorithm
# Prevents sub-clustering by merging overlapping clusters based on leader proximity and member overlap
# Function: _merge_overlapping_clusters

def _merge_overlapping_clusters(self, current_time: float):
    """Merge overlapping clusters to prevent sub-clustering"""
    MERGE_DISTANCE_THRESHOLD = 450  # If cluster centers are within 450 pixels, consider merging (matches max_cluster_radius)
    
    clusters_to_merge = []
    processed_clusters = set()
    
    cluster_list = list(self.app.clustering_engine.clusters.items())
    
    for i, (cluster_id_1, cluster_1) in enumerate(cluster_list):
        if cluster_id_1 in processed_clusters:
            continue
        
        if not cluster_1.member_ids or not cluster_1.head_id:
            continue
        
        # Get cluster 1 center (leader position)
        if cluster_1.head_id in self.app.vehicle_nodes:
            c1_x, c1_y = self.app.vehicle_nodes[cluster_1.head_id].location
        else:
            continue
        
        merge_candidates = []
        
        for j, (cluster_id_2, cluster_2) in enumerate(cluster_list[i+1:], start=i+1):
            if cluster_id_2 in processed_clusters:
                continue
            
            if not cluster_2.member_ids or not cluster_2.head_id:
                continue
            
            # Get cluster 2 center (leader position)
            if cluster_2.head_id in self.app.vehicle_nodes:
                c2_x, c2_y = self.app.vehicle_nodes[cluster_2.head_id].location
            else:
                continue
            
            # Calculate distance between cluster centers
            distance = math.sqrt((c1_x - c2_x)**2 + (c1_y - c2_y)**2)
            
            # Check if clusters overlap significantly
            if distance < MERGE_DISTANCE_THRESHOLD:
                # Count how many members are shared or very close
                shared_members = 0
                for member_id in cluster_2.member_ids:
                    if member_id in cluster_1.member_ids:
                        shared_members += 1
                    elif member_id in self.app.vehicle_nodes:
                        member_x, member_y = self.app.vehicle_nodes[member_id].location
                        dist_to_c1 = math.sqrt((member_x - c1_x)**2 + (member_y - c1_y)**2)
                        if dist_to_c1 < 250:  # Within communication range of cluster 1
                            shared_members += 1
                
                # If significant overlap, mark for merging
                overlap_ratio = shared_members / max(len(cluster_2.member_ids), 1)
                if overlap_ratio > 0.3 or distance < 350:  # 30% overlap or very close
                    merge_candidates.append(cluster_id_2)
        
        if merge_candidates:
            clusters_to_merge.append((cluster_id_1, merge_candidates))
            processed_clusters.add(cluster_id_1)
            processed_clusters.update(merge_candidates)
    
    # Perform merges
    for primary_cluster_id, secondary_cluster_ids in clusters_to_merge:
        if primary_cluster_id not in self.app.clustering_engine.clusters:
            continue
        
        primary_cluster = self.app.clustering_engine.clusters[primary_cluster_id]
        
        for secondary_id in secondary_cluster_ids:
            if secondary_id not in self.app.clustering_engine.clusters:
                continue
            
            secondary_cluster = self.app.clustering_engine.clusters[secondary_id]
            
            # Merge members
            for member_id in secondary_cluster.member_ids:
                if member_id not in primary_cluster.member_ids:
                    primary_cluster.member_ids.add(member_id)
                    
                    # Update vehicle's cluster assignment
                    if member_id in self.app.vehicle_nodes:
                        self.app.vehicle_nodes[member_id].cluster_id = primary_cluster_id
            
            # Remove the secondary cluster's head from being a head
            if secondary_cluster.head_id and secondary_cluster.head_id in self.app.vehicle_nodes:
                self.app.vehicle_nodes[secondary_cluster.head_id].is_cluster_head = False
                # Add to primary cluster as regular member if not already there
                if secondary_cluster.head_id not in primary_cluster.member_ids:
                    primary_cluster.member_ids.add(secondary_cluster.head_id)
                    self.app.vehicle_nodes[secondary_cluster.head_id].cluster_id = primary_cluster_id
            
            # Delete the secondary cluster
            del self.app.clustering_engine.clusters[secondary_id]
        
        if current_time % 30 < 0.5:  # Log occasionally
            print(f"   🔗  Merged {len(secondary_cluster_ids)} overlapping clusters into {primary_cluster_id}")
