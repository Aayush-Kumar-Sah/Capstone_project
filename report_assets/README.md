# VANET Simulation Report Assets

## 📦 Package Contents

### 1. Code Snippets (`code_snippets/`)
Extracted implementation code for report documentation:
- ✅ Multi-Metric Raft Election (`multi_metric_raft_election.py`)
- ✅ Co-Leader Succession (`co_leader_succession.py`)
- ✅ PoA Malicious Detection (`poa_malicious_detection.py`)
- ✅ Relay Node Election (`relay_node_election.py`)
- ✅ Boundary Node Election (`boundary_node_election.py`)
- ✅ V2V Message Broadcast (`v2v_message_broadcast.py`)
- ✅ Collision Detection (`collision_detection.py`)
- ✅ Cluster Merging Algorithm (`cluster_merging.py`)

### 2. Visualizations (`visualizations/`)
High-quality PNG images (200 DPI) showing system in action:
- ✅ Initial Network State (`initial_network.png`)
- ✅ Cluster Formation (`cluster_formation.png`)
- ✅ Leader Election (`leader_election.png`)
- ✅ Relay & Boundary Nodes (`relay_boundary.png`)
- ✅ Malicious Detection (`malicious_detection.png`)
- ✅ V2V Communication (`v2v_communication.png`)

### 3. Documentation
- ✅ `CODE_SNIPPETS.md` - Code implementation details with previews
- ✅ This README - Usage guide

## 🎯 How to Use in Your Report

### For Code Implementation Sections:
1. Open the relevant `.py` file from `code_snippets/`
2. Copy the code (already formatted with comments)
3. Insert into your report with syntax highlighting

### For Visual Demonstrations:
1. Use PNG images from `visualizations/`
2. Reference the captions provided in your donetask.txt
3. Images are 200 DPI - suitable for print and digital

### Recommended Report Structure:
1. **Introduction** → Use `initial_network.png`
2. **Clustering Algorithm** → Use `cluster_formation.png` + `cluster_merging.py`
3. **Leader Election** → Use `leader_election.png` + `multi_metric_raft_election.py`
4. **Security (PoA)** → Use `malicious_detection.png` + `poa_malicious_detection.py`
5. **Multi-Hop Communication** → Use `relay_boundary.png` + relay/boundary code
6. **V2V Safety** → Use `v2v_communication.png` + `collision_detection.py`

## 📊 System Statistics

Based on latest simulation run:
- **Total Vehicles:** 150 (cars, trucks, emergency)
- **Network:** 11×11 grid, 350 roads, 97 intersections
- **Clusters:** 3-12 (dynamic, merged)
- **Leader Elections:** 104-331 (failure-driven)
- **Malicious Detection:** 100% (13-18 nodes detected)
- **V2V Messages:** 11,000-19,000 per 120s simulation
- **Communication:** Multi-hop relay + inter-cluster boundary forwarding

## 🔧 Regenerating Assets

If you make code changes and need to regenerate:

```bash
# Run simulation to generate new data
python3 city_traffic_simulator.py

# Generate all report assets
python3 scripts/generate_report_assets.py

# Or run individually:
python3 scripts/generate_code_snippets.py
python3 scripts/capture_visualizations.py
```

---

*Generated automatically for VANET Capstone Project Report*
*Date: November 4, 2025*
