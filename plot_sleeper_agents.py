#!/usr/bin/env python3
"""
Visualize sleeper agent behavior over time
Shows trust evolution and detection timeline
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

# Set style
plt.style.use('seaborn-v0_8-darkgrid')
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), dpi=300)
fig.suptitle('Sleeper Agent Behavior: Trust Evolution and Detection Timeline', 
             fontsize=16, fontweight='bold', y=0.98)

# ============================================================================
# SUBPLOT 1: Trust Score Evolution Over Time
# ============================================================================

# Timeline data (seconds)
time = np.arange(0, 60, 0.1)

# v5 sleeper agent (activates at t=29.7s)
v5_trust = np.ones_like(time) * 0.85
v5_trust[time >= 29.7] = 0.15  # Activation
v5_trust[time >= 30.0] = 0.09  # Detection penalty

# v15 sleeper agent (activates at t=27.7s)
v15_trust = np.ones_like(time) * 0.85
v15_trust[time >= 27.7] = 0.15  # Activation
v15_trust[time >= 30.0] = 0.08  # Detection penalty

# Regular legitimate node (stable trust)
regular_trust = np.ones_like(time) * 0.95
regular_trust += np.random.normal(0, 0.02, len(time))  # Minor fluctuations
regular_trust = np.clip(regular_trust, 0.85, 1.0)

# Regular malicious node (consistently low)
malicious_trust = np.ones_like(time) * 0.20
malicious_trust -= np.linspace(0, 0.05, len(time))  # Gradual degradation
malicious_trust = np.clip(malicious_trust, 0.05, 0.20)

# Plot trust evolution
ax1.plot(time, v5_trust, 'r-', linewidth=3, label='v5 (Sleeper Agent)', marker='', markersize=0)
ax1.plot(time, v15_trust, 'darkred', linewidth=3, linestyle='--', label='v15 (Sleeper Agent)', marker='', markersize=0)
ax1.plot(time, regular_trust, 'g-', linewidth=2, alpha=0.7, label='Regular Node (Legitimate)')
ax1.plot(time, malicious_trust, 'orange', linewidth=2, alpha=0.7, label='Active Malicious Node')

# Mark key events
ax1.axvline(x=27.7, color='darkred', linestyle=':', alpha=0.6, linewidth=2)
ax1.text(27.7, 0.92, 'v15 Activates', ha='center', fontsize=10, color='darkred', fontweight='bold')

ax1.axvline(x=29.7, color='red', linestyle=':', alpha=0.6, linewidth=2)
ax1.text(29.7, 0.98, 'v5 Activates', ha='center', fontsize=10, color='red', fontweight='bold')

ax1.axvline(x=30.0, color='blue', linestyle='-.', alpha=0.8, linewidth=2.5)
ax1.text(30.0, 0.05, 'PoA Detection\n(Both Flagged)', ha='center', fontsize=11, 
         color='blue', fontweight='bold', bbox=dict(boxstyle='round,pad=0.5', facecolor='lightblue', alpha=0.7))

# Highlight detection zones
ax1.axhspan(0.0, 0.4, alpha=0.15, color='red', label='Malicious Zone (< 0.4)')
ax1.axhspan(0.8, 1.0, alpha=0.15, color='green', label='High Trust Zone (> 0.8)')

# Labels and formatting
ax1.set_xlabel('Time (seconds)', fontsize=12, fontweight='bold')
ax1.set_ylabel('Trust Score', fontsize=12, fontweight='bold')
ax1.set_title('A. Trust Score Evolution: Sleeper Agents vs. Regular Nodes', 
              fontsize=13, fontweight='bold', pad=15)
ax1.set_ylim(0, 1.05)
ax1.set_xlim(0, 60)
ax1.grid(True, alpha=0.3)
ax1.legend(loc='center left', fontsize=10, framealpha=0.9)

# Add annotations
ax1.annotate('', xy=(29.7, 0.15), xytext=(29.7, 0.85),
            arrowprops=dict(arrowstyle='->', lw=2, color='red', alpha=0.7))
ax1.text(26, 0.5, 'Trust Plummets\n82% Drop', fontsize=10, color='red', 
         fontweight='bold', ha='center',
         bbox=dict(boxstyle='round,pad=0.5', facecolor='white', edgecolor='red', alpha=0.8))

# ============================================================================
# SUBPLOT 2: Detection Timeline (Gantt Chart Style)
# ============================================================================

# Define phases for each sleeper agent
agents = ['v15\n(Sleeper Agent)', 'v5\n(Sleeper Agent)']
phases = {
    'v15': [
        ('Normal Behavior', 0, 27.7, 'green'),
        ('Activation', 27.7, 30.0, 'orange'),
        ('Detected & Flagged', 30.0, 60, 'red')
    ],
    'v5': [
        ('Normal Behavior', 0, 29.7, 'green'),
        ('Activation', 29.7, 30.0, 'orange'),
        ('Detected & Flagged', 30.0, 60, 'red')
    ]
}

# Plot timeline bars
y_positions = [1, 0]
for idx, (agent_name, agent_key) in enumerate(zip(agents, ['v15', 'v5'])):
    y = y_positions[idx]
    
    for phase_name, start, end, color in phases[agent_key]:
        duration = end - start
        ax2.barh(y, duration, left=start, height=0.4, color=color, 
                edgecolor='black', linewidth=1.5, alpha=0.8)
        
        # Add phase labels
        if duration > 5:  # Only label if wide enough
            ax2.text(start + duration/2, y, phase_name, 
                    ha='center', va='center', fontsize=9, fontweight='bold', color='white')

# Add activation markers
ax2.plot([27.7, 27.7], [-0.3, 1.3], 'darkred', linestyle='--', linewidth=2, alpha=0.7)
ax2.text(27.7, 1.5, 'v15: t=27.7s\nTrust: 0.85→0.15', ha='center', fontsize=9, 
         color='darkred', fontweight='bold',
         bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor='darkred'))

ax2.plot([29.7, 29.7], [-0.3, 1.3], 'red', linestyle='--', linewidth=2, alpha=0.7)
ax2.text(29.7, -0.55, 'v5: t=29.7s\nTrust: 0.85→0.15', ha='center', fontsize=9, 
         color='red', fontweight='bold',
         bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor='red'))

# Add detection marker
ax2.axvline(x=30.0, color='blue', linestyle='-.', linewidth=3, alpha=0.9)
ax2.text(30.0, -0.85, 'PoA Detection\nt=30.0s', ha='center', fontsize=10, 
         color='blue', fontweight='bold',
         bbox=dict(boxstyle='round,pad=0.4', facecolor='lightblue', edgecolor='blue', linewidth=2))

# Format timeline
ax2.set_yticks(y_positions)
ax2.set_yticklabels(agents, fontsize=11, fontweight='bold')
ax2.set_xlabel('Time (seconds)', fontsize=12, fontweight='bold')
ax2.set_title('B. Detection Timeline: From Normal Behavior to Flagged Status', 
              fontsize=13, fontweight='bold', pad=15)
ax2.set_xlim(0, 60)
ax2.set_ylim(-1, 2)
ax2.grid(axis='x', alpha=0.3)

# Add legend
legend_elements = [
    mpatches.Patch(color='green', label='Normal Behavior (High Trust)', alpha=0.8),
    mpatches.Patch(color='orange', label='Activation Phase (Trust Drop)', alpha=0.8),
    mpatches.Patch(color='red', label='Detected & Flagged (Low Trust)', alpha=0.8)
]
ax2.legend(handles=legend_elements, loc='upper right', fontsize=10, framealpha=0.9)

# Add detection performance metrics box
metrics_text = (
    "Detection Performance:\n"
    "━━━━━━━━━━━━━━━━━━━━\n"
    "v15: Detected in 2.3s\n"
    "v5:  Detected in 0.3s\n"
    "━━━━━━━━━━━━━━━━━━━━\n"
    "Avg: 1.3 seconds ✓\n"
    "Trust Drop: 82-89%"
)
ax2.text(45, 0.5, metrics_text, fontsize=9, color='black', fontweight='bold',
         ha='center', va='center',
         bbox=dict(boxstyle='round,pad=0.7', facecolor='lightyellow', 
                  edgecolor='black', linewidth=2))

# Overall layout
plt.tight_layout(rect=[0, 0.02, 1, 0.96])

# Add footer
fig.text(0.5, 0.01, 
         '✓ Improvement 3: Sleeper Agent Detection via Historical Analysis | '
         'Detection Rate: 100% (2/2 detected) | Average Response Time: 1.3s',
         ha='center', fontsize=10, style='italic', color='darkblue', fontweight='bold')

# Save
output_file = 'sleeper_agent_timeline.png'
plt.savefig(output_file, dpi=300, bbox_inches='tight', facecolor='white')
print(f"✓ Saved sleeper agent timeline visualization: {output_file}")
print(f"  Size: {14}x{10} inches at 300 DPI")
print(f"  Shows trust evolution and detection timeline for v5 and v15")

plt.close()
