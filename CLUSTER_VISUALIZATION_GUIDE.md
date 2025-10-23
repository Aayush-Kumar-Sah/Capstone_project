# VANET Cluster Visualization Guide

## Overview
The cluster visualization system provides comprehensive visual analysis of VANET clustering behavior, including trust scores, cluster formation, and network topology.

## Features ✅

### 1. Network Topology Visualization
- **Cluster member positions** - Color-coded by cluster
- **Cluster heads** - Highlighted with star markers
- **Trust scores overlay** - Displayed on each vehicle
  - Green: High trust (≥0.7)
  - Orange: Medium trust (0.4-0.7)
  - Red: Low trust (<0.4)
- **Membership lines** - Connecting members to cluster heads
- **Unclustered vehicles** - Shown in gray

### 2. Cluster Timeline
- Cluster count over time
- Formation events (green markers)
- Dissolution events (red markers)
- Statistical summaries (avg, max, min)

### 3. Trust Distribution
- Trust score histograms at multiple time points
- Trust evolution for sample vehicles
- Color-coded trust levels

### 4. Performance Metrics Dashboard
- Message statistics (sent/received)
- Clustering events (formations, joins, leaves, re-elections)
- Cluster size distribution
- Comprehensive simulation summary

## Quick Start

### Basic Usage
```bash
# Run with default settings (60s, 45 vehicles)
python3 cluster_visualization_demo.py

# Custom duration and vehicle count
python3 cluster_visualization_demo.py --duration 30 --vehicles 30

# Save plots to files
python3 cluster_visualization_demo.py --save-plots

# Try different algorithms
python3 cluster_visualization_demo.py --algorithm direction_based
python3 cluster_visualization_demo.py --algorithm kmeans
python3 cluster_visualization_demo.py --algorithm dbscan
```

### Command-Line Options
```
--duration SECONDS    Simulation duration (default: 60)
--algorithm ALGO      Clustering algorithm: mobility_based, direction_based, kmeans, dbscan
--vehicles NUM        Number of vehicles (default: 45)
--save-plots         Save plots to PNG files instead of displaying
--animate            Enable real-time animation (requires display)
```

## Output Files

### Generated Plots
1. **cluster_topology_{ALGORITHM}.png** (540KB)
   - Network snapshot at mid-simulation
   - Cluster boundaries and memberships
   - Trust scores on vehicles

2. **cluster_timeline_{ALGORITHM}.png** (123KB)
   - Cluster count over time
   - Formation/dissolution events
   - Statistical metrics

3. **trust_distribution_{ALGORITHM}.png** (171KB)
   - Trust histograms at different times
   - Trust evolution trends
   - Sample vehicle trust scores

4. **performance_metrics_{ALGORITHM}.png** (317KB)
   - Message statistics
   - Clustering events
   - Cluster size distribution
   - Simulation summary

### Results JSON
- **cluster_visualization_results_{timestamp}.json**
  - Metadata (algorithm, duration, vehicles)
  - Application statistics
  - Summary metrics (avg clusters, events, etc.)

## Example Runs

### Test 1: Mobility-Based Clustering
```bash
python3 cluster_visualization_demo.py --duration 40 --vehicles 35 --save-plots --algorithm mobility_based
```
**Results:**
- Duration: 40s
- Vehicles: 35
- Clusters: 9-11 (dynamic)
- Trust evaluations: Continuous
- Plots saved: ✅ All 4 plots

### Test 2: Direction-Based Clustering  
```bash
python3 cluster_visualization_demo.py --duration 30 --vehicles 30 --save-plots --algorithm direction_based
```
**Results:**
- Duration: 30s
- Vehicles: 30
- Clusters: 7-9 (separated by direction)
- Clear traffic direction separation
- Plots saved: ✅ All 4 plots

### Test 3: K-Means Clustering
```bash
python3 cluster_visualization_demo.py --duration 30 --vehicles 25 --save-plots --algorithm kmeans
```
**Results:**
- Duration: 30s  
- Vehicles: 25
- Clusters: 5-7 (balanced distribution)
- Stable cluster sizes
- Plots saved: ✅ All 4 plots

## Visualization Features

### Trust-Aware Elements
1. **Color-Coded Trust Scores**
   - Each vehicle shows its trust score
   - Colors indicate trust level
   - Helps identify malicious nodes

2. **Trust-Based Head Election**
   - Cluster heads must meet trust threshold (≥0.6)
   - Trust score displayed prominently
   - Head changes tracked when trust drops

3. **Trust Evolution**
   - Track trust changes over time
   - Identify degrading trust patterns
   - Visualize trust recovery

### Clustering Metrics
- **Formation Rate**: How often clusters form
- **Dissolution Rate**: How often clusters dissolve
- **Head Changes**: Frequency of re-elections
- **Cluster Stability**: Average cluster lifetime
- **Membership Dynamics**: Join/leave patterns

## Advanced Usage

### Customizing Visualization
Edit `cluster_visualization_demo.py` to customize:
- Color palette (line 83)
- Plot sizes (line 255)
- Trust thresholds (line 308)
- Sampling rates (line 144)

### Adding Custom Metrics
Add to `_collect_frame_data()` method:
```python
# Collect custom data
self.history['custom_metric'].append(your_calculation)
```

Then plot in `_plot_performance_metrics()`:
```python
ax.plot(timestamps, custom_metric, label='Custom Metric')
```

### Exporting Data
Results are automatically saved to JSON. Access via:
```python
import json
with open('cluster_visualization_results_{timestamp}.json') as f:
    data = json.load(f)
print(data['summary'])
```

## Troubleshooting

### Issue: No display available
**Solution**: Use `--save-plots` flag to save to files instead
```bash
python3 cluster_visualization_demo.py --save-plots
```

### Issue: ModuleNotFoundError: matplotlib
**Solution**: Install matplotlib
```bash
pip3 install matplotlib numpy --break-system-packages
```

### Issue: Plots look distorted
**Solution**: Increase figure size in code or use higher DPI
```python
# In cluster_visualization_demo.py, line 255
fig_topo = plt.figure(figsize=(20, 12))  # Increase from (16, 10)
```

### Issue: Simulation too slow
**Solution**: Reduce duration or vehicle count
```bash
python3 cluster_visualization_demo.py --duration 20 --vehicles 20
```

## Performance Benchmarks

### Test Configuration
- **System**: Ubuntu 24.10, Python 3.12
- **Duration**: 40 seconds
- **Vehicles**: 35
- **Algorithm**: Mobility-based

### Results
- **Simulation Time**: ~5 seconds (8x real-time)
- **Plot Generation**: ~3 seconds
- **Total Runtime**: ~8 seconds
- **Memory Usage**: ~150MB
- **File Sizes**: 
  - Topology: 540KB
  - Timeline: 123KB
  - Trust: 171KB
  - Metrics: 317KB

## Integration with Main System

The visualization can be integrated into the main VANET application:

```python
from src.custom_vanet_appl import CustomVANETApplication
from cluster_visualization_demo import ClusterVisualizationDemo

# Create application
app = CustomVANETApplication()
app.initialize_consensus("node1", "hybrid", ["auth1", "auth2", "auth3"])

# Create visualization demo
demo = ClusterVisualizationDemo(
    algorithm=ClusteringAlgorithm.MOBILITY_BASED,
    duration=60,
    num_vehicles=45
)

# Run simulation with visualization
demo.app = app  # Use your existing app
demo.run_simulation()
demo.create_visualizations(save_plots=True)
```

## Future Enhancements

### Planned Features
- [ ] Real-time animation during simulation
- [ ] 3D network topology view
- [ ] Interactive plot controls
- [ ] Video export of cluster evolution
- [ ] Comparison plots for multiple algorithms
- [ ] Heat maps for trust distribution
- [ ] Attack scenario visualization
- [ ] Performance profiling overlay

## Contributing

To add new visualizations:
1. Add data collection in `_collect_frame_data()`
2. Create plot method (e.g., `_plot_your_metric()`)
3. Call from `create_visualizations()`
4. Update documentation

## Summary

✅ **Implemented**: Complete cluster visualization system
✅ **Features**: 4 comprehensive plot types
✅ **Trust Integration**: Trust scores overlay on all plots
✅ **Performance**: Fast and efficient
✅ **Output**: High-quality PNG files + JSON data
✅ **Algorithms**: All 4 clustering algorithms supported

**Status**: READY FOR DEMONSTRATION ✨

---

*Last Updated: October 23, 2025*
*Version: 1.0.0*
