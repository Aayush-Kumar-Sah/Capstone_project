#!/usr/bin/env python3
"""
Updated Election Mechanism Flowchart
Shows complete 5-metric transparent election process with:
- Sleeper agent detection
- PoA security layers
- Correct weights: 40-20-15-15-10
- Trust-weighted consensus voting
- Complete transparency
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle

fig, ax = plt.subplots(figsize=(12, 16))
ax.set_xlim(0, 12)
ax.set_ylim(0, 18)
ax.axis('off')

# Updated color scheme
color_trigger = '#e3f2fd'       # Light blue - input
color_security = '#ffebee'      # Light red - security checks
color_filter = '#fff3e0'        # Light orange - filtering
color_metric = '#e8f5e9'        # Light green - metric calculation
color_composite = '#c8e6c9'     # Green - composite score
color_voting = '#f3e5f5'        # Light purple - consensus
color_output = '#81c784'        # Strong green - result
color_ha = '#fff9c4'            # Light yellow - HA mechanism

def draw_box(x, y, w, h, text, color, fontsize=9, bold=False, border_width=2):
    """Draw a rounded box with text"""
    box = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.15", 
                          edgecolor='#1a237e', facecolor=color, linewidth=border_width)
    ax.add_patch(box)
    weight = 'bold' if bold else 'normal'
    ax.text(x + w/2, y + h/2, text, ha='center', va='center', 
            fontsize=fontsize, weight=weight, wrap=True)

def draw_arrow(x1, y1, x2, y2, style='->', width=2, color='#1a237e'):
    """Draw arrow between components"""
    arrow = FancyArrowPatch((x1, y1), (x2, y2), 
                           arrowstyle=style, mutation_scale=25, 
                           linewidth=width, color=color)
    ax.add_patch(arrow)

def draw_decision(x, y, w, h, text, fontsize=8):
    """Draw diamond-shaped decision box"""
    from matplotlib.patches import Polygon
    points = [(x + w/2, y + h),      # top
              (x + w, y + h/2),       # right
              (x + w/2, y),           # bottom
              (x, y + h/2)]           # left
    poly = Polygon(points, edgecolor='#1a237e', facecolor='#fffde7', linewidth=2)
    ax.add_patch(poly)
    ax.text(x + w/2, y + h/2, text, ha='center', va='center', 
            fontsize=fontsize, weight='bold')

# ============================================================================
# TITLE
# ============================================================================
ax.text(6, 17.3, 'Transparent 5-Metric Election System', 
        ha='center', fontsize=16, weight='bold', color='#1a237e')
ax.text(6, 16.8, 'Security-First Architecture (40-20-15-15-10)', 
        ha='center', fontsize=11, style='italic', color='#424242')

# ============================================================================
# 1. TRIGGER
# ============================================================================
draw_box(3.5, 15.8, 5, 0.7, 'Election Triggered for Cluster', 
         color_trigger, 11, True)
draw_arrow(6, 15.8, 6, 15.2)

# ============================================================================
# 2. SECURITY LAYER 1: Sleeper Detection
# ============================================================================
draw_box(2, 14.5, 8, 0.7, 
         '🔒 Security Layer 1: Sleeper Agent Detection\n' +
         'Trust drop >0.3 in <10s? Historical anomaly?', 
         color_security, 9, True)
draw_arrow(6, 14.5, 6, 13.8)

# ============================================================================
# 3. SECURITY LAYER 2: PoA Check
# ============================================================================
draw_box(2, 13.1, 8, 0.7, 
         '🔒 Security Layer 2: PoA Authority Consensus\n' +
         'Flagged by ≥30% authorities? Suspicion score >0.5?', 
         color_security, 9, True)
draw_arrow(6, 13.1, 6, 12.4)

# ============================================================================
# 4. CANDIDATE FILTERING
# ============================================================================
draw_box(3.5, 11.7, 5, 0.7, 
         'Eligible Candidates: Trust ≥ 0.5\nNot malicious | Not sleeper', 
         color_filter, 10, True)
draw_arrow(6, 11.7, 6, 10.8)

# ============================================================================
# 5. FIVE METRICS (Main Feature)
# ============================================================================
ax.text(6, 10.5, '📊 5-METRIC TRANSPARENT SCORING', 
        ha='center', fontsize=11, weight='bold', 
        bbox=dict(boxstyle='round', facecolor='#e0f7fa', edgecolor='#006064', linewidth=2))

# Metric dimensions
metric_w = 2.2
metric_h = 1.5
gap_x = 0.3
gap_y = 0.3

# Top row: Trust, Resource, Stability
y_row1 = 7.8

# Trust (40%) - Largest emphasis
draw_box(0.8, y_row1, metric_w, metric_h, 
         '🛡️ TRUST\n40%\n\n' +
         '0.5×Historical\n+0.5×Social\n\n' +
         'Security First',
         color_metric, 8.5, True, border_width=3)

# Resource (20%)
draw_box(0.8 + metric_w + gap_x, y_row1, metric_w, metric_h,
         '⚡ RESOURCE\n20%\n\n' +
         'Bandwidth\n+Processing\n\n' +
         'Prevent\nBottlenecks',
         color_metric, 8.5, True)

# Stability (15%)
draw_box(0.8 + 2*(metric_w + gap_x), y_row1, metric_w, metric_h,
         '🔄 STABILITY\n15%\n\n' +
         'ClusterTime\n+ConnQuality\n\n' +
         'Reduce\nRe-elections',
         color_metric, 8.5, True)

# Bottom row: Behavior, Centrality
y_row2 = 5.8
x_offset = 1.9

# Behavior (15%)
draw_box(x_offset, y_row2, metric_w, metric_h,
         '🎯 BEHAVIOR\n15%\n\n' +
         'Authenticity\n+Cooperation\n\n' +
         'Catch\nSleepers',
         color_metric, 8.5, True)

# Centrality (10%)
draw_box(x_offset + metric_w + gap_x, y_row2, metric_w, metric_h,
         '📍 CENTRALITY\n10%\n\n' +
         '1 - Distance/\nMaxRadius\n\n' +
         'Optimize\nRouting',
         color_metric, 8.5, True)

# Arrows from metrics to composite
# From top row
draw_arrow(1.9, y_row1, 6, 5.0, width=2)
draw_arrow(4.2, y_row1, 6, 5.0, width=2)
draw_arrow(6.5, y_row1, 6, 5.0, width=2)
# From bottom row
draw_arrow(3.0, y_row2, 6, 5.0, width=2)
draw_arrow(5.3, y_row2, 6, 5.0, width=2)

# ============================================================================
# 6. COMPOSITE SCORE CALCULATION
# ============================================================================
draw_box(1.5, 4.3, 9, 0.7, 
         'Composite Score = 0.40×Trust + 0.20×Resource + 0.15×Stability + 0.15×Behavior + 0.10×Centrality',
         color_composite, 10, True, border_width=3)
draw_arrow(6, 4.3, 6, 3.6)

# ============================================================================
# 7. CONSENSUS VOTING
# ============================================================================
draw_box(2.5, 2.9, 7, 0.7, 
         '🗳️ Trust-Weighted Raft Consensus Voting\n' +
         '51% Majority Required | Vote Weight = voter_trust / total_trust',
         color_voting, 9, True)
draw_arrow(6, 2.9, 6, 2.2)

# ============================================================================
# 8. WINNER SELECTION
# ============================================================================
draw_box(3.5, 1.5, 5, 0.7, 
         'Elected Leader (Highest Composite + 51% Votes)',
         color_output, 11, True, border_width=3)

# Branch for HA mechanism
draw_arrow(6, 1.5, 2, 0.7)
draw_arrow(6, 1.5, 10, 0.7)

# ============================================================================
# 9. HIGH-AVAILABILITY CO-LEADER
# ============================================================================
draw_box(0.5, 0, 3, 0.7, 
         '⭐ Co-Leader Elected\n(2nd highest score)',
         color_ha, 9, True)

# ============================================================================
# 10. OUTPUT TRANSPARENCY
# ============================================================================
draw_box(8.5, 0, 3, 0.7, 
         '✓ 100% Transparent\nAll formulas logged',
         color_output, 9, True)

# ============================================================================
# TRANSPARENCY BOX (Bottom)
# ============================================================================
transparency_text = (
    '✓ All formulas explicit | ✓ All weights justified (40-20-15-15-10) | '
    '✓ Complete election logs\n'
    '✓ 98% detection rate | ✓ 95% sleeper detection | ✓ 1.2ms election time | '
    '✓ 65% re-election reduction'
)
ax.text(6, -0.8, transparency_text,
        ha='center', fontsize=8.5, style='italic', 
        bbox=dict(boxstyle='round,pad=0.5', facecolor='#fff9c4', 
                 edgecolor='#f57f17', linewidth=2, alpha=0.9))

# ============================================================================
# LEGEND
# ============================================================================
legend_y = -1.6
legend_elements = [
    mpatches.Rectangle((0, 0), 1, 1, fc=color_security, ec='black', label='Security Layers'),
    mpatches.Rectangle((0, 0), 1, 1, fc=color_metric, ec='black', label='5 Metrics'),
    mpatches.Rectangle((0, 0), 1, 1, fc=color_composite, ec='black', label='Composite Score'),
    mpatches.Rectangle((0, 0), 1, 1, fc=color_voting, ec='black', label='Consensus Voting'),
    mpatches.Rectangle((0, 0), 1, 1, fc=color_output, ec='black', label='Election Result')
]
ax.legend(handles=legend_elements, loc='upper center', 
         bbox_to_anchor=(0.5, -0.08), ncol=5, frameon=True, 
         fontsize=8, framealpha=0.9, edgecolor='#1a237e', fancybox=True)

plt.tight_layout()
plt.savefig('graph2_election_mechanism_UPDATED.png', dpi=300, bbox_inches='tight', 
            facecolor='white', edgecolor='none')
print('✅ Saved: graph2_election_mechanism_UPDATED.png (300 DPI)')
print('   📊 Shows: Complete 5-metric transparent election process')
print('   🔒 Security: Sleeper detection + PoA consensus')
print('   ⚖️  Weights: Trust 40%, Resource 20%, Stability 15%, Behavior 15%, Centrality 10%')
print('   ✓  Features: HA co-leader, trust-weighted voting, 100% transparency')
