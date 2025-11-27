import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Assumptions (documented):
# - Baseline: all leader changes trigger full re-elections (total_leader_changes)
# - Our model: co-leader succession reduces full re-elections by ~65%
# These numbers are inferred from manuscript text; change values below if you have exact counts.

baseline_full = 523
reduction_pct = 0.65
model_full = int(round(baseline_full * (1 - reduction_pct)))
co_leader_promotions = baseline_full - model_full

labels = ['Baseline (Full Re-elections)', 'Our Model (Full Re-elections)', 'Our Model (Co-leader promotions)']
values = [baseline_full, model_full, co_leader_promotions]
colors = ['#d62728', '#1f77b4', '#2ca02c']

fig, ax = plt.subplots(figsize=(8,5))
bars = ax.bar(labels, values, color=colors, edgecolor='black')

# Annotate values
for bar in bars:
    h = bar.get_height()
    ax.annotate(f'{h}', xy=(bar.get_x() + bar.get_width() / 2, h),
                xytext=(0, 6), textcoords='offset points', ha='center', va='bottom', fontsize=10)

ax.set_title('Full Re-Elections: Baseline vs Our Model with Co-leader Succession', fontsize=12)
ax.set_ylabel('Count (number of events)')
ax.set_ylim(0, max(values) * 1.2)
ax.grid(axis='y', linestyle='--', linewidth=0.5, alpha=0.7)

plt.tight_layout()
# Save high-resolution PNG for publication
plt.savefig('graph_re_elections.png', dpi=300)
print('Saved graph_re_elections.png')
