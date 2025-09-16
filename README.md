# Decentralized VANET System with P2P Architecture

A decentralized vehicular network model based on peer-to-peer (P2P) architecture, eliminating the need for traditional infrastructure components like base stations and roadside units. Vehicles act as relay nodes, directly exchanging and transmitting information.

## Key Features

### P2P Architecture
- Direct vehicle-to-vehicle (V2V) communication
- Distributed network topology
- Autonomous node operations

### Dynamic Node Selection
- **Cluster Formation**: Adaptive clustering based on:
  - Relative mobility
  - Direction similarity
  - Signal strength
  - Node stability

- **Node Roles**:
  - Cluster Heads: Manage local cluster communication
  - Relay Nodes: Handle inter-cluster message forwarding
  - Boundary Nodes: Connect different clusters
  - Regular Nodes: Participate in cluster activities

### Consensus Mechanism
- Hybrid consensus algorithm including Proof of Authority (PoA)
- Dynamic leader election based on:
  - Connectivity degree (25%)
  - Relative mobility (25%)
  - Signal strength (20%)
  - Battery level (15%)
  - Historical stability (15%)

### Enhanced Fault Tolerance
- Decentralized architecture prevents single points of failure
- Automatic cluster reorganization
- Dynamic relay node selection
- Continuous network health monitoring

## Project Structure

```
VANET_CAPStone/
├── src/
│   ├── __init__.py
│   ├── vehicle_node.py      # Vehicle node implementation
│   ├── clustering.py        # Clustering algorithm
│   ├── consensus.py         # PoA consensus mechanism
│   ├── network_manager.py   # Network management
│   ├── custom_vanet_appl.py # VANET application layer
│   ├── simulation_bridge.py # OMNeT++/SUMO integration
│   └── visualization.py     # Cluster visualization
├── simulations/
│   ├── config.sumo.cfg     # SUMO configuration
│   ├── omnetpp.ini         # OMNeT++ configuration
│   ├── vanet.net.xml       # Road network definition
│   ├── vanet.rou.xml       # Vehicle routes
│   ├── vanet.add.xml       # Additional SUMO config
│   └── VANETScenario.ned   # Network description
├── tests/                   # Test files
└── requirements.txt         # Project dependencies
```

## Technologies Used

- **OMNeT++**: Network simulation
- **SUMO**: Traffic simulation
- **Veins**: Vehicle network simulation framework
- **Python**: Core implementation
- Libraries:
  - networkx: Network analysis
  - numpy: Numerical computations
  - matplotlib: Visualization
  - traci: Traffic Control Interface

## Setup and Installation

1. Prerequisites:
   ```bash
   # Required software
   - OMNeT++ (6.0 or later)
   - SUMO (1.8.0 or later)
   - Veins (5.2 or later)
   - Python 3.8+
   ```

2. Environment Setup:
   ```bash
   # Clone the repository
   git clone https://github.com/Aayush-Kumar-Sah/Capstone_project.git
   cd VANET_CAPStone

   # Create and activate virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate

   # Install dependencies
   pip install -r requirements.txt
   ```

3. Configure SUMO:
   ```bash
   # Set SUMO_HOME environment variable
   export SUMO_HOME=/path/to/sumo
   ```

## Running the Simulation

1. Start the simulation:
   ```bash
   ./run_simulation.sh
   ```

2. The visualization will show:
   - Red stars (*): Cluster heads
   - Green squares: Relay nodes
   - Blue triangles: Boundary nodes
   - Gray circles: Regular members
   - Dotted circles: Cluster boundaries
   - Thin lines: Node connections

## Simulation Parameters

Key parameters can be adjusted in `simulations/omnetpp.ini`:
- Playground size: 2500m x 2500m
- Cluster update interval: 5s
- Maximum cluster radius: 300m
- Beacon interval: 1s
- IEEE 802.11p parameters configured for VANET communication

## Development

To contribute to this project:

1. Clone the repository
2. Create a feature branch (`git checkout -b feature/NewFeature`)
3. Make your changes
4. Write/update tests
5. Submit a pull request

## Testing

Run tests using pytest:
```bash
pytest tests/
```