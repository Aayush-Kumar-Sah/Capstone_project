# P2P VANET System

A decentralized vehicular network model based on a peer-to-peer (P2P) architecture. This system eliminates the need for traditional infrastructure components like base stations and roadside units, instead utilizing vehicles as relay nodes for direct information exchange and transmission.

## Key Features

- **P2P Architecture**: Vehicles communicate directly with each other without relying on central infrastructure.
- **Dynamic Relay Node Selection**: Uses degree distribution and hybrid consensus (Proof of Authority) for optimal relay node selection.
- **Enhanced Fault Tolerance**: Decentralized architecture prevents single points of failure.
- **Real-time Performance**: Efficient message propagation and network management.

## Project Structure

```
VANET_CAPStone/
├── src/
│   ├── __init__.py
│   ├── vehicle_node.py      # Core vehicle node implementation
│   ├── consensus.py         # PoA consensus mechanism
│   └── network_manager.py   # Network management and fault tolerance
├── tests/                   # Test files
└── requirements.txt         # Project dependencies
```

## Installation

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Components

### Vehicle Node
- Basic P2P node functionality
- Location and status tracking
- Connection management
- Relay score calculation

### Consensus Manager
- Proof of Authority (PoA) implementation
- Network graph management
- Node centrality calculation
- Relay node selection algorithm

### Network Manager
- Network health monitoring
- Fault detection and recovery
- Network statistics
- Dynamic relay node updates

## Development

To contribute to this project:

1. Clone the repository
2. Create a feature branch
3. Make your changes
4. Write/update tests
5. Submit a pull request

## Testing

Run tests using pytest:
```bash
pytest tests/
```