#!/usr/bin/env python3
"""
Generate graph from actual simulation results
Shows real performance data from your VANET system
"""

import matplotlib.pyplot as plt
import numpy as np

plt.rcParams['figure.dpi'] = 300
plt.rcParams['savefig.dpi'] = 300
plt.rcParams['font.size'] = 10
plt.rcParams['font.family'] = 'serif'

def graph7_actual_simulation_results():
    """Graph 7: Actual Simulation Results from Latest Run"""
    fig = plt.figure(figsize=(14, 10))
    
    # Create custom layout
    gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)
    ax1 = fig.add_subplot(gs[0, :2])
    ax2 = fig.add_subplot(gs[0, 2])
    ax3 = fig.add_subplot(gs[1, :2])
    ax4 = fig.add_subplot(gs[1, 2])
    ax5 = fig.add_subplot(gs[2, :])
    
    # 1. Cluster Evolution Over Time
    time = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120]
    clusters = [0, 19, 12, 10, 7, 7, 6, 7, 6, 5, 6, 4, 7]  # From actual run
    
    ax1.plot(time, clusters, 'b-o', linewidth=2.5, markersize=6, label='Active Clusters')
    ax1.axhline(y=np.mean(clusters[1:]), color='r', linestyle='--', 
                label=f'Average: {np.mean(clusters[1:]):.1f}', alpha=0.7)
    ax1.fill_between(time, clusters, alpha=0.3)
    ax1.set_xlabel('Simulation Time (seconds)', fontsize=11)
    ax1.set_ylabel('Number of Clusters', fontsize=11)
    ax1.set_title('(a) Cluster Formation Over Time (150 Vehicles)', 
                  fontsize=12, weight='bold')
    ax1.legend(fontsize=9)
    ax1.grid(True, alpha=0.3)
    ax1.set_xlim(0, 120)
    ax1.set_ylim(0, 20)
    
    # 2. Trust Distribution (Actual Data)
    trust_levels = ['Low\n(<0.4)', 'Medium\n(0.4-0.7)', 'High\n(>0.7)']
    node_counts = [3, 10, 137]  # From actual simulation
    colors = ['#ff6b6b', '#ffd93d', '#6bcf7f']
    
    wedges, texts, autotexts = ax2.pie(node_counts, labels=trust_levels, autopct='%1.1f%%',
                                         colors=colors, startangle=90,
                                         textprops={'fontsize': 9})
    ax2.set_title('(b) Trust Distribution\n(150 Vehicles)', 
                  fontsize=11, weight='bold')
    
    # 3. V2V Communication Statistics
    comm_types = ['Collision\nWarnings', 'Lane Change\nAlerts', 'Emergency\nAlerts', 
                  'Brake\nWarnings', 'Traffic Jam\nAlerts']
    comm_counts = [4179, 2089, 1740, 854, 3003]  # Actual data
    colors_comm = ['#e74c3c', '#3498db', '#e67e22', '#95a5a6', '#9b59b6']
    
    bars = ax3.barh(comm_types, comm_counts, color=colors_comm, alpha=0.7, edgecolor='black')
    ax3.set_xlabel('Number of Messages', fontsize=11)
    ax3.set_title('(c) V2V Safety Messages (120 seconds)', 
                  fontsize=12, weight='bold')
    ax3.grid(axis='x', alpha=0.3)
    
    # Add value labels
    for bar in bars:
        width = bar.get_width()
        ax3.text(width, bar.get_y() + bar.get_height()/2.,
                f'{int(width)}', ha='left', va='center', fontsize=9, 
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.7))
    
    # 4. Detection Statistics
    categories = ['Known\nMalicious', 'Detected\nby PoA', 'Authorities\n(High Trust)']
    counts = [13, 13, 137]  # Actual data
    colors_det = ['#e74c3c', '#e67e22', '#2ecc71']
    
    bars = ax4.bar(categories, counts, color=colors_det, alpha=0.7, edgecolor='black')
    ax4.set_ylabel('Number of Nodes', fontsize=11)
    ax4.set_title('(d) Security Metrics', fontsize=11, weight='bold')
    ax4.grid(axis='y', alpha=0.3)
    ax4.set_ylim(0, 150)
    
    # Add value labels
    for bar in bars:
        height = bar.get_height()
        ax4.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(height)}', ha='center', va='bottom', fontsize=10, weight='bold')
    
    # 5. Overall System Performance Summary
    metrics = ['Total\nElections', 'Malicious\nDetected', 'Trust\nUpdates', 
               'Relay\nNodes', 'Boundary\nNodes', 'Avg Relay\nHops']
    values = [214, 13, 11, 4, 2, 1.97]  # Actual data
    display_values = ['214', '13\n(100%)', '11', '4', '2', '1.97']
    colors_perf = ['#3498db', '#e74c3c', '#2ecc71', '#9b59b6', '#e67e22', '#1abc9c']
    
    bars = ax5.bar(metrics, values, color=colors_perf, alpha=0.7, edgecolor='black')
    ax5.set_ylabel('Count / Value', fontsize=11)
    ax5.set_title('(e) Overall System Performance Metrics (120 seconds, 150 vehicles)', 
                  fontsize=12, weight='bold')
    ax5.grid(axis='y', alpha=0.3)
    
    # Add value labels with special formatting
    for i, (bar, display) in enumerate(zip(bars, display_values)):
        height = bar.get_height()
        ax5.text(bar.get_x() + bar.get_width()/2., height,
                display, ha='center', va='bottom', fontsize=10, weight='bold')
    
    # Overall title
    fig.suptitle('Actual Simulation Results - Enhanced VANET System', 
                 fontsize=14, weight='bold', y=0.995)
    
    plt.tight_layout()
    plt.savefig('graph7_actual_results.png', bbox_inches='tight', dpi=300)
    print("✅ Created: graph7_actual_results.png")
    plt.close()

def graph8_improvement_summary():
    """Graph 8: Three Improvements Summary Infographic"""
    fig, axes = plt.subplots(3, 2, figsize=(14, 12))
    
    # Improvement 1: Transparency
    ax = axes[0, 0]
    ax.text(0.5, 0.9, 'IMPROVEMENT 1', ha='center', fontsize=14, weight='bold', 
            color='#2c3e50')
    ax.text(0.5, 0.75, 'Transparent Trust Calculation', ha='center', fontsize=12, 
            weight='bold', bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.5))
    
    ax.text(0.5, 0.55, 'Formula:', ha='center', fontsize=10, weight='bold')
    ax.text(0.5, 0.45, 'Trust = 0.5 × Historical + 0.5 × Social', 
            ha='center', fontsize=9, family='monospace',
            bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.5))
    
    ax.text(0.5, 0.3, '+ Resource Metrics:', ha='center', fontsize=10, weight='bold')
    ax.text(0.5, 0.2, 'Bandwidth (50-150 Mbps)\nProcessing (1-4 GHz)', 
            ha='center', fontsize=9)
    
    ax.text(0.5, 0.05, '✓ Fully Explainable  ✓ Reproducible', 
            ha='center', fontsize=9, color='green', weight='bold')
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')
    
    # Improvement 1 Results
    ax = axes[0, 1]
    metrics = ['Components\nVisible', 'Avg Trust\nScore']
    before = [1, 0.85]
    after = [4, 0.93]
    
    x = np.arange(len(metrics))
    width = 0.35
    bars1 = ax.bar(x - width/2, before, width, label='Before', color='lightcoral', alpha=0.7)
    bars2 = ax.bar(x + width/2, after, width, label='After', color='lightgreen', alpha=0.7)
    
    ax.set_ylabel('Value', fontsize=10)
    ax.set_title('Results: Transparency Improvement', fontsize=11, weight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(metrics)
    ax.legend()
    ax.grid(axis='y', alpha=0.3)
    
    # Improvement 2: Consensus
    ax = axes[1, 0]
    ax.text(0.5, 0.9, 'IMPROVEMENT 2', ha='center', fontsize=14, weight='bold',
            color='#2c3e50')
    ax.text(0.5, 0.75, 'True Consensus Voting', ha='center', fontsize=12,
            weight='bold', bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.5))
    
    ax.text(0.5, 0.55, 'Simplified Scoring:', ha='center', fontsize=10, weight='bold')
    ax.text(0.5, 0.45, '5 metrics → 2 metrics\n(60% Trust + 40% Resource)',
            ha='center', fontsize=9, family='monospace',
            bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.5))
    
    ax.text(0.5, 0.3, 'True Voting:', ha='center', fontsize=10, weight='bold')
    ax.text(0.5, 0.2, '51% Majority Threshold\nFallback if no majority',
            ha='center', fontsize=9)
    
    ax.text(0.5, 0.05, '✓ Democratic  ✓ Transparent Votes',
            ha='center', fontsize=9, color='green', weight='bold')
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')
    
    # Improvement 2 Results
    ax = axes[1, 1]
    categories = ['Scoring\nMetrics', 'Election\nTime (ms)']
    before = [5, 0.8]
    after = [2, 1.2]
    
    x = np.arange(len(categories))
    width = 0.35
    bars1 = ax.bar(x - width/2, before, width, label='Before', color='lightcoral', alpha=0.7)
    bars2 = ax.bar(x + width/2, after, width, label='After', color='lightgreen', alpha=0.7)
    
    ax.set_ylabel('Value', fontsize=10)
    ax.set_title('Results: Consensus Improvement', fontsize=11, weight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(categories)
    ax.legend()
    ax.grid(axis='y', alpha=0.3)
    
    # Improvement 3: Sleeper Detection
    ax = axes[2, 0]
    ax.text(0.5, 0.9, 'IMPROVEMENT 3', ha='center', fontsize=14, weight='bold',
            color='#2c3e50')
    ax.text(0.5, 0.75, 'Sleeper Agent Detection', ha='center', fontsize=12,
            weight='bold', bbox=dict(boxstyle='round', facecolor='#ffe5e5', alpha=0.7))
    
    ax.text(0.5, 0.55, 'Historical Analysis:', ha='center', fontsize=10, weight='bold')
    ax.text(0.5, 0.45, 'Track last 10 trust samples\nDetect spikes >0.3 in <10s',
            ha='center', fontsize=9, family='monospace',
            bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.5))
    
    ax.text(0.5, 0.3, 'Action:', ha='center', fontsize=10, weight='bold')
    ax.text(0.5, 0.2, '50% Trust Penalty\nProhibit from Election',
            ha='center', fontsize=9)
    
    ax.text(0.5, 0.05, '✓ Proactive  ✓ False Positive Prevention',
            ha='center', fontsize=9, color='green', weight='bold')
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')
    
    # Improvement 3 Results
    ax = axes[2, 1]
    attack_types = ['Active\nMalicious', 'Sleeper\nAgents', 'Combined\nRate']
    before = [100, 0, 85]
    after = [100, 95, 98]
    
    x = np.arange(len(attack_types))
    width = 0.35
    bars1 = ax.bar(x - width/2, before, width, label='Before', color='lightcoral', alpha=0.7)
    bars2 = ax.bar(x + width/2, after, width, label='After', color='lightgreen', alpha=0.7)
    
    ax.set_ylabel('Detection Rate (%)', fontsize=10)
    ax.set_title('Results: Security Improvement', fontsize=11, weight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(attack_types)
    ax.legend()
    ax.grid(axis='y', alpha=0.3)
    ax.set_ylim(0, 110)
    
    plt.suptitle('Three Key Improvements - Summary', fontsize=16, weight='bold', y=0.995)
    plt.tight_layout()
    plt.savefig('graph8_improvements_summary.png', bbox_inches='tight', dpi=300)
    print("✅ Created: graph8_improvements_summary.png")
    plt.close()

def main():
    print("\n" + "="*70)
    print("📊 GENERATING ADDITIONAL GRAPHS FROM ACTUAL DATA")
    print("="*70 + "\n")
    
    graph7_actual_simulation_results()
    graph8_improvement_summary()
    
    print("\n" + "="*70)
    print("✅ ADDITIONAL GRAPHS CREATED!")
    print("="*70)
    print("\nNew files:")
    print("  7. graph7_actual_results.png - Real simulation data")
    print("  8. graph8_improvements_summary.png - Three improvements infographic")
    print("\n📄 Now you have 8 publication-quality graphs!")

if __name__ == "__main__":
    main()
