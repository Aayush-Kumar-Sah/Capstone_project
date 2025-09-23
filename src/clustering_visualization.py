"""
VANET Clustering Visualization Tools

This module provides visualization capabilities for displaying vehicle clusters,
cluster heads, and membership changes in SUMO simulation environment.
"""

import time
import math
import logging
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass
from enum import Enum
import colorsys

try:
    import traci
    TRACI_AVAILABLE = True
except ImportError:
    TRACI_AVAILABLE = False
    logging.warning("TraCI not available - visualization will be limited")
    
    # Create mock traci module for compatibility
    class MockTraCI:
        class vehicle:
            @staticmethod
            def setColor(vehicle_id, color):
                pass
        
        class gui:
            @staticmethod
            def addLine(line_id, x1, y1, x2, y2, color=None, width=1.0):
                pass
            
            @staticmethod
            def removeLine(line_id):
                pass
            
            @staticmethod
            def addPolygon(polygon_id, shape, color=None, fill=True, layer=0):
                pass
            
            @staticmethod
            def removePolygon(polygon_id):
                pass
    
    traci = MockTraCI()

from .clustering import Vehicle, Cluster
from .cluster_manager import ClusterState, ClusterManager
from .custom_vanet_appl import CustomVANETApplication

class VisualizationMode(Enum):
    CLUSTER_COLORS = "cluster_colors"
    HEAD_HIGHLIGHTING = "head_highlighting"
    MEMBERSHIP_LINES = "membership_lines"
    STATE_INDICATORS = "state_indicators"
    PERFORMANCE_METRICS = "performance_metrics"

@dataclass
class VisualizationConfig:
    """Configuration for visualization settings"""
    show_cluster_colors: bool = True
    show_head_highlighting: bool = True
    show_membership_lines: bool = True
    show_cluster_boundaries: bool = True
    show_state_indicators: bool = True
    show_performance_overlay: bool = False
    
    # Color settings
    default_vehicle_color: Tuple[int, int, int] = (255, 255, 255)  # White
    cluster_head_color: Tuple[int, int, int] = (255, 0, 0)  # Red
    unclustered_color: Tuple[int, int, int] = (128, 128, 128)  # Gray
    
    # Line settings
    membership_line_width: float = 2.0
    boundary_line_width: float = 1.5
    
    # Update intervals
    color_update_interval: float = 1.0  # seconds
    line_update_interval: float = 2.0  # seconds
    metrics_update_interval: float = 5.0  # seconds

class ClusterVisualizer:
    """Main visualization manager for VANET clustering"""
    
    def __init__(self, vanet_app: CustomVANETApplication, config: VisualizationConfig = None):
        self.vanet_app = vanet_app
        self.config = config or VisualizationConfig()
        self.logger = logging.getLogger(__name__)
        
        # Visualization state
        self.cluster_colors: Dict[str, Tuple[int, int, int]] = {}
        self.last_color_update = 0.0
        self.last_line_update = 0.0
        self.last_metrics_update = 0.0
        
        # Visual elements tracking
        self.active_lines: Set[str] = set()
        self.active_polygons: Set[str] = set()
        self.gui_elements: Dict[str, str] = {}  # element_id -> element_type
        
        # Performance tracking for visualization
        self.visualization_stats = {
            'updates_performed': 0,
            'elements_created': 0,
            'elements_removed': 0,
            'last_update_time': 0.0
        }
        
        if not TRACI_AVAILABLE:
            self.logger.warning("TraCI not available - using simulation mode")
    
    def update_visualization(self, current_time: float):
        """Update all visualization elements"""
        start_time = time.time()
        
        if not TRACI_AVAILABLE:
            self.logger.debug("Skipping visualization update - TraCI not available")
            return
        
        try:
            # Update vehicle colors
            if self._should_update_colors(current_time):
                self._update_vehicle_colors()
                self.last_color_update = current_time
            
            # Update membership lines and boundaries
            if self._should_update_lines(current_time):
                self._update_cluster_lines()
                self._update_cluster_boundaries()
                self.last_line_update = current_time
            
            # Update performance metrics overlay
            if self._should_update_metrics(current_time):
                self._update_performance_overlay()
                self.last_metrics_update = current_time
            
            self.visualization_stats['updates_performed'] += 1
            self.visualization_stats['last_update_time'] = time.time() - start_time
            
        except Exception as e:
            self.logger.error(f"Error updating visualization: {e}")
    
    def _should_update_colors(self, current_time: float) -> bool:
        """Check if vehicle colors should be updated"""
        return (current_time - self.last_color_update) >= self.config.color_update_interval
    
    def _should_update_lines(self, current_time: float) -> bool:
        """Check if cluster lines should be updated"""
        return (current_time - self.last_line_update) >= self.config.line_update_interval
    
    def _should_update_metrics(self, current_time: float) -> bool:
        """Check if metrics overlay should be updated"""
        return (current_time - self.last_metrics_update) >= self.config.metrics_update_interval
    
    def _update_vehicle_colors(self):
        """Update vehicle colors based on cluster membership"""
        if not (self.config.show_cluster_colors or self.config.show_head_highlighting):
            return
        
        clusters = self.vanet_app.clustering_engine.clusters
        
        # Generate colors for clusters if needed
        self._generate_cluster_colors(clusters)
        
        # Update each vehicle's color
        for vehicle_id, node in self.vanet_app.vehicle_nodes.items():
            try:
                if not node.cluster_id:
                    # Unclustered vehicle
                    color = self.config.unclustered_color
                elif node.is_cluster_head and self.config.show_head_highlighting:
                    # Cluster head
                    color = self.config.cluster_head_color
                elif node.cluster_id in self.cluster_colors and self.config.show_cluster_colors:
                    # Cluster member
                    color = self.cluster_colors[node.cluster_id]
                else:
                    # Default color
                    color = self.config.default_vehicle_color
                
                # Apply color to vehicle in SUMO
                traci.vehicle.setColor(vehicle_id, color)
                
            except Exception as e:
                self.logger.debug(f"Could not set color for vehicle {vehicle_id}: {e}")
    
    def _generate_cluster_colors(self, clusters: Dict[str, Cluster]):
        """Generate unique colors for each cluster"""
        existing_clusters = set(self.cluster_colors.keys())
        new_clusters = set(clusters.keys()) - existing_clusters
        removed_clusters = existing_clusters - set(clusters.keys())
        
        # Remove colors for dissolved clusters
        for cluster_id in removed_clusters:
            del self.cluster_colors[cluster_id]
        
        # Generate colors for new clusters
        if new_clusters:
            self._assign_cluster_colors(list(new_clusters))
    
    def _assign_cluster_colors(self, cluster_ids: List[str]):
        """Assign unique colors to cluster IDs"""
        num_colors = len(cluster_ids)
        
        for i, cluster_id in enumerate(cluster_ids):
            # Generate distinct colors using HSV color space
            hue = i / max(num_colors, 1)  # Spread hues evenly
            saturation = 0.8
            value = 0.9
            
            # Convert HSV to RGB
            rgb = colorsys.hsv_to_rgb(hue, saturation, value)
            color = tuple(int(c * 255) for c in rgb)
            
            self.cluster_colors[cluster_id] = color
    
    def _update_cluster_lines(self):
        """Update lines connecting cluster members to heads"""
        if not self.config.show_membership_lines:
            return
        
        # Remove old lines
        self._clear_membership_lines()
        
        clusters = self.vanet_app.clustering_engine.clusters
        
        for cluster_id, cluster in clusters.items():
            if cluster.head_id not in self.vanet_app.vehicle_nodes:
                continue
            
            head_node = self.vanet_app.vehicle_nodes[cluster.head_id]
            head_pos = head_node.location
            cluster_color = self.cluster_colors.get(cluster_id, (255, 255, 255))
            
            # Draw lines from head to each member
            for member_id in cluster.member_ids:
                if member_id not in self.vanet_app.vehicle_nodes:
                    continue
                
                member_node = self.vanet_app.vehicle_nodes[member_id]
                member_pos = member_node.location
                
                line_id = f"cluster_line_{cluster_id}_{member_id}"
                
                try:
                    # Create line in SUMO GUI
                    traci.gui.addLine(
                        line_id,
                        head_pos[0], head_pos[1],
                        member_pos[0], member_pos[1],
                        color=cluster_color,
                        width=self.config.membership_line_width
                    )
                    self.active_lines.add(line_id)
                    
                except Exception as e:
                    self.logger.debug(f"Could not create line {line_id}: {e}")
    
    def _update_cluster_boundaries(self):
        """Update cluster boundary visualization"""
        if not self.config.show_cluster_boundaries:
            return
        
        # Remove old boundaries
        self._clear_cluster_boundaries()
        
        clusters = self.vanet_app.clustering_engine.clusters
        
        for cluster_id, cluster in clusters.items():
            cluster_vehicles = []
            
            # Collect cluster vehicle positions
            if cluster.head_id in self.vanet_app.vehicle_nodes:
                head_node = self.vanet_app.vehicle_nodes[cluster.head_id]
                cluster_vehicles.append(head_node.location)
            
            for member_id in cluster.member_ids:
                if member_id in self.vanet_app.vehicle_nodes:
                    member_node = self.vanet_app.vehicle_nodes[member_id]
                    cluster_vehicles.append(member_node.location)
            
            if len(cluster_vehicles) >= 3:
                # Create convex hull boundary
                boundary_points = self._calculate_convex_hull(cluster_vehicles)
                self._draw_cluster_boundary(cluster_id, boundary_points)
    
    def _calculate_convex_hull(self, points: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
        """Calculate convex hull of points (simplified implementation)"""
        if len(points) < 3:
            return points
        
        # Simple convex hull using gift wrapping algorithm
        def orientation(p, q, r):
            val = (q[1] - p[1]) * (r[0] - q[0]) - (q[0] - p[0]) * (r[1] - q[1])
            if val == 0:
                return 0  # Collinear
            return 1 if val > 0 else 2  # Clockwise or Counterclockwise
        
        n = len(points)
        if n < 3:
            return points
        
        # Find the leftmost point
        leftmost = 0
        for i in range(1, n):
            if points[i][0] < points[leftmost][0]:
                leftmost = i
            elif points[i][0] == points[leftmost][0] and points[i][1] < points[leftmost][1]:
                leftmost = i
        
        hull = []
        p = leftmost
        
        while True:
            hull.append(points[p])
            q = (p + 1) % n
            
            for i in range(n):
                if orientation(points[p], points[i], points[q]) == 2:
                    q = i
            
            p = q
            if p == leftmost:
                break
        
        return hull
    
    def _draw_cluster_boundary(self, cluster_id: str, boundary_points: List[Tuple[float, float]]):
        """Draw cluster boundary polygon"""
        if len(boundary_points) < 3:
            return
        
        polygon_id = f"cluster_boundary_{cluster_id}"
        cluster_color = self.cluster_colors.get(cluster_id, (255, 255, 255))
        
        # Create semi-transparent color for boundary
        boundary_color = (*cluster_color, 50)  # RGBA with low alpha
        
        try:
            # Create polygon in SUMO GUI
            shape = []
            for point in boundary_points:
                shape.extend([point[0], point[1]])
            
            traci.gui.addPolygon(
                polygon_id,
                shape,
                color=boundary_color,
                fill=True,
                layer=0
            )
            self.active_polygons.add(polygon_id)
            
        except Exception as e:
            self.logger.debug(f"Could not create boundary polygon {polygon_id}: {e}")
    
    def _update_performance_overlay(self):
        """Update performance metrics overlay"""
        if not self.config.show_performance_overlay:
            return
        
        try:
            stats = self.vanet_app.get_application_statistics()
            
            # Create performance text overlay
            overlay_text = self._format_performance_text(stats)
            
            # Display in SUMO GUI (if supported)
            # This is a placeholder - actual implementation would depend on SUMO GUI capabilities
            self.logger.debug(f"Performance overlay: {overlay_text}")
            
        except Exception as e:
            self.logger.debug(f"Could not update performance overlay: {e}")
    
    def _format_performance_text(self, stats: Dict) -> str:
        """Format performance statistics for display"""
        app_stats = stats.get('application', {})
        cluster_stats = stats.get('clustering', {})
        
        text_lines = [
            f"Vehicles: {app_stats.get('total_vehicles', 0)}",
            f"Clusters: {cluster_stats.get('total_clusters', 0)}",
            f"Clustered: {cluster_stats.get('total_clustered_vehicles', 0)}",
            f"Avg Size: {cluster_stats.get('avg_cluster_size', 0):.1f}",
            f"Messages: {app_stats.get('messages_sent', 0)}"
        ]
        
        return " | ".join(text_lines)
    
    def _clear_membership_lines(self):
        """Remove all membership lines"""
        for line_id in list(self.active_lines):
            try:
                traci.gui.removeLine(line_id)
                self.visualization_stats['elements_removed'] += 1
            except:
                pass
        self.active_lines.clear()
    
    def _clear_cluster_boundaries(self):
        """Remove all cluster boundary polygons"""
        for polygon_id in list(self.active_polygons):
            try:
                traci.gui.removePolygon(polygon_id)
                self.visualization_stats['elements_removed'] += 1
            except:
                pass
        self.active_polygons.clear()
    
    def set_visualization_mode(self, mode: VisualizationMode, enabled: bool = True):
        """Enable or disable specific visualization modes"""
        if mode == VisualizationMode.CLUSTER_COLORS:
            self.config.show_cluster_colors = enabled
        elif mode == VisualizationMode.HEAD_HIGHLIGHTING:
            self.config.show_head_highlighting = enabled
        elif mode == VisualizationMode.MEMBERSHIP_LINES:
            self.config.show_membership_lines = enabled
            if not enabled:
                self._clear_membership_lines()
        elif mode == VisualizationMode.STATE_INDICATORS:
            self.config.show_state_indicators = enabled
        elif mode == VisualizationMode.PERFORMANCE_METRICS:
            self.config.show_performance_overlay = enabled
        
        self.logger.info(f"Visualization mode {mode.value} {'enabled' if enabled else 'disabled'}")
    
    def highlight_cluster(self, cluster_id: str, duration: float = 5.0):
        """Temporarily highlight a specific cluster"""
        if cluster_id not in self.cluster_colors:
            return
        
        # Store original color
        original_color = self.cluster_colors[cluster_id]
        
        # Set highlight color (bright yellow)
        highlight_color = (255, 255, 0)
        self.cluster_colors[cluster_id] = highlight_color
        
        # Force immediate color update
        self._update_vehicle_colors()
        
        # Schedule color restoration (in a real implementation, this would be handled by a timer)
        # For now, we'll just log the action
        self.logger.info(f"Highlighted cluster {cluster_id} for {duration} seconds")
    
    def create_cluster_animation(self, cluster_id: str, animation_type: str = "formation"):
        """Create animation for cluster events"""
        if not TRACI_AVAILABLE:
            return
        
        cluster = self.vanet_app.clustering_engine.clusters.get(cluster_id)
        if not cluster:
            return
        
        if animation_type == "formation":
            self._animate_cluster_formation(cluster)
        elif animation_type == "merge":
            self._animate_cluster_merge(cluster)
        elif animation_type == "split":
            self._animate_cluster_split(cluster)
    
    def _animate_cluster_formation(self, cluster: Cluster):
        """Animate cluster formation process"""
        # Create expanding circle animation around cluster centroid
        animation_id = f"formation_animation_{cluster.id}"
        
        try:
            # Create series of expanding circles
            for radius in range(50, 300, 50):
                circle_id = f"{animation_id}_radius_{radius}"
                # This would create a circle in SUMO GUI
                # Implementation depends on SUMO GUI capabilities
                self.logger.debug(f"Animation frame: {circle_id}")
                
        except Exception as e:
            self.logger.debug(f"Could not create formation animation: {e}")
    
    def _animate_cluster_merge(self, cluster: Cluster):
        """Animate cluster merge process"""
        self.logger.debug(f"Animating cluster merge for {cluster.id}")
        # Implementation would show merging animation
    
    def _animate_cluster_split(self, cluster: Cluster):
        """Animate cluster split process"""
        self.logger.debug(f"Animating cluster split for {cluster.id}")
        # Implementation would show splitting animation
    
    def export_visualization_data(self, filename: str):
        """Export visualization state for external analysis"""
        visualization_data = {
            'timestamp': time.time(),
            'cluster_colors': self.cluster_colors,
            'active_lines': list(self.active_lines),
            'active_polygons': list(self.active_polygons),
            'statistics': self.visualization_stats,
            'config': {
                'show_cluster_colors': self.config.show_cluster_colors,
                'show_head_highlighting': self.config.show_head_highlighting,
                'show_membership_lines': self.config.show_membership_lines,
                'show_cluster_boundaries': self.config.show_cluster_boundaries
            },
            'clusters': {}
        }
        
        # Add cluster information
        for cluster_id, cluster in self.vanet_app.clustering_engine.clusters.items():
            visualization_data['clusters'][cluster_id] = {
                'head_id': cluster.head_id,
                'member_count': cluster.size(),
                'centroid': (cluster.centroid_x, cluster.centroid_y),
                'color': self.cluster_colors.get(cluster_id, (255, 255, 255))
            }
        
        try:
            import json
            with open(filename, 'w') as f:
                json.dump(visualization_data, f, indent=2)
            self.logger.info(f"Visualization data exported to {filename}")
        except Exception as e:
            self.logger.error(f"Could not export visualization data: {e}")
    
    def cleanup(self):
        """Clean up all visualization elements"""
        self._clear_membership_lines()
        self._clear_cluster_boundaries()
        
        # Reset vehicle colors to default
        if TRACI_AVAILABLE:
            for vehicle_id in self.vanet_app.vehicle_nodes.keys():
                try:
                    traci.vehicle.setColor(vehicle_id, self.config.default_vehicle_color)
                except:
                    pass
        
        self.logger.info("Visualization cleanup completed")
    
    def get_visualization_statistics(self) -> Dict:
        """Get visualization performance statistics"""
        return {
            'visualization_stats': self.visualization_stats,
            'active_elements': {
                'lines': len(self.active_lines),
                'polygons': len(self.active_polygons),
                'cluster_colors': len(self.cluster_colors)
            },
            'configuration': {
                'cluster_colors_enabled': self.config.show_cluster_colors,
                'head_highlighting_enabled': self.config.show_head_highlighting,
                'membership_lines_enabled': self.config.show_membership_lines,
                'cluster_boundaries_enabled': self.config.show_cluster_boundaries,
                'performance_overlay_enabled': self.config.show_performance_overlay
            },
            'update_intervals': {
                'color_update_interval': self.config.color_update_interval,
                'line_update_interval': self.config.line_update_interval,
                'metrics_update_interval': self.config.metrics_update_interval
            }
        }

# Utility functions for external scripts
def create_visualization_script(output_file: str = "clustering_visualization.py"):
    """Create a standalone visualization script for SUMO"""
    script_content = '''"""
Standalone VANET Clustering Visualization Script for SUMO

Run this script to visualize clustering in SUMO simulation.
Usage: python clustering_visualization.py
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.custom_vanet_appl import CustomVANETApplication
from src.clustering_visualization import ClusterVisualizer, VisualizationConfig
import traci
import time

def main():
    # Initialize SUMO connection
    traci.start(["sumo-gui", "-c", "simulations/config.sumo.cfg"])
    
    # Create VANET application
    vanet_app = CustomVANETApplication()
    vanet_app.initialize()
    
    # Create visualizer
    config = VisualizationConfig()
    visualizer = ClusterVisualizer(vanet_app, config)
    
    # Main simulation loop
    step = 0
    while traci.simulation.getMinExpectedNumber() > 0:
        traci.simulationStep()
        
        # Update application
        current_time = traci.simulation.getTime()
        vanet_app.handle_timeStep(current_time)
        
        # Update visualization
        visualizer.update_visualization(current_time)
        
        step += 1
        if step % 100 == 0:
            print(f"Simulation step: {step}, Time: {current_time:.2f}s")
    
    # Cleanup
    visualizer.cleanup()
    traci.close()

if __name__ == "__main__":
    main()
'''
    
    try:
        with open(output_file, 'w') as f:
            f.write(script_content)
        print(f"Visualization script created: {output_file}")
    except Exception as e:
        print(f"Error creating visualization script: {e}")

if __name__ == "__main__":
    # Create standalone visualization script when module is run directly
    create_visualization_script()