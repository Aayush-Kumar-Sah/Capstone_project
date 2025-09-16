"""
Custom VANET application implementing the P2P clustering algorithm.
"""

import os
import sys
from enum import Enum
import traci
from .clustering import ClusterManager
from .vehicle_node import VehicleNode

class MessageType(Enum):
    BEACON = 1
    CLUSTER_HEAD_ANNOUNCEMENT = 2
    JOIN_REQUEST = 3
    JOIN_RESPONSE = 4
    RELAY_ANNOUNCEMENT = 5
    BOUNDARY_UPDATE = 6

class CustomVANETApplication:
    def __init__(self):
        self.cluster_manager = ClusterManager()
        self.vehicle_nodes = {}  # vid -> VehicleNode
        self.beacon_interval = 1.0  # seconds
        self.cluster_update_interval = 5.0  # seconds
        self.last_beacon_time = 0
        self.last_cluster_update = 0

    def initialize(self):
        """Initialize the VANET application"""
        try:
            if 'SUMO_HOME' in os.environ:
                tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
                sys.path.append(tools)
            else:
                sys.exit("Please declare environment variable 'SUMO_HOME'")
        except Exception as e:
            print(f"Error initializing VANET application: {e}")

    def handle_timeStep(self, step):
        """Handle simulation time step"""
        try:
            # Update vehicle positions and states
            self._update_vehicle_states()

            # Send periodic beacons
            if step - self.last_beacon_time >= self.beacon_interval:
                self._send_beacons()
                self.last_beacon_time = step

            # Update clustering
            if step - self.last_cluster_update >= self.cluster_update_interval:
                self._update_clustering()
                self.last_cluster_update = step

        except Exception as e:
            print(f"Error in time step handling: {e}")

    def _update_vehicle_states(self):
        """Update vehicle states from SUMO"""
        try:
            # Get current vehicle IDs
            vehicle_ids = traci.vehicle.getIDList()

            # Remove vehicles that left the simulation
            for vid in list(self.vehicle_nodes.keys()):
                if vid not in vehicle_ids:
                    del self.vehicle_nodes[vid]

            # Update or add vehicles
            for vid in vehicle_ids:
                pos = traci.vehicle.getPosition(vid)
                speed = traci.vehicle.getSpeed(vid)
                angle = traci.vehicle.getAngle(vid)

                if vid not in self.vehicle_nodes:
                    # Create new vehicle node
                    self.vehicle_nodes[vid] = VehicleNode(
                        node_id=vid,
                        location=(pos[0], pos[1]),
                        speed=speed,
                        direction=angle
                    )
                else:
                    # Update existing vehicle
                    self.vehicle_nodes[vid].update_location(pos[0], pos[1])
                    self.vehicle_nodes[vid].update_status(speed, angle)

        except Exception as e:
            print(f"Error updating vehicle states: {e}")

    def _send_beacons(self):
        """Send periodic beacons from all vehicles"""
        try:
            for vid, node in self.vehicle_nodes.items():
                # Get vehicle's cluster status
                is_cluster_head = vid in self.cluster_manager.cluster_heads
                is_relay = vid in self.cluster_manager.relay_nodes
                is_boundary = vid in self.cluster_manager.boundary_nodes

                # Prepare beacon message
                message = {
                    'type': MessageType.BEACON,
                    'vehicle_id': vid,
                    'position': node.location,
                    'speed': node.speed,
                    'direction': node.direction,
                    'is_cluster_head': is_cluster_head,
                    'is_relay': is_relay,
                    'is_boundary': is_boundary
                }

                # In real implementation, this would use DSRC/WAVE communication
                # For simulation, we use TraCI to get neighboring vehicles
                radius = 300  # communication radius in meters
                neighbors = self._get_neighbors(vid, radius)
                
                # Update node connections
                node.connections = neighbors

        except Exception as e:
            print(f"Error sending beacons: {e}")

    def _update_clustering(self):
        """Update cluster formation"""
        try:
            # Convert dictionary to list for cluster manager
            nodes = list(self.vehicle_nodes.values())

            # Update clusters
            self.cluster_manager.form_clusters(nodes)

            # Select relay nodes
            self.cluster_manager.select_relay_nodes(nodes)

            # Update cluster status
            self.cluster_manager.update_cluster_status(nodes)

            # Log clustering information
            self._log_cluster_info()

        except Exception as e:
            print(f"Error updating clustering: {e}")

    def _get_neighbors(self, vehicle_id, radius):
        """Get neighboring vehicles within radius"""
        try:
            neighbors = []
            vehicle_pos = traci.vehicle.getPosition(vehicle_id)
            
            for other_id in traci.vehicle.getIDList():
                if other_id != vehicle_id:
                    other_pos = traci.vehicle.getPosition(other_id)
                    distance = ((vehicle_pos[0] - other_pos[0])**2 + 
                              (vehicle_pos[1] - other_pos[1])**2)**0.5
                    if distance <= radius:
                        neighbors.append(other_id)
            
            return neighbors

        except Exception as e:
            print(f"Error getting neighbors: {e}")
            return []

    def _log_cluster_info(self):
        """Log clustering information for visualization"""
        try:
            print("\nClustering Status:")
            print(f"Number of clusters: {len(self.cluster_manager.clusters)}")
            print(f"Number of relay nodes: {len(self.cluster_manager.relay_nodes)}")
            print(f"Number of boundary nodes: {len(self.cluster_manager.boundary_nodes)}")
            
            for head_id, members in self.cluster_manager.clusters.items():
                print(f"\nCluster {head_id}:")
                print(f"Members: {members}")

        except Exception as e:
            print(f"Error logging cluster info: {e}")
