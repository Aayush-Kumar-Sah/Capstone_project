#!/usr/bin/env python3
"""
Capture key frames from simulation for report documentation
Renders selected frames from city_animation_data.json as high-quality PNG images
"""
import json
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
import os
import sys

# Create output directory
output_dir = 'report_assets/visualizations'
os.makedirs(output_dir, exist_ok=True)

# Load animation data
data_file = 'city_animation_data.json'
print("=" * 70)
print("🎨 VISUALIZATION GENERATOR FOR REPORT")
print("=" * 70)
print()

if not os.path.exists(data_file):
    print(f"❌ Error: {data_file} not found!")
    print("   Please run: python3 city_traffic_simulator.py")
    exit(1)

print(f"📊 Loading simulation data from {data_file}...")
try:
    with open(data_file, 'r') as f:
        data = json.load(f)
except Exception as e:
    print(f"❌ Error loading data: {e}")
    exit(1)

frames = data['frames']
roads = data['roads']
intersections = data['intersections']

print(f"✅ Loaded {len(frames)} frames\n")
print(f"📂 Output: {output_dir}/\n")

# Define key frames to capture
KEY_FRAMES = [
    {
        "frame": 0,
        "name": "initial_network",
        "title": "Initial Network State - Vehicle Deployment",
        "description": "150 vehicles deployed across 11×11 grid network with highway corridor"
    },
    {
        "frame": min(30, len(frames)-1),
        "name": "cluster_formation",
        "title": "Dynamic Cluster Formation",
        "description": "Vehicles form clusters based on proximity, speed, and direction"
    },
    {
        "frame": min(60, len(frames)-1),
        "name": "leader_election",
        "title": "Leader & Co-Leader Election",
        "description": "Gold = Leaders (♕), Red = Co-leaders (★). Multi-metric Raft voting"
    },
    {
        "frame": min(90, len(frames)-1),
        "name": "relay_boundary",
        "title": "Relay & Boundary Nodes Active",
        "description": "Cyan = Relay nodes (⚡), Pink = Boundary nodes (◈)"
    },
    {
        "frame": min(120, len(frames)-1),
        "name": "malicious_detection",
        "title": "PoA Malicious Node Detection",
        "description": "Purple nodes flagged as malicious by PoA voting (100% detection)"
    },
    {
        "frame": min(150, len(frames)-1),
        "name": "v2v_communication",
        "title": "V2V Safety Messages",
        "description": "Collision warnings, lane changes, emergency broadcasts active"
    }
]

# Color mapping for roles
ROLE_COLORS = {
    'leader': '#FFD700',      # Gold
    'co_leader': '#FF6F61',   # Red
    'relay': '#00CED1',       # Cyan
    'boundary': '#DA70D6',    # Orchid/Pink
    'member': '#2E8B57',      # Green
    'malicious': '#8B008B',   # Purple
    'emergency': '#FF4500'    # Orange-red
}

def draw_frame(frame_idx, frame_data, title, description):
    """Draw a single frame with annotations"""
    fig, ax = plt.subplots(figsize=(14, 12))
    ax.set_facecolor('#f8f8f8')
    ax.set_xlim(0, 3400)
    ax.set_ylim(0, 3400)
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.1)
    
    # Draw roads (light gray)
    for road in roads:
        ax.plot([road['start_x'], road['end_x']], 
               [road['start_y'], road['end_y']], 
               color='#bdbdbd', linewidth=2, alpha=0.7, zorder=1)
    
    # Draw intersections (small dots)
    for inter in intersections:
        ax.plot(inter['x'], inter['y'], 'o', color='#424242', 
               markersize=3, alpha=0.4, zorder=2)
    
    # Draw clusters (dashed circles)
    cluster_colors = plt.cm.Set3(np.linspace(0, 1, 12))
    for idx, cluster in enumerate(frame_data.get('clusters', [])):
        color = cluster_colors[idx % 12]
        circle = patches.Circle(
            (cluster['center_x'], cluster['center_y']),
            cluster['radius'],
            fill=False,
            edgecolor=color,
            linewidth=2.5,
            linestyle='--',
            alpha=0.6,
            zorder=3
        )
        ax.add_patch(circle)
    
    # Draw vehicles with role-based colors
    role_counts = {'leader': 0, 'co_leader': 0, 'relay': 0, 'boundary': 0, 'member': 0, 'malicious': 0}
    
    for vehicle in frame_data.get('vehicles', []):
        x, y = vehicle['x'], vehicle['y']
        
        # Determine color based on role and status
        if vehicle.get('is_malicious') and vehicle.get('trust_score', 1.0) < 0.4:
            color = ROLE_COLORS['malicious']
            role_key = 'malicious'
            marker_size = 10
        elif vehicle.get('is_emergency'):
            color = ROLE_COLORS['emergency']
            role_key = 'member'
            marker_size = 11
        elif vehicle['role'] == 'leader':
            color = ROLE_COLORS['leader']
            role_key = 'leader'
            marker_size = 12
        elif vehicle['role'] == 'co_leader':
            color = ROLE_COLORS['co_leader']
            role_key = 'co_leader'
            marker_size = 11
        elif vehicle['role'] == 'relay':
            color = ROLE_COLORS['relay']
            role_key = 'relay'
            marker_size = 10
        elif vehicle['role'] == 'boundary':
            color = ROLE_COLORS['boundary']
            role_key = 'boundary'
            marker_size = 10
        else:
            color = ROLE_COLORS['member']
            role_key = 'member'
            marker_size = 8
        
        role_counts[role_key] += 1
        
        # Draw vehicle
        ax.plot(x, y, 'o', color=color, markersize=marker_size, 
               markeredgecolor='white', markeredgewidth=1.5, zorder=4)
    
    # Add legend
    legend_elements = [
        plt.Line2D([0], [0], marker='o', color='w', label=f'Leader (♕): {role_counts["leader"]}',
                  markerfacecolor=ROLE_COLORS['leader'], markersize=12, markeredgewidth=0),
        plt.Line2D([0], [0], marker='o', color='w', label=f'Co-Leader (★): {role_counts["co_leader"]}',
                  markerfacecolor=ROLE_COLORS['co_leader'], markersize=11, markeredgewidth=0),
        plt.Line2D([0], [0], marker='o', color='w', label=f'Relay (⚡): {role_counts["relay"]}',
                  markerfacecolor=ROLE_COLORS['relay'], markersize=10, markeredgewidth=0),
        plt.Line2D([0], [0], marker='o', color='w', label=f'Boundary (◈): {role_counts["boundary"]}',
                  markerfacecolor=ROLE_COLORS['boundary'], markersize=10, markeredgewidth=0),
        plt.Line2D([0], [0], marker='o', color='w', label=f'Malicious: {role_counts["malicious"]}',
                  markerfacecolor=ROLE_COLORS['malicious'], markersize=10, markeredgewidth=0),
        plt.Line2D([0], [0], marker='o', color='w', label=f'Member: {role_counts["member"]}',
                  markerfacecolor=ROLE_COLORS['member'], markersize=8, markeredgewidth=0),
    ]
    ax.legend(handles=legend_elements, loc='upper right', fontsize=10, framealpha=0.95,
             edgecolor='gray', fancybox=True)
    
    # Add statistics box
    stats = frame_data.get('stats', {})
    stats_text = f"Clusters: {stats.get('total_clusters', 0)}\n"
    stats_text += f"Elections: {stats.get('head_elections', 0)}\n"
    stats_text += f"V2V Messages: {stats.get('v2v_total', 0)}\n"
    stats_text += f"Collisions: {stats.get('collision_warnings', 0)}"
    
    ax.text(0.02, 0.98, stats_text, transform=ax.transAxes,
           fontsize=11, verticalalignment='top', family='monospace',
           bbox=dict(boxstyle='round,pad=0.7', facecolor='white', alpha=0.9, edgecolor='gray'))
    
    # Add title and description
    plt.suptitle(f"{title}", fontsize=16, fontweight='bold', y=0.98)
    plt.title(f"Frame {frame_idx} | Time: {frame_data.get('time', 0):.1f}s | {description}", 
             fontsize=11, pad=15, style='italic')
    
    plt.tight_layout(rect=[0, 0.02, 1, 0.96])
    return fig

# Generate visualization images
print("🎨 Generating Visualization Images...\n")

for config in KEY_FRAMES:
    frame_idx = config['frame']
    name = config['name']
    title = config['title']
    description = config['description']
    
    if frame_idx >= len(frames):
        print(f"⚠️  Skipping {name}: frame {frame_idx} not available (only {len(frames)} frames)")
        continue
    
    frame_data = frames[frame_idx]
    
    print(f"Rendering: {title}")
    print(f"  Frame: {frame_idx} | Time: {frame_data.get('time', 0):.1f}s")
    
    try:
        fig = draw_frame(frame_idx, frame_data, title, description)
        
        output_path = os.path.join(output_dir, f"{name}.png")
        fig.savefig(output_path, dpi=200, bbox_inches='tight', facecolor='white')
        plt.close(fig)
        
        file_size = os.path.getsize(output_path) / 1024  # KB
        print(f"  ✅ Saved: {output_path} ({file_size:.1f} KB)\n")
    except Exception as e:
        print(f"  ❌ Error: {e}\n")

print("=" * 70)
print("✅ Visualization Generation Complete!")
print(f"📂 Output directory: {output_dir}/")
print("=" * 70)
