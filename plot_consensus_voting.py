import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

# Simulating a consensus voting scenario
# Candidate votes accumulate as nodes cast trust-weighted votes

# Example: Top 3 candidates receiving votes
candidates = ['Vehicle v75\n(Winner)', 'Vehicle v42\n(Runner-up)', 'Vehicle v18']
vote_percentages = [55.2, 28.6, 16.2]  # Trust-weighted vote percentages (totals 100%)
colors = ['#2ecc71', '#3498db', '#95a5a6']  # Green for winner, blue for runner-up, gray for others

fig, ax = plt.subplots(figsize=(10, 6))

# Create horizontal bar chart
bars = ax.barh(candidates, vote_percentages, color=colors, edgecolor='black', linewidth=1.5)

# Add 51% threshold line
ax.axvline(x=51, color='red', linestyle='--', linewidth=2.5, zorder=5, label='51% Majority Threshold')

# Annotate each bar with vote percentage
for bar, pct in zip(bars, vote_percentages):
    width = bar.get_width()
    ax.text(width + 1.5, bar.get_y() + bar.get_height()/2,
            f'{pct}%',
            ha='left', va='center', fontsize=12, fontweight='bold')

# Add "ELECTED" annotation for winner
ax.text(vote_percentages[0] + 1.5, bars[0].get_y() + bars[0].get_height()/2 - 0.2,
        '✓ ELECTED',
        ha='left', va='center', fontsize=10, fontweight='bold', color='green',
        bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.7))

# Styling
ax.set_xlabel('Vote Weight (%)', fontsize=12, fontweight='bold')
ax.set_title('Cluster Head Election: Trust-Weighted Consensus Voting\n(Transparent 5-Metric Composite Score Based)', 
             fontsize=14, fontweight='bold', pad=20)
ax.set_xlim(0, 100)
ax.grid(axis='x', linestyle='--', alpha=0.3)
ax.legend(loc='lower right', fontsize=11)

# Add composite score info as text on the right side
info_text = 'Composite Scores:\n\nv75: 0.753\n  Trust: 0.996 (40%)\n  Resource: 0.836 (20%)\n  Stability: 0.000 (15%)\n  Behavior: 1.000 (15%)\n  Centrality: 0.379 (10%)\n\nv42: 0.621\nv18: 0.548'
ax.text(0.98, 0.50, info_text, transform=ax.transAxes,
        fontsize=9, va='center', ha='right',
        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.4, pad=0.8))

plt.tight_layout()
plt.savefig('graph_consensus_voting.png', dpi=300, bbox_inches='tight')
print('✓ Saved graph_consensus_voting.png (300 DPI)')
