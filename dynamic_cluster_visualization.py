"""
Dynamic Cluster Visualization with Animation

This module creates animated visualizations showing:
- Real-time vehicle movements
- Dynamic cluster formation/dissolution
- Vehicles joining/leaving clusters
- Trust score changes over time
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.patches import Circle, FancyBboxPatch
from matplotlib.collections import LineCollection
import json
import argparse
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import time

# Try to import the VANET modules
try:
    from src.clustering import ClusteringAlgorithm
    from src.custom_vanet_appl import CustomVANETApplication
except ImportError:
    print("Warning: Could not import VANET modules. Using standalone mode.")


@dataclass
class VehicleSnapshot:
    """Snapshot of vehicle state at a point in time"""
    vehicle_id: str
    x: float
    y: float
    speed: float
    direction: float
    cluster_id: Optional[str]
    is_cluster_head: bool
    trust_score: float
    timestamp: float


@dataclass
class ClusterSnapshot:
    """Snapshot of cluster state at a point in time"""
    cluster_id: str
    head_id: str
    member_ids: List[str]
    center: Tuple[float, float]
    timestamp: float


class DynamicClusterVisualizer:
    """
    Creates animated visualizations of VANET clustering
    """
    
    def __init__(self, figsize=(16, 10)):
        self.figsize = figsize
        self.snapshots: List[Dict] = []
        self.colors = plt.cm.tab10(np.linspace(0, 1, 10))
        
    def add_snapshot(self, vehicles: List[VehicleSnapshot], 
                    clusters: List[ClusterSnapshot],
                    timestamp: float):
        """Add a snapshot of the current state"""
        self.snapshots.append({
            'timestamp': timestamp,
            'vehicles': vehicles,
            'clusters': clusters
        })
    
    def create_animation(self, output_file='dynamic_clustering.mp4', 
                        interval=200, fps=10):
        """
        Create animated video of cluster evolution
        
        Args:
            output_file: Output filename (.mp4, .gif, or .html)
            interval: Delay between frames in milliseconds
            fps: Frames per second for video output
        """
        if not self.snapshots:
            print("No snapshots to animate!")
            return
        
        # Create figure with subplots
        fig = plt.figure(figsize=self.figsize)
        gs = fig.add_gridspec(2, 2, hspace=0.3, wspace=0.3)
        
        ax_main = fig.add_subplot(gs[:, 0])  # Main topology view
        ax_trust = fig.add_subplot(gs[0, 1])  # Trust scores over time
        ax_clusters = fig.add_subplot(gs[1, 1])  # Cluster count over time
        
        # Initialize plots
        self._setup_axes(ax_main, ax_trust, ax_clusters)
        
        # Animation data
        trust_history = {v.vehicle_id: [] for v in self.snapshots[0]['vehicles']}
        cluster_counts = []
        
        def animate(frame_idx):
            """Animation function called for each frame"""
            snapshot = self.snapshots[frame_idx]
            timestamp = snapshot['timestamp']
            vehicles = snapshot['vehicles']
            clusters = snapshot['clusters']
            
            # Clear main axis
            ax_main.clear()
            self._setup_main_axis(ax_main)
            
            # Draw clusters (as shaded regions)
            cluster_colors = {}
            for idx, cluster in enumerate(clusters):
                color = self.colors[idx % len(self.colors)]
                cluster_colors[cluster.cluster_id] = color
                
                # Draw cluster members' convex hull
                member_positions = [(v.x, v.y) for v in vehicles 
                                  if v.cluster_id == cluster.cluster_id]
                if len(member_positions) >= 3:
                    self._draw_cluster_hull(ax_main, member_positions, color, 
                                          cluster.cluster_id)
            
            # Draw vehicles
            for vehicle in vehicles:
                color = cluster_colors.get(vehicle.cluster_id, 'gray')
                self._draw_vehicle(ax_main, vehicle, color)
            
            # Draw connections (edges between cluster members)
            self._draw_connections(ax_main, vehicles, clusters, cluster_colors)
            
            # Update title with current time
            ax_main.set_title(f'Dynamic Cluster Topology (t={timestamp:.1f}s)', 
                            fontsize=14, fontweight='bold')
            
            # Update trust score plot
            for vehicle in vehicles:
                if vehicle.vehicle_id in trust_history:
                    trust_history[vehicle.vehicle_id].append(
                        (timestamp, vehicle.trust_score)
                    )
            
            ax_trust.clear()
            self._plot_trust_history(ax_trust, trust_history, timestamp)
            
            # Update cluster count plot
            cluster_counts.append((timestamp, len(clusters)))
            ax_clusters.clear()
            self._plot_cluster_count(ax_clusters, cluster_counts)
            
            return ax_main, ax_trust, ax_clusters
        
        # Create animation
        anim = animation.FuncAnimation(
            fig, animate, frames=len(self.snapshots),
            interval=interval, blit=False, repeat=True
        )
        
        # Save animation
        if output_file.endswith('.mp4'):
            print(f"Saving animation as MP4: {output_file}")
            Writer = animation.writers['ffmpeg']
            writer = Writer(fps=fps, metadata=dict(artist='VANET Simulator'), 
                          bitrate=1800)
            anim.save(output_file, writer=writer)
            print(f"✓ Saved to {output_file}")
            
        elif output_file.endswith('.gif'):
            print(f"Saving animation as GIF: {output_file}")
            anim.save(output_file, writer='pillow', fps=fps)
            print(f"✓ Saved to {output_file}")
            
        elif output_file.endswith('.html'):
            print(f"Saving animation as HTML: {output_file}")
            from matplotlib.animation import HTMLWriter
            anim.save(output_file, writer=HTMLWriter(fps=fps))
            print(f"✓ Saved to {output_file}")
        else:
            print(f"Unsupported format: {output_file}")
            print("Supported formats: .mp4, .gif, .html")
        
        plt.close()
        return anim
    
    def create_interactive_plot(self, output_file='interactive_clustering.html'):
        """
        Create interactive HTML visualization using Plotly
        """
        try:
            import plotly.graph_objects as go
            from plotly.subplots import make_subplots
        except ImportError:
            print("Plotly not installed. Install with: pip3 install plotly")
            return
        
        if not self.snapshots:
            print("No snapshots to visualize!")
            return
        
        # Create frames for each snapshot
        frames = []
        
        for snapshot in self.snapshots:
            timestamp = snapshot['timestamp']
            vehicles = snapshot['vehicles']
            clusters = snapshot['clusters']
            
            # Prepare vehicle data
            vehicle_data = {
                'x': [], 'y': [], 'ids': [], 'clusters': [], 
                'trust': [], 'is_head': [], 'colors': []
            }
            
            cluster_colors = {}
            for idx, cluster in enumerate(clusters):
                cluster_colors[cluster.cluster_id] = idx
            
            for vehicle in vehicles:
                vehicle_data['x'].append(vehicle.x)
                vehicle_data['y'].append(vehicle.y)
                vehicle_data['ids'].append(vehicle.vehicle_id)
                vehicle_data['clusters'].append(vehicle.cluster_id or 'None')
                vehicle_data['trust'].append(vehicle.trust_score)
                vehicle_data['is_head'].append(vehicle.is_cluster_head)
                
                # Color based on cluster
                if vehicle.cluster_id:
                    color_idx = cluster_colors[vehicle.cluster_id]
                    vehicle_data['colors'].append(color_idx)
                else:
                    vehicle_data['colors'].append(-1)
            
            # Create scatter trace
            trace = go.Scatter(
                x=vehicle_data['x'],
                y=vehicle_data['y'],
                mode='markers+text',
                marker=dict(
                    size=[15 if h else 10 for h in vehicle_data['is_head']],
                    color=vehicle_data['colors'],
                    colorscale='Viridis',
                    symbol=['diamond' if h else 'circle' 
                           for h in vehicle_data['is_head']],
                    line=dict(width=2, color='white')
                ),
                text=vehicle_data['ids'],
                textposition='top center',
                hovertemplate=(
                    '<b>%{text}</b><br>'
                    'Position: (%{x:.1f}, %{y:.1f})<br>'
                    'Cluster: %{customdata[0]}<br>'
                    'Trust: %{customdata[1]:.3f}<br>'
                    '<extra></extra>'
                ),
                customdata=list(zip(vehicle_data['clusters'], 
                                  vehicle_data['trust']))
            )
            
            frames.append(go.Frame(
                data=[trace],
                name=f't={timestamp:.1f}',
                layout=go.Layout(title_text=f'Time: {timestamp:.1f}s')
            ))
        
        # Create initial figure
        fig = go.Figure(
            data=frames[0].data,
            layout=go.Layout(
                title='Interactive Dynamic Cluster Visualization',
                xaxis=dict(title='X Position (m)', range=[0, 2000]),
                yaxis=dict(title='Y Position (m)', range=[0, 1000]),
                hovermode='closest',
                updatemenus=[dict(
                    type='buttons',
                    showactive=False,
                    buttons=[
                        dict(label='Play',
                             method='animate',
                             args=[None, dict(frame=dict(duration=200, redraw=True),
                                            fromcurrent=True)]),
                        dict(label='Pause',
                             method='animate',
                             args=[[None], dict(frame=dict(duration=0, redraw=False),
                                              mode='immediate')])
                    ],
                    x=0.1, y=0, xanchor='left', yanchor='bottom'
                )],
                sliders=[dict(
                    steps=[dict(
                        method='animate',
                        args=[[f't={s["timestamp"]:.1f}'],
                              dict(mode='immediate', frame=dict(duration=200))],
                        label=f'{s["timestamp"]:.1f}s'
                    ) for s in self.snapshots],
                    x=0.1, y=0, len=0.9, xanchor='left', yanchor='top'
                )]
            ),
            frames=frames
        )
        
        fig.write_html(output_file)
        print(f"✓ Interactive visualization saved to {output_file}")
        print(f"  Open in browser to view animation with play/pause controls")
    
    def _setup_axes(self, ax_main, ax_trust, ax_clusters):
        """Setup initial axes"""
        self._setup_main_axis(ax_main)
        ax_trust.set_title('Trust Scores Over Time', fontweight='bold')
        ax_trust.set_xlabel('Time (s)')
        ax_trust.set_ylabel('Trust Score')
        ax_trust.grid(True, alpha=0.3)
        
        ax_clusters.set_title('Cluster Count Over Time', fontweight='bold')
        ax_clusters.set_xlabel('Time (s)')
        ax_clusters.set_ylabel('Number of Clusters')
        ax_clusters.grid(True, alpha=0.3)
    
    def _setup_main_axis(self, ax):
        """Setup main topology axis"""
        ax.set_xlim(0, 2000)
        ax.set_ylim(0, 1000)
        ax.set_xlabel('X Position (m)', fontsize=11)
        ax.set_ylabel('Y Position (m)', fontsize=11)
        ax.grid(True, alpha=0.3, linestyle='--')
        ax.set_aspect('equal')
    
    def _draw_cluster_hull(self, ax, positions, color, cluster_id):
        """Draw convex hull around cluster members"""
        from scipy.spatial import ConvexHull
        
        if len(positions) < 3:
            return
        
        try:
            points = np.array(positions)
            hull = ConvexHull(points)
            
            # Draw filled polygon
            for simplex in hull.simplices:
                ax.fill(points[simplex, 0], points[simplex, 1], 
                       alpha=0.2, color=color, zorder=1)
            
            # Draw hull outline
            ax.plot(points[hull.vertices, 0], points[hull.vertices, 1], 
                   'o-', color=color, alpha=0.5, linewidth=2, zorder=2)
            
            # Add cluster label
            center = points.mean(axis=0)
            ax.text(center[0], center[1], cluster_id, 
                   fontsize=12, fontweight='bold', 
                   ha='center', va='center',
                   bbox=dict(boxstyle='round', facecolor=color, alpha=0.3),
                   zorder=3)
        except Exception as e:
            pass  # Skip if convex hull fails
    
    def _draw_vehicle(self, ax, vehicle, color):
        """Draw vehicle marker"""
        marker = 'D' if vehicle.is_cluster_head else 'o'
        size = 150 if vehicle.is_cluster_head else 80
        edge_color = 'black' if vehicle.is_cluster_head else 'white'
        edge_width = 2 if vehicle.is_cluster_head else 1
        
        # Color based on trust score
        trust_color = plt.cm.RdYlGn(vehicle.trust_score)
        
        ax.scatter(vehicle.x, vehicle.y, c=[trust_color], 
                  marker=marker, s=size, edgecolors=edge_color,
                  linewidths=edge_width, zorder=4, alpha=0.9)
        
        # Add vehicle ID
        ax.text(vehicle.x, vehicle.y + 30, vehicle.vehicle_id[:3],
               fontsize=8, ha='center', va='bottom', zorder=5)
    
    def _draw_connections(self, ax, vehicles, clusters, cluster_colors):
        """Draw connections between cluster members"""
        for cluster in clusters:
            members = [v for v in vehicles if v.cluster_id == cluster.cluster_id]
            if len(members) < 2:
                continue
            
            color = cluster_colors.get(cluster.cluster_id, 'gray')
            
            # Draw lines from head to all members
            head = next((v for v in members if v.is_cluster_head), None)
            if head:
                for member in members:
                    if member.vehicle_id != head.vehicle_id:
                        ax.plot([head.x, member.x], [head.y, member.y],
                               color=color, alpha=0.3, linewidth=1, 
                               linestyle='--', zorder=2)
    
    def _plot_trust_history(self, ax, trust_history, current_time):
        """Plot trust score evolution"""
        for vehicle_id, history in trust_history.items():
            if history:
                times, scores = zip(*history)
                ax.plot(times, scores, label=vehicle_id[:5], alpha=0.7)
        
        ax.axvline(current_time, color='red', linestyle='--', 
                  alpha=0.5, label='Current Time')
        ax.set_xlim(0, max(current_time + 1, 10))
        ax.set_ylim(0, 1)
        ax.legend(loc='center left', bbox_to_anchor=(1, 0.5), fontsize=8)
    
    def _plot_cluster_count(self, ax, cluster_counts):
        """Plot cluster count evolution"""
        if cluster_counts:
            times, counts = zip(*cluster_counts)
            ax.plot(times, counts, marker='o', linewidth=2, markersize=4)
            ax.set_xlim(0, max(times) + 1)
            ax.set_ylim(0, max(counts) + 1)


def run_simulation_with_animation(algorithm=ClusteringAlgorithm.MOBILITY_BASED,
                                  duration=20, num_vehicles=20,
                                  trust_enabled=True):
    """
    Run a VANET simulation and create animated visualization
    """
    print("=" * 80)
    print("Dynamic Cluster Visualization Demo")
    print("=" * 80)
    
    # Create application
    app = CustomVANETApplication(algorithm)
    app.trust_enabled = trust_enabled
    
    # Add vehicles
    print(f"\nInitializing {num_vehicles} vehicles...")
    np.random.seed(42)
    for i in range(num_vehicles):
        x = np.random.uniform(100, 1900)
        y = np.random.uniform(100, 900)
        speed = np.random.uniform(15, 35)
        direction = np.random.uniform(0, 360)
        
        app.add_vehicle(
            f'v{i}',
            x=x, y=y,
            speed=speed,
            direction=direction,
            lane_id=f'lane_{i%4}'
        )
    
    # Create visualizer
    visualizer = DynamicClusterVisualizer()
    
    # Run simulation and collect snapshots
    print(f"Running simulation for {duration}s...")
    timestep = 0.5
    num_steps = int(duration / timestep)
    
    for step in range(num_steps):
        current_time = step * timestep
        app.handle_timeStep(current_time)
        
        # Collect snapshot every 0.5 seconds
        vehicles_snapshot = []
        for node in app.vehicle_nodes.values():
            vehicles_snapshot.append(VehicleSnapshot(
                vehicle_id=node.vehicle_id,
                x=node.location[0],
                y=node.location[1],
                speed=node.speed,
                direction=node.direction,
                cluster_id=node.cluster_id,
                is_cluster_head=node.is_cluster_head,
                trust_score=node.trust_score,
                timestamp=current_time
            ))
        
        clusters_snapshot = []
        for cluster in app.clustering_engine.clusters.values():
            clusters_snapshot.append(ClusterSnapshot(
                cluster_id=cluster.id,
                head_id=cluster.head_id,
                member_ids=list(cluster.member_ids),
                center=(0, 0),  # Could calculate center
                timestamp=current_time
            ))
        
        visualizer.add_snapshot(vehicles_snapshot, clusters_snapshot, current_time)
        
        if step % 10 == 0:
            print(f"  Progress: {step}/{num_steps} steps ({current_time:.1f}s)")
    
    print(f"\n✓ Simulation complete!")
    print(f"  Total snapshots: {len(visualizer.snapshots)}")
    print(f"  Final cluster count: {len(app.clustering_engine.clusters)}")
    
    return visualizer, app


def main():
    parser = argparse.ArgumentParser(description='Dynamic VANET Cluster Visualization')
    parser.add_argument('--algorithm', type=str, default='mobility_based',
                       choices=['mobility_based', 'direction_based', 'kmeans', 'dbscan'],
                       help='Clustering algorithm to use')
    parser.add_argument('--duration', type=float, default=20,
                       help='Simulation duration in seconds')
    parser.add_argument('--vehicles', type=int, default=20,
                       help='Number of vehicles')
    parser.add_argument('--output', type=str, default='dynamic_clustering',
                       help='Output filename (without extension)')
    parser.add_argument('--format', type=str, default='html',
                       choices=['mp4', 'gif', 'html'],
                       help='Output format')
    parser.add_argument('--fps', type=int, default=10,
                       help='Frames per second for video')
    
    args = parser.parse_args()
    
    # Map algorithm name
    algo_map = {
        'mobility_based': ClusteringAlgorithm.MOBILITY_BASED,
        'direction_based': ClusteringAlgorithm.DIRECTION_BASED,
        'kmeans': ClusteringAlgorithm.KMEANS,
        'dbscan': ClusteringAlgorithm.DBSCAN
    }
    
    # Run simulation
    visualizer, app = run_simulation_with_animation(
        algorithm=algo_map[args.algorithm],
        duration=args.duration,
        num_vehicles=args.vehicles
    )
    
    # Create visualizations
    output_file = f"{args.output}.{args.format}"
    
    print("\n" + "=" * 80)
    print("Creating Visualizations")
    print("=" * 80)
    
    if args.format == 'html':
        visualizer.create_interactive_plot(output_file)
    else:
        visualizer.create_animation(output_file, fps=args.fps)
    
    print("\n✓ All visualizations created successfully!")


if __name__ == '__main__':
    main()
