import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

fig, ax = plt.subplots(figsize=(10, 12))
ax.set_xlim(0, 10)
ax.set_ylim(0, 14)
ax.axis('off')

# Colors
color_input = '#e8f4f8'
color_security = '#ffebee'
color_metric = '#fff3e0'
color_composite = '#e8f5e9'
color_consensus = '#f3e5f5'
color_output = '#c8e6c9'

def draw_box(x, y, w, h, text, color, fontsize=10, bold=False):
    box = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.1", 
                          edgecolor='black', facecolor=color, linewidth=2)
    ax.add_patch(box)
    weight = 'bold' if bold else 'normal'
    ax.text(x + w/2, y + h/2, text, ha='center', va='center', 
            fontsize=fontsize, weight=weight, wrap=True)

def draw_arrow(x1, y1, x2, y2):
    arrow = FancyArrowPatch((x1, y1), (x2, y2), 
                           arrowstyle='->', mutation_scale=20, 
                           linewidth=2, color='black')
    ax.add_patch(arrow)

# Title
ax.text(5, 13.2, 'Transparent 5-Metric Election Process', 
        ha='center', fontsize=14, weight='bold')

# 1. Input
draw_box(3, 12, 4, 0.6, 'Cluster Election Triggered', color_input, 11, True)
draw_arrow(5, 12, 5, 11.4)

# 2. Security Layer 1 - Sleeper Detection
draw_box(2.5, 10.5, 5, 0.8, 'Security Layer 1: Sleeper Agent Check\n(Trust spike >0.3 in <10s)', 
         color_security, 9)
draw_arrow(5, 10.5, 5, 9.8)

# 3. Security Layer 2 - PoA
draw_box(2.5, 9, 5, 0.8, 'Security Layer 2: PoA Status Check\n(Flagged by authority consensus?)', 
         color_security, 9)
draw_arrow(5, 9, 5, 8.2)

# 4. Eligible candidates
draw_box(3, 7.6, 4, 0.6, 'Eligible Candidates (Trust ≥ 0.5)', color_input, 10)
draw_arrow(5, 7.6, 5, 6.9)

# 5. Five Metrics (side by side in 2 rows)
y_start = 4.8
metric_h = 1.4
metric_w = 1.8
gap = 0.2

# Row 1: Trust, Resource, Stability
draw_box(0.5, y_start, metric_w, metric_h, 
         'Trust (40%)\n0.5×Historical\n+0.5×Social', color_metric, 8.5, True)
draw_box(0.5 + metric_w + gap, y_start, metric_w, metric_h,
         'Resource (20%)\n(Bandwidth\n+Processing)/2', color_metric, 8.5, True)
draw_box(0.5 + 2*(metric_w + gap), y_start, metric_w, metric_h,
         'Stability (15%)\n(ClusterTime\n+ConnQuality)/2', color_metric, 8.5, True)

# Row 2: Behavior, Centrality
y_start2 = y_start - metric_h - 0.3
draw_box(0.5 + 1.5*gap, y_start2, metric_w, metric_h,
         'Behavior (15%)\n(Authenticity\n+Cooperation)/2', color_metric, 8.5, True)
draw_box(0.5 + 1.5*gap + metric_w + gap, y_start2, metric_w, metric_h,
         'Centrality (10%)\n1 - Distance/\nMaxRadius', color_metric, 8.5, True)

# Arrows from metrics to composite
draw_arrow(1.4, y_start2, 5, 2.5)
draw_arrow(3.3, y_start2, 5, 2.5)
draw_arrow(5.2, y_start2, 5, 2.5)
draw_arrow(3.3, y_start, 5, 2.5)
draw_arrow(7.1, y_start, 5, 2.5)

# 6. Composite Score
draw_box(2, 1.8, 6, 0.7, 
         'Composite Score = 0.40×T + 0.20×R + 0.15×S + 0.15×B + 0.10×C',
         color_composite, 9.5, True)
draw_arrow(5, 1.8, 5, 1.2)

# 7. Consensus Voting
draw_box(2.5, 0.5, 5, 0.7, '51% Majority Consensus Voting\n(Trust-weighted)', 
         color_consensus, 10)
draw_arrow(5, 0.5, 7.5, 0.15)

# 8. Output - New Leader
draw_box(7, -0.4, 2.5, 0.7, 'Elected Leader\n(100% transparent)', 
         color_output, 10, True)

# Add transparency note
ax.text(5, -1.2, '✓ All formulas visible | All weights explicit (40-20-15-15-10) | Complete logging',
        ha='center', fontsize=9, style='italic', 
        bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8))

plt.tight_layout()
plt.savefig('graph2_election_mechanism.png', dpi=300, bbox_inches='tight')
print('✓ Saved graph2_election_mechanism.png (300 DPI)')
print('  Shows: Transparent 5-metric election flowchart')
