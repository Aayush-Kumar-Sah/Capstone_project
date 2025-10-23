#!/usr/bin/env python3
"""
Enhanced VANET Cluster Formation Visualization Demo

This script provides comprehensive visualization of:
- Real-time cluster formation and changes
- Trust scores overlay on clusters
- Cluster head changes over time
- Network topology and connectivity
- Performance metrics dashboard

Usage:
    python3 cluster_visualization_demo.py [options]
    
Options:
    --duration SECONDS    Simulation duration (default: 60)
    --algorithm ALGO      Clustering algorithm (default: mobility_based)
    --vehicles NUM        Number of vehicles (default: 45)
    --animate            Enable real-time animation
    --save-plots         Save plots to files
"""

import sys
import os
import time
import argparse
import logging
from typing import Dict, List, Tuple, Optional
from collections import defaultdict, deque
import json

# Add src to path
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import matplotlib
matplotlib.use('Agg')  # Use Agg backend for non-interactive (file output) plots
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.animation import FuncAnimation
from matplotlib.collections import LineCollection
import numpy as np

from src.custom_vanet_appl import CustomVANETApplication
from src.clustering import ClusteringAlgorithm, Vehicle
from src.consensus_engine import ConsensusEngine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ClusterVisualizationDemo:
    """Enhanced cluster visualization with real-time and post-analysis plots"""
    
    def __init__(self, algorithm: ClusteringAlgorithm, duration: float = 60.0, 
                 num_vehicles: int = 45, animate: bool = False):
        self.algorithm = algorithm
        self.duration = duration
        self.num_vehicles = num_vehicles
        self.animate_mode = animate
        
        # Initialize VANET application with trust
        self.app = CustomVANETApplication(algorithm)
        self.app.initialize_consensus("main_node", "hybrid", 
                                     ["authority_001", "authority_002", "authority_003"])
        
        # Simulation state
        self.current_time = 0.0
        self.time_step = 0.1
        self.frame_count = 0
        
        # Data collection for visualization
        self.history = {
            'timestamps': [],
            'cluster_counts': [],
            'vehicle_positions': [],  # List of dicts: {vehicle_id: (x, y)}
            'cluster_assignments': [],  # List of dicts: {vehicle_id: cluster_id}
            'cluster_heads': [],  # List of sets: {head_vehicle_ids}
            'trust_scores': [],  # List of dicts: {vehicle_id: trust_score}
            'cluster_events': [],  # List of (time, event_type, cluster_id)
            'head_changes': [],  # List of (time, cluster_id, old_head, new_head)
        }
        
        # Visualization setup
        self.colors = self._generate_color_palette(30)  # Support up to 30 clusters
        self.fig = None
        self.axes = None
        
        logger.info(f"Initialized cluster visualization demo with {algorithm.name}")
    
    def _generate_color_palette(self, n_colors: int) -> List[Tuple[float, float, float]]:
        """Generate distinct colors for clusters"""
        colors = []
        for i in range(n_colors):
            hue = i / n_colors
            # Use matplotlib's HSV to RGB conversion
            rgb = matplotlib.colors.hsv_to_rgb([hue, 0.8, 0.9])
            colors.append(tuple(rgb))
        return colors
    
    def setup_simulation(self):
        """Initialize vehicles and simulation environment"""
        logger.info("Setting up simulation environment...")
        
        # Create vehicles with varied properties
        for i in range(self.num_vehicles):
            # Distribute vehicles along a road
            x = np.random.uniform(50, 1950)
            y = np.random.uniform(50, 450) if i < self.num_vehicles // 2 else np.random.uniform(550, 950)
            
            # Random speeds (highway speeds)
            speed = np.random.uniform(20, 30)  # m/s (72-108 km/h)
            direction = 0 if y < 500 else 180  # East or West direction
            
            # Determine lane
            lane = f"lane_{int(y // 100)}"
            
            vehicle_id = f"vehicle_{i:03d}"
            self.app.add_vehicle(vehicle_id, x, y, speed, direction, lane)
            
            # Assign varied trust scores
            node = self.app.vehicle_nodes[vehicle_id]
            if i % 10 == 0:
                # Some vehicles with lower trust
                node.trust_score = np.random.uniform(0.4, 0.6)
            else:
                # Most vehicles with high trust
                node.trust_score = np.random.uniform(0.75, 0.95)
            
            # Mark a few as malicious for demonstration
            if i % 15 == 0:
                node.is_malicious = True
                node.trust_score = np.random.uniform(0.1, 0.3)
        
        logger.info(f"Created {self.num_vehicles} vehicles")
        
        # Initial clustering
        self.app.handle_timeStep(0.0)
        
        # Collect initial data
        self._collect_frame_data()
    
    def run_simulation(self):
        """Run the simulation and collect data"""
        logger.info(f"Running simulation for {self.duration} seconds...")
        
        frames = int(self.duration / self.time_step)
        last_cluster_count = 0
        
        for frame in range(frames):
            self.current_time = frame * self.time_step
            
            # Update vehicle positions (simulate movement)
            self._update_vehicle_positions()
            
            # Update VANET application
            self.app.handle_timeStep(self.current_time)
            
            # Evaluate trust periodically
            if frame % 100 == 0:  # Every 10 seconds
                self._evaluate_trust()
            
            # Collect data for this frame
            self._collect_frame_data()
            
            # Detect cluster events
            current_cluster_count = len(self.app.clustering_engine.clusters)
            if current_cluster_count != last_cluster_count:
                event_type = "formation" if current_cluster_count > last_cluster_count else "dissolution"
                self.history['cluster_events'].append((self.current_time, event_type, current_cluster_count))
                last_cluster_count = current_cluster_count
            
            # Progress indicator
            if frame % 100 == 0:
                progress = (frame / frames) * 100
                logger.info(f"Progress: {progress:.1f}% - Time: {self.current_time:.1f}s - "
                          f"Clusters: {current_cluster_count}")
        
        logger.info("Simulation completed")
        logger.info(f"Total frames collected: {len(self.history['timestamps'])}")
    
    def _update_vehicle_positions(self):
        """Update vehicle positions for simulation"""
        for vehicle_id, node in self.app.vehicle_nodes.items():
            # Simple linear movement
            dx = node.speed * np.cos(np.radians(node.direction)) * self.time_step
            dy = node.speed * np.sin(np.radians(node.direction)) * self.time_step
            
            new_x = node.location[0] + dx
            new_y = node.location[1] + dy
            
            # Wrap around boundaries
            if new_x < 0:
                new_x = 2000
            elif new_x > 2000:
                new_x = 0
            
            if new_y < 0:
                new_y = 1000
            elif new_y > 1000:
                new_y = 0
            
            node.location = (new_x, new_y)
    
    def _evaluate_trust(self):
        """Evaluate trust scores for all vehicles"""
        for vehicle_id, node in self.app.vehicle_nodes.items():
            if not node.is_malicious:
                # Normal vehicles maintain or slightly improve trust
                node.trust_score = min(0.95, node.trust_score + np.random.uniform(-0.01, 0.02))
            else:
                # Malicious vehicles' trust may degrade
                node.trust_score = max(0.1, node.trust_score - np.random.uniform(0.0, 0.05))
    
    def _collect_frame_data(self):
        """Collect data for current frame"""
        # Timestamp
        self.history['timestamps'].append(self.current_time)
        
        # Cluster count
        cluster_count = len(self.app.clustering_engine.clusters)
        self.history['cluster_counts'].append(cluster_count)
        
        # Vehicle positions
        positions = {}
        for vehicle_id, node in self.app.vehicle_nodes.items():
            positions[vehicle_id] = node.location
        self.history['vehicle_positions'].append(positions)
        
        # Cluster assignments
        assignments = {}
        for vehicle_id, node in self.app.vehicle_nodes.items():
            assignments[vehicle_id] = node.cluster_id
        self.history['cluster_assignments'].append(assignments)
        
        # Cluster heads
        heads = set()
        for cluster_id, cluster in self.app.clustering_engine.clusters.items():
            if cluster.head_id:
                heads.add(cluster.head_id)
        self.history['cluster_heads'].append(heads)
        
        # Trust scores
        trust_scores = {}
        for vehicle_id, node in self.app.vehicle_nodes.items():
            trust_scores[vehicle_id] = node.trust_score
        self.history['trust_scores'].append(trust_scores)
    
    def create_visualizations(self, save_plots: bool = False):
        """Create all visualization plots"""
        logger.info("Creating visualizations...")
        
        # Create figure with subplots
        self.fig = plt.figure(figsize=(20, 12))
        self.fig.suptitle(f'VANET Cluster Formation Visualization - {self.algorithm.name}', 
                         fontsize=16, fontweight='bold')
        
        # 1. Main network topology plot (largest)
        self._plot_network_topology(save_plots)
        
        # 2. Cluster timeline
        self._plot_cluster_timeline(save_plots)
        
        # 3. Trust distribution
        self._plot_trust_distribution(save_plots)
        
        # 4. Performance metrics
        self._plot_performance_metrics(save_plots)
        
        if not save_plots:
            plt.tight_layout()
            plt.show()
        else:
            logger.info("Plots saved to files")
    
    def _plot_network_topology(self, save: bool = False):
        """Plot network topology with clusters"""
        logger.info("Plotting network topology...")
        
        # Create figure for topology
        fig_topo = plt.figure(figsize=(16, 10))
        ax = fig_topo.add_subplot(111)
        
        # Use data from middle of simulation for snapshot
        mid_frame = len(self.history['timestamps']) // 2
        
        positions = self.history['vehicle_positions'][mid_frame]
        assignments = self.history['cluster_assignments'][mid_frame]
        heads = self.history['cluster_heads'][mid_frame]
        trust_scores = self.history['trust_scores'][mid_frame]
        
        # Get unique clusters
        clusters = {}
        for vehicle_id, cluster_id in assignments.items():
            if cluster_id:
                if cluster_id not in clusters:
                    clusters[cluster_id] = []
                clusters[cluster_id].append(vehicle_id)
        
        # Plot each cluster
        cluster_ids = sorted(clusters.keys())
        for idx, cluster_id in enumerate(cluster_ids):
            color = self.colors[idx % len(self.colors)]
            members = clusters[cluster_id]
            
            # Find cluster head
            head_id = None
            for vehicle_id in members:
                if vehicle_id in heads:
                    head_id = vehicle_id
                    break
            
            # Plot cluster members
            member_x = []
            member_y = []
            for vehicle_id in members:
                if vehicle_id != head_id:
                    x, y = positions[vehicle_id]
                    member_x.append(x)
                    member_y.append(y)
                    
                    # Add trust score as text
                    trust = trust_scores.get(vehicle_id, 0.0)
                    trust_color = 'green' if trust >= 0.7 else 'orange' if trust >= 0.4 else 'red'
                    ax.text(x, y - 15, f'{trust:.2f}', fontsize=7, ha='center', 
                           color=trust_color, fontweight='bold')
            
            # Plot members
            if member_x:
                ax.scatter(member_x, member_y, c=[color], s=100, alpha=0.6, 
                          edgecolors='black', linewidth=1, label=f'Cluster {cluster_id}')
            
            # Plot cluster head
            if head_id and head_id in positions:
                head_x, head_y = positions[head_id]
                ax.scatter([head_x], [head_y], c=[color], s=300, alpha=0.9,
                          marker='*', edgecolors='red', linewidth=2)
                
                # Draw lines from head to members
                for vehicle_id in members:
                    if vehicle_id != head_id:
                        member_x, member_y = positions[vehicle_id]
                        ax.plot([head_x, member_x], [head_y, member_y], 
                               color=color, alpha=0.3, linewidth=1)
                
                # Head label
                trust = trust_scores.get(head_id, 0.0)
                ax.text(head_x, head_y + 20, f'HEAD\n{trust:.2f}', fontsize=9, 
                       ha='center', fontweight='bold', 
                       bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.7))
        
        # Plot unclustered vehicles
        unclustered = [vid for vid, cid in assignments.items() if not cid]
        if unclustered:
            unc_x = [positions[vid][0] for vid in unclustered]
            unc_y = [positions[vid][1] for vid in unclustered]
            ax.scatter(unc_x, unc_y, c='gray', s=80, alpha=0.5, 
                      marker='o', label='Unclustered')
        
        ax.set_xlim(0, 2000)
        ax.set_ylim(0, 1000)
        ax.set_xlabel('X Position (m)', fontsize=12)
        ax.set_ylabel('Y Position (m)', fontsize=12)
        ax.set_title(f'Network Topology at t={self.history["timestamps"][mid_frame]:.1f}s\n'
                    f'{len(clusters)} Clusters, {len(positions)} Vehicles', 
                    fontsize=14, fontweight='bold')
        ax.legend(loc='upper right', fontsize=8)
        ax.grid(True, alpha=0.3)
        
        # Add trust score legend
        trust_legend = ax.text(0.02, 0.98, 
                              'Trust Scores:\nGreen: ≥0.7 (Trusted)\nOrange: 0.4-0.7 (Medium)\nRed: <0.4 (Low)',
                              transform=ax.transAxes, fontsize=10,
                              verticalalignment='top',
                              bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        plt.tight_layout()
        
        if save:
            filename = f'cluster_topology_{self.algorithm.name}.png'
            fig_topo.savefig(filename, dpi=300, bbox_inches='tight')
            logger.info(f"Saved topology plot: {filename}")
            plt.close(fig_topo)
        else:
            plt.show()
    
    def _plot_cluster_timeline(self, save: bool = False):
        """Plot cluster formation timeline"""
        logger.info("Plotting cluster timeline...")
        
        fig_time = plt.figure(figsize=(14, 6))
        ax = fig_time.add_subplot(111)
        
        timestamps = self.history['timestamps']
        cluster_counts = self.history['cluster_counts']
        
        # Plot cluster count over time
        ax.plot(timestamps, cluster_counts, linewidth=2, color='blue', label='Active Clusters')
        ax.fill_between(timestamps, 0, cluster_counts, alpha=0.3, color='blue')
        
        # Mark cluster events
        for event_time, event_type, count in self.history['cluster_events']:
            color = 'green' if event_type == 'formation' else 'red'
            marker = '^' if event_type == 'formation' else 'v'
            ax.scatter([event_time], [count], c=color, s=100, marker=marker, 
                      zorder=5, edgecolors='black')
        
        ax.set_xlabel('Time (s)', fontsize=12)
        ax.set_ylabel('Number of Clusters', fontsize=12)
        ax.set_title('Cluster Formation Timeline', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.legend()
        
        # Add statistics
        avg_clusters = np.mean(cluster_counts)
        max_clusters = np.max(cluster_counts)
        min_clusters = np.min(cluster_counts)
        
        stats_text = f'Avg: {avg_clusters:.1f}\nMax: {max_clusters}\nMin: {min_clusters}'
        ax.text(0.98, 0.98, stats_text, transform=ax.transAxes,
               fontsize=10, verticalalignment='top', horizontalalignment='right',
               bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
        
        plt.tight_layout()
        
        if save:
            filename = f'cluster_timeline_{self.algorithm.name}.png'
            fig_time.savefig(filename, dpi=300, bbox_inches='tight')
            logger.info(f"Saved timeline plot: {filename}")
            plt.close(fig_time)
        else:
            plt.show()
    
    def _plot_trust_distribution(self, save: bool = False):
        """Plot trust score distribution"""
        logger.info("Plotting trust distribution...")
        
        fig_trust = plt.figure(figsize=(12, 6))
        
        # Subplot 1: Trust histogram
        ax1 = fig_trust.add_subplot(121)
        
        # Get trust scores from multiple time points
        sample_frames = [0, len(self.history['timestamps'])//4, 
                        len(self.history['timestamps'])//2,
                        3*len(self.history['timestamps'])//4,
                        len(self.history['timestamps'])-1]
        
        for frame_idx in sample_frames:
            trust_scores = list(self.history['trust_scores'][frame_idx].values())
            time_label = f't={self.history["timestamps"][frame_idx]:.0f}s'
            ax1.hist(trust_scores, bins=20, alpha=0.5, label=time_label)
        
        ax1.set_xlabel('Trust Score', fontsize=12)
        ax1.set_ylabel('Frequency', fontsize=12)
        ax1.set_title('Trust Score Distribution Over Time', fontsize=13, fontweight='bold')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Subplot 2: Trust evolution
        ax2 = fig_trust.add_subplot(122)
        
        # Plot trust evolution for sample vehicles
        sample_vehicles = list(self.app.vehicle_nodes.keys())[:10]
        timestamps = self.history['timestamps']
        
        for vehicle_id in sample_vehicles:
            trust_evolution = [frame_trust.get(vehicle_id, 0.0) 
                             for frame_trust in self.history['trust_scores']]
            ax2.plot(timestamps, trust_evolution, alpha=0.7, linewidth=1.5, 
                    label=vehicle_id[-6:])  # Show last 6 chars of ID
        
        ax2.set_xlabel('Time (s)', fontsize=12)
        ax2.set_ylabel('Trust Score', fontsize=12)
        ax2.set_title('Trust Score Evolution (Sample Vehicles)', fontsize=13, fontweight='bold')
        ax2.legend(ncol=2, fontsize=8)
        ax2.grid(True, alpha=0.3)
        ax2.set_ylim([0, 1])
        
        plt.tight_layout()
        
        if save:
            filename = f'trust_distribution_{self.algorithm.name}.png'
            fig_trust.savefig(filename, dpi=300, bbox_inches='tight')
            logger.info(f"Saved trust plot: {filename}")
            plt.close(fig_trust)
        else:
            plt.show()
    
    def _plot_performance_metrics(self, save: bool = False):
        """Plot performance metrics dashboard"""
        logger.info("Plotting performance metrics...")
        
        fig_perf = plt.figure(figsize=(14, 8))
        
        # Get statistics
        stats = self.app.get_application_statistics()
        
        # Subplot 1: Messages
        ax1 = fig_perf.add_subplot(221)
        message_types = ['Sent', 'Received', 'Dropped']
        message_counts = [
            stats['application']['messages_sent'],
            stats['application']['messages_received'],
            stats['application'].get('messages_dropped', 0)
        ]
        colors = ['green', 'blue', 'red']
        ax1.bar(message_types, message_counts, color=colors, alpha=0.7)
        ax1.set_ylabel('Count', fontsize=11)
        ax1.set_title('Message Statistics', fontsize=12, fontweight='bold')
        ax1.grid(True, alpha=0.3, axis='y')
        
        # Subplot 2: Cluster statistics
        ax2 = fig_perf.add_subplot(222)
        cluster_stats_labels = ['Formations', 'Joins', 'Leaves', 'Re-elections']
        cluster_stats_values = [
            stats['application']['clusters_formed'],
            stats['application']['cluster_joins'],
            stats['application']['cluster_leaves'],
            stats['application'].get('head_elections', 0)
        ]
        ax2.bar(cluster_stats_labels, cluster_stats_values, color='orange', alpha=0.7)
        ax2.set_ylabel('Count', fontsize=11)
        ax2.set_title('Clustering Events', fontsize=12, fontweight='bold')
        ax2.grid(True, alpha=0.3, axis='y')
        
        # Subplot 3: Cluster size distribution
        ax3 = fig_perf.add_subplot(223)
        final_frame = len(self.history['timestamps']) - 1
        assignments = self.history['cluster_assignments'][final_frame]
        
        # Count cluster sizes
        cluster_sizes = defaultdict(int)
        for vehicle_id, cluster_id in assignments.items():
            if cluster_id:
                cluster_sizes[cluster_id] += 1
        
        sizes = list(cluster_sizes.values())
        if sizes:
            ax3.hist(sizes, bins=range(1, max(sizes)+2), color='purple', alpha=0.7)
            ax3.set_xlabel('Cluster Size', fontsize=11)
            ax3.set_ylabel('Frequency', fontsize=11)
            ax3.set_title('Final Cluster Size Distribution', fontsize=12, fontweight='bold')
            ax3.grid(True, alpha=0.3, axis='y')
        
        # Subplot 4: Summary metrics
        ax4 = fig_perf.add_subplot(224)
        ax4.axis('off')
        
        # Calculate clustering efficiency
        total_clusters = stats['clustering']['total_clusters']
        total_vehicles = stats['application']['total_vehicles']
        clustering_efficiency = (stats['application']['clusters_formed'] / total_vehicles * 100) if total_vehicles > 0 else 0
        
        # Get avg trust score
        if self.history['trust_scores']:
            last_trust_scores = list(self.history['trust_scores'][-1].values())
            avg_trust = np.mean(last_trust_scores) if last_trust_scores else 0.0
        else:
            avg_trust = 0.0
        
        summary_text = f"""
        SIMULATION SUMMARY
        {'='*35}
        Duration: {self.duration:.1f}s
        Vehicles: {self.num_vehicles}
        Algorithm: {self.algorithm.name}
        
        CLUSTERING METRICS
        {'='*35}
        Total Clusters: {total_clusters}
        Avg Cluster Size: {stats['clustering']['avg_cluster_size']:.2f}
        Clustered Vehicles: {stats['clustering']['total_clustered_vehicles']}
        Cluster Formations: {stats['application']['clusters_formed']}
        Clustering Efficiency: {clustering_efficiency:.1f}%
        
        TRUST METRICS
        {'='*35}
        Trust Evaluations: {stats['application'].get('trust_evaluations', 0)}
        Malicious Detected: {stats['application'].get('malicious_nodes_detected', 0)}
        Avg Trust Score: {avg_trust:.3f}
        
        MESSAGE METRICS
        {'='*35}
        Messages Sent: {stats['application']['messages_sent']}
        Messages Received: {stats['application']['messages_received']}
        Message Rate: {stats['application']['messages_sent']/self.duration:.1f} msg/s
        """
        
        ax4.text(0.1, 0.95, summary_text, transform=ax4.transAxes,
                fontsize=10, verticalalignment='top', fontfamily='monospace',
                bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8))
        
        plt.tight_layout()
        
        if save:
            filename = f'performance_metrics_{self.algorithm.name}.png'
            fig_perf.savefig(filename, dpi=300, bbox_inches='tight')
            logger.info(f"Saved performance plot: {filename}")
            plt.close(fig_perf)
        else:
            plt.show()
    
    def save_results(self, filename: str = None):
        """Save simulation results to JSON"""
        if filename is None:
            timestamp = int(time.time())
            filename = f'cluster_visualization_results_{timestamp}.json'
        
        # Prepare data for JSON serialization
        results = {
            'metadata': {
                'algorithm': self.algorithm.name,
                'duration': self.duration,
                'num_vehicles': self.num_vehicles,
                'timestamp': time.time()
            },
            'statistics': self.app.get_application_statistics(),
            'summary': {
                'total_frames': len(self.history['timestamps']),
                'cluster_events': len(self.history['cluster_events']),
                'head_changes': len(self.history['head_changes']),
                'avg_clusters': float(np.mean(self.history['cluster_counts'])),
                'max_clusters': int(np.max(self.history['cluster_counts'])),
                'min_clusters': int(np.min(self.history['cluster_counts']))
            }
        }
        
        try:
            with open(filename, 'w') as f:
                json.dump(results, f, indent=2)
            logger.info(f"Results saved to {filename}")
        except Exception as e:
            logger.error(f"Failed to save results: {e}")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='VANET Cluster Visualization Demo')
    parser.add_argument('--duration', type=float, default=60.0,
                       help='Simulation duration in seconds (default: 60)')
    parser.add_argument('--algorithm', type=str, default='mobility_based',
                       choices=['mobility_based', 'direction_based', 'kmeans', 'dbscan'],
                       help='Clustering algorithm (default: mobility_based)')
    parser.add_argument('--vehicles', type=int, default=45,
                       help='Number of vehicles (default: 45)')
    parser.add_argument('--animate', action='store_true',
                       help='Enable real-time animation')
    parser.add_argument('--save-plots', action='store_true',
                       help='Save plots to files')
    
    args = parser.parse_args()
    
    # Map algorithm name to enum
    algo_map = {
        'mobility_based': ClusteringAlgorithm.MOBILITY_BASED,
        'direction_based': ClusteringAlgorithm.DIRECTION_BASED,
        'kmeans': ClusteringAlgorithm.KMEANS,
        'dbscan': ClusteringAlgorithm.DBSCAN
    }
    
    algorithm = algo_map[args.algorithm]
    
    print("="*60)
    print("VANET CLUSTER FORMATION VISUALIZATION DEMO")
    print("="*60)
    print(f"Algorithm: {args.algorithm}")
    print(f"Duration: {args.duration}s")
    print(f"Vehicles: {args.vehicles}")
    print(f"Animation: {'Enabled' if args.animate else 'Disabled'}")
    print(f"Save Plots: {'Yes' if args.save_plots else 'No'}")
    print("="*60)
    
    # Create demo instance
    demo = ClusterVisualizationDemo(
        algorithm=algorithm,
        duration=args.duration,
        num_vehicles=args.vehicles,
        animate=args.animate
    )
    
    # Run simulation
    demo.setup_simulation()
    demo.run_simulation()
    
    # Create visualizations
    demo.create_visualizations(save_plots=args.save_plots)
    
    # Save results
    demo.save_results()
    
    print("="*60)
    print("DEMO COMPLETED SUCCESSFULLY")
    print("="*60)

if __name__ == "__main__":
    main()
