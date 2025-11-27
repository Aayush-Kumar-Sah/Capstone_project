#!/usr/bin/env python3
"""
Complete PoA Detection Flowchart with Sleeper Agent Detection
Shows the two-phase detection system:
1. Sleeper agent pattern detection (trust spike analysis)
2. PoA authority consensus voting
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle, Wedge
import matplotlib.patches as mpatches

fig, ax = plt.subplots(figsize=(14, 16))
ax.set_xlim(0, 14)
ax.set_ylim(0, 18)
ax.axis('off')

# Colors
color_trigger = '#e3f2fd'
color_sleeper = '#ffcdd2'      # Light red - sleeper detection
color_poa = '#fff3e0'          # Light orange - PoA process
color_voting = '#e8f5e9'       # Light green - voting
color_action = '#f3e5f5'       # Light purple - actions
color_result = '#c8e6c9'       # Green - results
color_stats = '#fff9c4'        # Yellow - statistics

def draw_box(x, y, w, h, text, color, fontsize=9, bold=False, border=2):
    box = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.15", 
                          edgecolor='#1a237e', facecolor=color, linewidth=border)
    ax.add_patch(box)
    weight = 'bold' if bold else 'normal'
    ax.text(x + w/2, y + h/2, text, ha='center', va='center', 
            fontsize=fontsize, weight=weight, wrap=True)

def draw_arrow(x1, y1, x2, y2, style='->', width=2.5, color='#1a237e'):
    arrow = FancyArrowPatch((x1, y1), (x2, y2), 
                           arrowstyle=style, mutation_scale=25, 
                           linewidth=width, color=color)
    ax.add_patch(arrow)

def draw_decision(x, y, size, text, fontsize=8):
    from matplotlib.patches import Polygon
    points = [(x + size/2, y + size),    # top
              (x + size, y + size/2),    # right
              (x + size/2, y),           # bottom
              (x, y + size/2)]           # left
    poly = Polygon(points, edgecolor='#1a237e', facecolor='#fffde7', linewidth=2.5)
    ax.add_patch(poly)
    ax.text(x + size/2, y + size/2, text, ha='center', va='center', 
            fontsize=fontsize, weight='bold')

# ============================================================================
# TITLE
# ============================================================================
ax.text(7, 17.3, 'PoA Malicious Detection System', 
        ha='center', fontsize=16, weight='bold', color='#1a237e')
ax.text(7, 16.7, 'Dual-Phase: Sleeper Detection + Authority Consensus', 
        ha='center', fontsize=11, style='italic', color='#424242')

# ============================================================================
# TRIGGER
# ============================================================================
draw_box(4.5, 15.8, 5, 0.6, 'Security Monitoring Cycle (Every 1s)', 
         color_trigger, 10, True)
draw_arrow(7, 15.8, 7, 15.2)

# ============================================================================
# PHASE 1: SLEEPER AGENT DETECTION
# ============================================================================
ax.text(7, 15, '🕵️ PHASE 1: SLEEPER AGENT DETECTION', 
        ha='center', fontsize=11, weight='bold',
        bbox=dict(boxstyle='round', facecolor=color_sleeper, 
                 edgecolor='#b71c1c', linewidth=2.5))

draw_box(2.5, 13.6, 9, 0.7, 
         'Track Historical Trust Scores (Last 10 values with timestamps)',
         color_sleeper, 9)
draw_arrow(7, 13.6, 7, 12.9)

# Sleeper detection criteria
draw_box(3, 12.2, 8, 0.7,
         'Calculate: Δtrust = current_trust - previous_trust\n' +
         'Time window: Δt < 10 seconds',
         color_sleeper, 8.5)
draw_arrow(7, 12.2, 7, 11.4)

# Decision: Sleeper pattern?
draw_decision(5.5, 10.4, 3, 
              'Trust drop\n>0.3 in\n<10s?\nAND\nPreviously\n>0.8?',
              8)

# YES branch (Sleeper detected)
draw_arrow(8.5, 11.9, 11, 11.9, width=2, color='#d32f2f')
ax.text(9.7, 12.2, 'YES', fontsize=9, weight='bold', color='#d32f2f')

draw_box(10, 11.4, 3, 1.0,
         '🚨 SLEEPER\nACTIVATED\n\n' +
         'Immediate Flag\nSkip to Voting',
         '#ffcdd2', 9, True, border=3)
draw_arrow(11.5, 11.4, 11.5, 9.5)

# NO branch (Continue normal detection)
draw_arrow(7, 10.4, 7, 9.8, width=2)
ax.text(7.3, 10, 'NO', fontsize=9, weight='bold')

# ============================================================================
# PHASE 2: POA AUTHORITY IDENTIFICATION
# ============================================================================
ax.text(7, 9.5, '👮 PHASE 2: PoA AUTHORITY CONSENSUS', 
        ha='center', fontsize=11, weight='bold',
        bbox=dict(boxstyle='round', facecolor=color_poa, 
                 edgecolor='#e65100', linewidth=2.5))

draw_box(3.5, 8.6, 7, 0.6,
         'Identify Authorities: Trust ≥ 0.8 (High-trust validators)',
         color_poa, 9, True)
draw_arrow(7, 8.6, 7, 8.0)

# ============================================================================
# AUTHORITY MONITORING LOOP
# ============================================================================
draw_box(3, 7.3, 8, 0.7,
         'FOR EACH Authority: Monitor cluster members + neighbors',
         color_poa, 9)
draw_arrow(7, 7.3, 7, 6.5)

# Suspicion score calculation
draw_box(1.5, 5.2, 11, 1.3,
         '📊 Calculate Suspicion Score for Each Monitored Node:\n' +
         '• Trust < 0.4? → +0.3  |  • Known malicious? → +0.5  |  • Speed > 75mph? → +0.2\n' +
         '• Message spam >100? → +0.2  |  • Erratic behavior? → +0.3  |  • Failed verification? → +0.4\n' +
         '• Sleeper detected? → +0.6',
         color_poa, 8.5)
draw_arrow(7, 5.2, 7, 4.4)

# Decision: Suspicion threshold
draw_decision(5.5, 3.4, 3,
              'Suspicion\nScore\n>0.5?',
              9)

# NO branch - safe node
draw_arrow(5.5, 4.9, 3, 4.9, width=2)
ax.text(4, 5.1, 'NO', fontsize=9, weight='bold')
draw_box(1, 4.4, 4, 0.5, '✓ Node Safe - Skip', '#c8e6c9', 9)

# YES branch - vote against
draw_arrow(8.5, 4.9, 11, 4.9, width=2, color='#d32f2f')
ax.text(9.7, 5.1, 'YES', fontsize=9, weight='bold', color='#d32f2f')
draw_box(10, 4.4, 3, 0.5, '⚠️ Authority Votes\nAGAINST node', '#ffcdd2', 8.5, True)

# Convergence arrows
draw_arrow(2.5, 4.4, 2.5, 3.2)
draw_arrow(11.5, 4.4, 11.5, 3.2)
draw_arrow(2.5, 3.2, 6, 2.8)
draw_arrow(11.5, 3.2, 8, 2.8)
draw_arrow(7, 3.4, 7, 2.8)

# ============================================================================
# PHASE 3: CONSENSUS EVALUATION
# ============================================================================
ax.text(7, 2.5, '🗳️ PHASE 3: CONSENSUS EVALUATION', 
        ha='center', fontsize=10, weight='bold',
        bbox=dict(boxstyle='round', facecolor=color_voting, 
                 edgecolor='#2e7d32', linewidth=2))

draw_box(3, 1.6, 8, 0.6,
         'Count votes: threshold = 30% of cluster authorities (min 2 votes)',
         color_voting, 9)
draw_arrow(7, 1.6, 7, 0.9)

# Decision: Consensus reached?
draw_decision(5.5, -0.1, 3,
              'Votes ≥\nThreshold?',
              9)

# NO branch - insufficient consensus
draw_arrow(5.5, 1.4, 2, 1.4, width=2)
ax.text(3.5, 1.6, 'NO', fontsize=9, weight='bold')
draw_box(0.2, 0.9, 3.6, 0.5, 'No Action - Insufficient Consensus', '#fff9c4', 8.5)

# YES branch - flag as malicious
draw_arrow(8.5, 1.4, 11, 1.4, width=2, color='#d32f2f')
ax.text(9.7, 1.6, 'YES', fontsize=9, weight='bold', color='#d32f2f')

# ============================================================================
# ACTIONS ON MALICIOUS NODE
# ============================================================================
draw_box(10, 0.4, 3, 0.5, 
         '🚨 FLAG AS MALICIOUS', 
         '#ef5350', 10, True, border=3)
draw_arrow(11.5, 0.4, 11.5, -0.5)

draw_box(9.5, -1.5, 4, 0.7,
         'Apply Trust Penalty:\ntrust ×= 0.7 (30% reduction)',
         color_action, 9)
draw_arrow(11.5, -1.5, 11.5, -2.3)

# Decision: Is cluster head?
draw_decision(10, -3.3, 3,
              'Is Cluster\nHead?',
              9)

# NO branch
draw_arrow(10, -1.8, 8, -1.8, width=2)
ax.text(8.8, -1.6, 'NO', fontsize=9, weight='bold')
draw_box(5.5, -2.3, 5, 0.5, 
         '👁️ Monitor for Re-offense', 
         color_result, 9)

# YES branch - emergency removal
draw_arrow(13, -1.8, 13, -3.8, width=2, color='#d32f2f')
ax.text(13.3, -2.5, 'YES', fontsize=9, weight='bold', color='#d32f2f')
draw_box(12.2, -4.3, 1.6, 0.5, 
         '⚡ REMOVE\nLEADER', 
         '#ff5252', 8.5, True, border=3)
draw_arrow(13, -4.3, 13, -5.0)
draw_box(12.2, -5.5, 1.6, 0.5, 
         'Emergency\nRe-election', 
         color_action, 8)

# Convergence
draw_arrow(8, -2.3, 8, -5.5)
draw_arrow(11.5, -3.3, 11.5, -5.5)
draw_arrow(13, -5.5, 11.5, -6.0)
draw_arrow(8, -5.5, 11.5, -6.0)
draw_arrow(11.5, -6.0, 11.5, -6.8)

# ============================================================================
# FINAL RESULT
# ============================================================================
draw_box(9, -7.3, 5, 0.5,
         '✓ Detection Complete | Statistics Updated',
         color_result, 10, True, border=2.5)

# ============================================================================
# PERFORMANCE STATISTICS BOX
# ============================================================================
stats_text = (
    '📊 DETECTION PERFORMANCE METRICS 📊\n'
    '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n'
    '✓ Overall Detection: 98.03% (2,794/2,850)  |  ✓ Sleeper Detection: 95.00% (282/300)\n'
    '✓ False Positive Rate: 0.40% (78/19,650)  |  ✓ Precision: 97.28%  |  ✓ F1 Score: 97.65%\n'
    '⏱️ Detection Time: Random 3.2s avg | Sleepers 27.8s avg (after activation)'
)
ax.text(7, -8.5, stats_text,
        ha='center', fontsize=8, family='monospace',
        bbox=dict(boxstyle='round,pad=0.6', facecolor=color_stats, 
                 edgecolor='#f57f17', linewidth=2.5, alpha=0.95))

# ============================================================================
# LEGEND
# ============================================================================
legend_elements = [
    mpatches.Rectangle((0, 0), 1, 1, fc=color_sleeper, ec='black', label='Sleeper Detection'),
    mpatches.Rectangle((0, 0), 1, 1, fc=color_poa, ec='black', label='PoA Process'),
    mpatches.Rectangle((0, 0), 1, 1, fc=color_voting, ec='black', label='Consensus'),
    mpatches.Rectangle((0, 0), 1, 1, fc=color_action, ec='black', label='Actions'),
    mpatches.Rectangle((0, 0), 1, 1, fc=color_result, ec='black', label='Results')
]
ax.legend(handles=legend_elements, loc='upper center', 
         bbox_to_anchor=(0.5, -0.52), ncol=5, frameon=True, 
         fontsize=9, framealpha=0.9, edgecolor='#1a237e', fancybox=True)

plt.tight_layout()
plt.savefig('graph_poa_detection_flowchart.png', dpi=300, bbox_inches='tight',
            facecolor='white', edgecolor='none')
print('✅ Saved: graph_poa_detection_flowchart.png (300 DPI)')
print('   🕵️  Shows: Dual-phase detection (Sleeper + PoA)')
print('   📊 Performance: 98% overall, 95% sleeper detection')
print('   ⏱️  Speed: 3.2s avg (random), 27.8s (sleepers after activation)')
