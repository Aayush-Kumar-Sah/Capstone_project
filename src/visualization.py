"""
Visualization script for VANET clustering
"""

import matplotlib.pyplot as plt
import numpy as np
import traci
import time
from matplotlib.patches import Circle
import matplotlib.colors as mcolors

class ClusterVisualizer:
    def __init__(self):
        self.fig, self.ax = plt.subplots(figsize=(12, 12))
        self.colors = list(mcolors.TABLEAU_COLORS.values())
        
    def update(self, vehicle_nodes, cluster_manager):
        """Update visualization"""
        self.ax.clear()
        
        # Plot vehicles
        for vid, node in vehicle_nodes.items():
            x, y = node.location
            
            # Determine node color and style
            if vid in cluster_manager.cluster_heads:
                color = 'red'
                size = 100
                marker = '*'
            elif vid in cluster_manager.relay_nodes:
                color = 'green'
                size = 80
                marker = 's'
            elif vid in cluster_manager.boundary_nodes:
                color = 'blue'
                size = 80
                marker = '^'
            else:
                color = 'gray'
                size = 50
                marker = 'o'
                
            self.ax.scatter(x, y, c=color, s=size, marker=marker, label=vid)
            
            # Draw connections
            for neighbor_id in node.connections:
                if neighbor_id in vehicle_nodes:
                    neighbor = vehicle_nodes[neighbor_id]
                    self.ax.plot([x, neighbor.location[0]], 
                               [y, neighbor.location[1]], 
                               'k-', alpha=0.2)
        
        # Draw cluster boundaries
        for i, (head_id, members) in enumerate(cluster_manager.clusters.items()):
            if head_id in vehicle_nodes:
                head_node = vehicle_nodes[head_id]
                color = self.colors[i % len(self.colors)]
                circle = Circle(head_node.location, 300, 
                              fill=False, linestyle='--', 
                              color=color, alpha=0.5)
                self.ax.add_patch(circle)
        
        # Set plot properties
        self.ax.set_xlim(0, 2500)
        self.ax.set_ylim(0, 2500)
        self.ax.set_xlabel('X Position (m)')
        self.ax.set_ylabel('Y Position (m)')
        self.ax.set_title('VANET Clustering Visualization')
        
        # Add legend
        legend_elements = [
            plt.Line2D([0], [0], marker='*', color='w', 
                      markerfacecolor='red', markersize=15, label='Cluster Head'),
            plt.Line2D([0], [0], marker='s', color='w', 
                      markerfacecolor='green', markersize=10, label='Relay Node'),
            plt.Line2D([0], [0], marker='^', color='w', 
                      markerfacecolor='blue', markersize=10, label='Boundary Node'),
            plt.Line2D([0], [0], marker='o', color='w', 
                      markerfacecolor='gray', markersize=10, label='Member Node')
        ]
        self.ax.legend(handles=legend_elements, loc='upper right')
        
        plt.pause(0.1)

def main():
    try:
        # Connect to SUMO
        traci.start(["sumo-gui", "-c", "config.sumo.cfg"])
        
        # Initialize visualizer
        visualizer = ClusterVisualizer()
        
        # Main simulation loop
        step = 0
        while step < 1000:  # Run for 1000 steps
            traci.simulationStep()
            
            # Get vehicle data and update visualization
            # (This part would integrate with your CustomVANETApplication)
            
            step += 1
            
        traci.close()
        plt.show()
        
    except Exception as e:
        print(f"Error in visualization: {e}")
        if 'traci' in globals() and traci.isLoaded():
            traci.close()

if __name__ == "__main__":
    main()