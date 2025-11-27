import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import matplotlib.lines as mlines

fig, ax = plt.subplots(figsize=(10, 12))
ax.set_xlim(0, 10)
ax.set_ylim(0, 14)
ax.axis('off')

# Title
ax.text(5, 13.5, 'Transparent Five-Metric Election Mechanism', 
        fontsize=16, weight='bold', ha='center')

# Colors
color_input = '#e8f4f8'
color_security = '#ffe6e6'
color_metric = '#e6f3e6'
color_composite = '#fff4e6'
color_consensus = '#f0e6ff'
color_output = '#e6ffe6'

# Helper function for boxes
def draw_box(x, y, w, h, text, color, fontsize=10):
    box = FancyBboxPatch((x-w/2, y-h/2), w, h, 
                         boxstyle="round,pad=0.1", 
                         edgecolor='black', facecolor=color, linewidth=2)
    ax.add_patch(box)
    ax.text(x, y, text, fontsize=fontsize, ha='center', va='center', weight='bold')

def draw_arrow(x1, y1, x2, y2, label=''):
    arrow = FancyArrowPatch((x1, y1), (x2, y2),
                           arrowstyle='->', mutation_scale=20, 
                           linewidth=2, color='black')
    ax.add_patch(arrow)
    if label:
        mid_x, mid_y = (x1+x2)/2, (y1+y2)/2
        ax.text(mid_x + 0.3, mid_y, label, fontsize=8, style='italic')

# Step 1: Input
draw_box(5, 12, 3, 0.6, 'Cluster Members\n(Candidates)', color_input, 10)
draw_arrow(5, 11.7, 5, 11.2)

# Step 2: Security Layers
draw_box(2.5, 10.5, 2.5, 0.8, 'Layer 1:\nProactive PoA\nCheck', color_security, 9)
draw_box(7.5, 10.5, 2.5, 0.8, 'Layer 2:\nSleeper Agent\nDetection', color_security, 9)
draw_arrow(5, 11.2, 2.5, 10.9)
draw_arrow(5, 11.2, 7.5, 10.9)
draw_arrow(2.5, 10.1, 5, 9.5)
draw_arrow(7.5, 10.1, 5, 9.5)

# Security passed
draw_box(5, 9.2, 3, 0.5, 'Security Checks Passed', color_security, 9)
draw_arrow(5, 8.95, 5, 8.5)

# Step 3: Five Metrics (Vertical stack)
y_start = 8.2
metric_height = 0.6
metric_gap = 0.1

metrics = [
    ('Trust (40%)\n0.5×Historical + 0.5×Social', '#ffcccc'),
    ('Resource (20%)\n(Bandwidth + Processing)/2', '#cce5ff'),
    ('Stability (15%)\n(ClusterTime + ConnQuality)/2', '#d9f2d9'),
    ('Behavior (15%)\n(Authenticity + Cooperation)/2', '#ffe6cc'),
    ('Centrality (10%)\n1 - Distance/MaxRadius', '#e6ccff')
]

for i, (metric_text, metric_color) in enumerate(metrics):
    y_pos = y_start - i * (metric_height + metric_gap)
    draw_box(5, y_pos, 4, metric_height, metric_text, metric_color, 8)

# Arrow from metrics to composite
draw_arrow(5, y_start - len(metrics)*(metric_height + metric_gap) + 0.3, 5, 4.8)

# Step 4: Composite Score
composite_text = 'Composite Score\n0.40×T + 0.20×R + 0.15×S\n+ 0.15×B + 0.10×C'
draw_box(5, 4.3, 4.5, 0.9, composite_text, color_composite, 9)
draw_arrow(5, 3.85, 5, 3.4)

# Step 5: Transparent Logging
draw_box(5, 3, 3.5, 0.6, '📊 Log Full Breakdown\n(All formulas visible)', color_output, 9)
draw_arrow(5, 2.7, 5, 2.3)

# Step 6: Consensus Voting
draw_box(5, 1.9, 3.5, 0.7, 'Trust-Weighted Voting\n51% Majority Consensus', color_consensus, 9)
draw_arrow(5, 1.55, 5, 1.1)

# Step 7: Output
draw_box(5, 0.7, 2.5, 0.5, 'Elected Leader', color_output, 10)

# Add legend for weights
legend_x = 0.5
legend_y = 1.5
ax.text(legend_x, legend_y + 1.2, 'Weight Distribution:', fontsize=9, weight='bold')
ax.text(legend_x, legend_y + 0.9, '• Trust: 40% (Security priority)', fontsize=8)
ax.text(legend_x, legend_y + 0.6, '• Resource: 20% (Capacity)', fontsize=8)
ax.text(legend_x, legend_y + 0.3, '• Stability: 15% (Longevity)', fontsize=8)
ax.text(legend_x, legend_y, '• Behavior: 15% (Reliability)', fontsize=8)
ax.text(legend_x, legend_y - 0.3, '• Centrality: 10% (Efficiency)', fontsize=8)

# Add transparency note
ax.text(5, 0.15, '✓ Complete Transparency: All formulas, weights, and calculations explicitly logged', 
        fontsize=8, ha='center', style='italic', 
        bbox=dict(boxstyle='round,pad=0.5', facecolor='yellow', alpha=0.3))

plt.tight_layout()
plt.savefig('graph2_election_mechanism.png', dpi=300, bbox_inches='tight')
print('Updated graph2_election_mechanism.png - showing only our 5-metric transparent system')
