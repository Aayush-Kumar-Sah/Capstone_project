import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

# Create side-by-side comparison
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

# --- LEFT: Mahmood et al. (2-Metric System) ---
metrics_mahmood = ['Trust', 'Resources']
weights_mahmood = [60, 40]
colors_mahmood = ['#e74c3c', '#3498db']

bars1 = ax1.bar(metrics_mahmood, weights_mahmood, color=colors_mahmood, 
                edgecolor='black', linewidth=1.5, width=0.5)

# Annotate
for bar, weight in zip(bars1, weights_mahmood):
    height = bar.get_height()
    ax1.text(bar.get_x() + bar.get_width()/2., height,
            f'{weight}%',
            ha='center', va='bottom', fontsize=14, fontweight='bold')

ax1.set_ylabel('Weight (%)', fontsize=12, fontweight='bold')
ax1.set_title('Mahmood et al. [2019]\n2-Metric System (Black-box)', 
             fontsize=13, fontweight='bold', pad=15)
ax1.set_ylim(0, 70)
ax1.grid(axis='y', linestyle='--', alpha=0.3)
ax1.text(0.5, -0.12, 'Formula: 0.60×Trust + 0.40×Resources', 
        transform=ax1.transAxes, ha='center', va='top', fontsize=9,
        bbox=dict(boxstyle='round', facecolor='lightgray', alpha=0.5))

# Add "Limited Coverage" label
ax1.text(0.5, 0.85, '⚠ Limited Coverage\n(Only 2 dimensions)', 
        transform=ax1.transAxes, ha='center', va='top', fontsize=9,
        color='red', fontweight='bold',
        bbox=dict(boxstyle='round', facecolor='#ffcccc', alpha=0.7))

# --- RIGHT: Our 5-Metric Transparent System ---
metrics_ours = ['Trust\n(Security)', 'Resource\n(Capacity)', 'Stability\n(Longevity)', 
                'Behavior\n(Consistency)', 'Centrality\n(Geography)']
weights_ours = [40, 20, 15, 15, 10]
colors_ours = ['#e74c3c', '#3498db', '#2ecc71', '#f39c12', '#9b59b6']

bars2 = ax2.bar(metrics_ours, weights_ours, color=colors_ours, 
                edgecolor='black', linewidth=1.5, width=0.6)

# Annotate
for bar, weight in zip(bars2, weights_ours):
    height = bar.get_height()
    ax2.text(bar.get_x() + bar.get_width()/2., height,
            f'{weight}%',
            ha='center', va='bottom', fontsize=13, fontweight='bold')

ax2.set_ylabel('Weight (%)', fontsize=12, fontweight='bold')
ax2.set_title('Our Transparent 5-Metric System\n(All Formulas Explicit)', 
             fontsize=13, fontweight='bold', pad=15, color='green')
ax2.set_ylim(0, 70)
ax2.grid(axis='y', linestyle='--', alpha=0.3)
ax2.text(0.5, -0.12, 'Formula: 0.40×T + 0.20×R + 0.15×S + 0.15×B + 0.10×C', 
        transform=ax2.transAxes, ha='center', va='top', fontsize=9,
        bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.5))

# Add "Comprehensive + Transparent" label
ax2.text(0.5, 0.85, '✓ Comprehensive Coverage\n✓ Full Transparency (100%)', 
        transform=ax2.transAxes, ha='center', va='top', fontsize=9,
        color='darkgreen', fontweight='bold',
        bbox=dict(boxstyle='round', facecolor='#ccffcc', alpha=0.7))

# Main title
fig.suptitle('Trust Transparency Comparison: Benchmark vs. Our Approach', 
             fontsize=16, fontweight='bold', y=0.98)

plt.tight_layout(rect=[0, 0, 1, 0.96])
plt.savefig('graph1_trust_transparency.png', dpi=300, bbox_inches='tight')
print('✓ Saved graph1_trust_transparency.png (300 DPI)')
