import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

# Our 5-metric transparent system
metrics = ['Trust\n(Security)', 'Resource\n(Capacity)', 'Stability\n(Longevity)', 'Behavior\n(Consistency)', 'Centrality\n(Geography)']
weights = [40, 20, 15, 15, 10]
colors = ['#e74c3c', '#3498db', '#2ecc71', '#f39c12', '#9b59b6']

fig, ax = plt.subplots(figsize=(10, 6))
bars = ax.bar(metrics, weights, color=colors, edgecolor='black', linewidth=1.5, width=0.6)

# Annotate each bar with weight percentage
for bar, weight in zip(bars, weights):
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., height,
            f'{weight}%',
            ha='center', va='bottom', fontsize=14, fontweight='bold')

# Add formulas as text below
ax.text(0.5, -0.15, 
        'Composite Score = 0.40×Trust + 0.20×Resource + 0.15×Stability + 0.15×Behavior + 0.10×Centrality',
        transform=ax.transAxes, ha='center', va='top', fontsize=10, 
        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))

ax.set_ylabel('Weight (%)', fontsize=12, fontweight='bold')
ax.set_title('Our Transparent 5-Metric Election System\n(All Formulas Explicitly Defined)', 
             fontsize=14, fontweight='bold', pad=20)
ax.set_ylim(0, 50)
ax.grid(axis='y', linestyle='--', alpha=0.3)

# Add total = 100% annotation
ax.text(0.95, 0.95, 'Total: 100%', transform=ax.transAxes,
        fontsize=12, fontweight='bold', ha='right', va='top',
        bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.5))

plt.tight_layout()
plt.savefig('graph2_election_mechanism.png', dpi=300, bbox_inches='tight')
print('✓ Saved graph2_election_mechanism.png (300 DPI)')
