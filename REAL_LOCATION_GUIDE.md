# 🌍 Real-World Location-Based VANET Simulation Guide

## Overview

This simulator can use **real street networks from anywhere in the world** using OpenStreetMap data!

---

## 🚀 Quick Start

### Using Preset Locations

```bash
# Times Square, New York
python3 real_world_simulator.py --location times_square --vehicles 20 --duration 40

# Connaught Place, New Delhi  
python3 real_world_simulator.py --location connaught_place --vehicles 25 --duration 50
```

### Using Any Real Location (requires OSMnx)

```bash
# Install OSMnx (if not already installed)
pip3 install osmnx folium geopandas

# Download and simulate any location
python3 real_world_simulator.py --location "Shibuya Crossing, Tokyo, Japan" --vehicles 30

python3 real_world_simulator.py --location "Times Square, Manhattan, New York, USA" --vehicles 25

python3 real_world_simulator.py --location "Piccadilly Circus, London, UK" --vehicles 20

python3 real_world_simulator.py --location "Champs-Élysées, Paris, France" --vehicles 30

python3 real_world_simulator.py --location "India Gate, New Delhi, India" --vehicles 25
```

---

## 📍 Supported Locations

### Preset Locations (No OSMnx needed)
- `times_square` - Times Square, New York
- `connaught_place` - Connaught Place, New Delhi

### Any Location Worldwide (with OSMnx)
You can use any location that OpenStreetMap has data for!

#### Famous Intersections:
- "Shibuya Crossing, Tokyo, Japan"
- "Times Square, Manhattan, New York, USA"
- "Piccadilly Circus, London, UK"
- "Champs-Élysées, Paris, France"
- "La Rambla, Barcelona, Spain"

#### City Centers:
- "Downtown Los Angeles, USA"
- "Central Mumbai, India"
- "City Centre, Singapore"
- "Downtown Toronto, Canada"

#### Specific Addresses:
- "Stanford University, California, USA"
- "MIT Campus, Cambridge, Massachusetts, USA"
- "IIT Delhi, New Delhi, India"

---

## 🎬 Viewing the Simulation

After running the simulation:

```bash
# Make sure HTTP server is running
python3 -m http.server 8080 &

# Open the viewer
# Then navigate to: http://localhost:8080/real_location_viewer.html
```

Or open in external browser:
```bash
firefox real_location_viewer.html
# or
google-chrome real_location_viewer.html
```

---

## ⚙️ Command Line Options

```bash
python3 real_world_simulator.py [OPTIONS]

Options:
  --location LOCATION    Location name or preset
                        Examples: "Times Square, NY" or times_square
                        Default: times_square

  --vehicles NUM         Number of vehicles to simulate
                        Default: 25

  --duration SECONDS     Simulation duration in seconds
                        Default: 60
```

### Examples:

```bash
# Small simulation (fast)
python3 real_world_simulator.py --location times_square --vehicles 10 --duration 30

# Medium simulation (balanced)
python3 real_world_simulator.py --location "Shibuya Crossing, Tokyo" --vehicles 25 --duration 60

# Large simulation (detailed)
python3 real_world_simulator.py --location "Downtown Manhattan, NY" --vehicles 50 --duration 120
```

---

## 🗺️ How It Works

### 1. Map Data Loading
- **With OSMnx**: Downloads real street network from OpenStreetMap
- **Without OSMnx**: Uses preset road layouts

### 2. Vehicle Placement
- Vehicles are placed on actual road segments
- Direction matches road direction
- Speed varies realistically

### 3. Movement Simulation
- Vehicles follow real road network
- Turn at actual intersections
- Speed adapts to road type

### 4. Clustering
- VANET clustering adapts to real traffic flow
- Cluster heads emerge naturally
- Trust scores track vehicle behavior

---

## 📊 What You'll See

### In the Animation:
1. **Gray Roads** - Real street network from OpenStreetMap
2. **Gray Dots** - Actual intersections
3. **Colored Circles** - Dynamic VANET clusters
4. **Moving Dots** - Vehicles following real roads
   - 🟢 Green = Normal vehicles
   - 🔴 Red = Malicious vehicles
   - 🟡 Yellow = Cluster heads
   - 🟠 Orange = Emergency vehicles

### Statistics:
- Number of roads and intersections
- Active clusters
- Messages exchanged
- Vehicles tracked

---

## 🎯 Use Cases

### 1. **Traffic Safety Research**
Simulate emergency vehicle routing in real city layouts

```bash
python3 real_world_simulator.py --location "Downtown Boston, MA" --vehicles 30
```

### 2. **Urban Planning**
Test VANET deployment in specific neighborhoods

```bash
python3 real_world_simulator.py --location "Silicon Valley, California" --vehicles 40
```

### 3. **Comparative Studies**
Compare different cities' traffic patterns

```bash
# Dense city
python3 real_world_simulator.py --location "Manhattan, NY" --vehicles 50

# Suburban area
python3 real_world_simulator.py --location "Palo Alto, CA" --vehicles 30
```

### 4. **Academic Research**
Use real-world topology for research validation

---

## 🔧 Advanced Usage

### Custom Map Area Size

Edit `real_world_simulator.py`:

```python
# Larger area (more roads)
G = ox.graph_from_place(
    location_query,
    network_type='drive',
    dist=1000,  # 1km radius
    simplify=True
)

# Smaller area (less roads, faster)
G = ox.graph_from_place(
    location_query,
    network_type='drive',
    dist=300,   # 300m radius
    simplify=True
)
```

### Add More Presets

Add to `PRESET_LOCATIONS` in `real_world_simulator.py`:

```python
PRESET_LOCATIONS = {
    'my_location': {
        'name': 'My Custom Location',
        'center': (latitude, longitude),
        'nodes': [(lat1, lon1), (lat2, lon2), ...],
        'edges': [((lat1, lon1), (lat2, lon2)), ...]
    }
}
```

---

## 📦 Output Files

### `real_location_animation.json`
Contains all simulation data:
- Vehicle positions over time
- Road network layout
- Cluster formation data
- Statistics

### File Structure:
```json
{
  "metadata": {
    "location": "Times Square, NY",
    "duration": 60,
    "num_vehicles": 25
  },
  "roads": [...],
  "intersections": [...],
  "frames": [...]
}
```

---

## 🐛 Troubleshooting

### OSMnx Not Working?

```bash
# Install dependencies
pip3 install osmnx folium geopandas

# If still not working, use presets
python3 real_world_simulator.py --location times_square
```

### Location Not Found?

```bash
# Be more specific
❌ python3 real_world_simulator.py --location "Main Street"
✅ python3 real_world_simulator.py --location "Main Street, Springfield, MA, USA"

# Or use coordinates
python3 real_world_simulator.py --location "40.7580,-73.9855"  # Times Square coords
```

### Simulation Too Slow?

```bash
# Reduce vehicles or duration
python3 real_world_simulator.py --vehicles 15 --duration 30

# Use preset locations (faster)
python3 real_world_simulator.py --location times_square
```

---

## 🌟 Cool Locations to Try

### Iconic Intersections:
1. **Shibuya Crossing** (Tokyo) - World's busiest intersection
2. **Times Square** (New York) - Famous intersection
3. **Piccadilly Circus** (London) - Historic junction
4. **Arc de Triomphe** (Paris) - Circular intersection

### University Campuses:
1. **Stanford University, CA**
2. **MIT, Cambridge, MA**
3. **IIT Delhi, India**
4. **Oxford University, UK**

### Downtown Areas:
1. **Manhattan Financial District**
2. **Downtown Los Angeles**
3. **Central London**
4. **Ginza, Tokyo**

---

## 📚 Examples Gallery

### Example 1: Times Square
```bash
python3 real_world_simulator.py --location times_square --vehicles 20
```
**Use Case:** Urban traffic congestion simulation

### Example 2: Real Tokyo
```bash
python3 real_world_simulator.py --location "Shibuya, Tokyo, Japan" --vehicles 30
```
**Use Case:** High-density pedestrian/vehicle interaction

### Example 3: Campus Network
```bash
python3 real_world_simulator.py --location "Stanford University, CA" --vehicles 15
```
**Use Case:** Controlled environment testing

---

## 📝 Next Steps

1. **Run a simulation** with your location of choice
2. **Open the viewer** (`real_location_viewer.html`)
3. **Analyze the results** - cluster formation, message passing
4. **Export data** for research or presentations

---

## 🎓 Research Applications

- **Thesis/Dissertation**: Use real-world topology for validation
- **Paper Submissions**: Include actual city layouts in experiments
- **Comparative Analysis**: Test algorithms across different cities
- **Urban Planning**: Simulate VANET deployment strategies

---

**Happy Simulating! 🚗📍**

For questions or issues, check the simulation output logs or try a preset location first.
