#!/bin/bash

# Set strict error handling
set -e

# Function to cleanup processes
cleanup() {
    echo "Cleaning up processes..."
    pkill -f "sumo|veins_launchd|python.*launchd" 2>/dev/null || true
    lsof -i :9999 | grep LISTEN | awk '{print $2}' | xargs kill -9 2>/dev/null || true
    deactivate 2>/dev/null || true
    echo "Cleanup complete"
}

# Function to check command exists
check_command() {
    if ! command -v $1 &> /dev/null; then
        echo "Error: $1 is not installed"
        exit 1
    fi
}

# Set trap for cleanup on script exit
trap cleanup EXIT

# Kill any existing SUMO/Veins processes
cleanup
sleep 2

# Check required commands
check_command sumo
check_command python3
check_command opp_run

# Set environment variables
export SUMO_HOME="/home/vboxuser/sumo"
export VEINS_ROOT="/home/vboxuser/VANET_CAPStone/veins"
export PROJECT_ROOT="/home/vboxuser/VANET_CAPStone"
export PATH="$SUMO_HOME/bin:$VEINS_ROOT/bin:$PATH"
export PYTHONPATH="$SUMO_HOME/tools:$PROJECT_ROOT:$PYTHONPATH"
export LD_LIBRARY_PATH="$VEINS_ROOT/out/clang-release/src:$LD_LIBRARY_PATH"
export NEDPATH="$PROJECT_ROOT/src:$VEINS_ROOT/src:$PROJECT_ROOT/simulations"

# Verify environment variables
if [ -z "$SUMO_HOME" ] || [ ! -d "$SUMO_HOME" ]; then
    echo "Error: SUMO_HOME is not set correctly"
    exit 1
fi

if [ -z "$VEINS_ROOT" ] || [ ! -d "$VEINS_ROOT" ]; then
    echo "Error: VEINS_ROOT is not set correctly"
    exit 1
fi

# Create and activate Python virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# Build Veins
echo "Building Veins..."
cd "$VEINS_ROOT"
./configure && make -j$(nproc) MODE=release || {
    echo "Error: Failed to build Veins"
    exit 1
}
cd "$PROJECT_ROOT"

# Start SUMO
echo "Starting SUMO..."
cd "$PROJECT_ROOT/simulations"
sumo-gui -c config.sumo.cfg & 
SUMO_GUI_PID=$!
sleep 2  # Wait for SUMO to initialize

# Start SUMO launcher
echo "Starting SUMO launcher..."
python3 "$VEINS_ROOT/sumo-launchd.py" -vv &
SUMO_PID=$!

# Wait for SUMO launcher to initialize and verify it's running
sleep 2
if ! ps -p $SUMO_PID > /dev/null; then
    echo "Error: SUMO launcher failed to start"
    exit 1
fi

# Prepare simulation environment
echo "Preparing simulation environment..."
mkdir -p results
rm -f results/* # Clear previous results

# Run OMNeT++ simulation
echo "Starting OMNeT++ simulation..."
opp_run -m -u Cmdenv \
    -c General \
    -n .:$PROJECT_ROOT/src:$VEINS_ROOT/src \
    -l $VEINS_ROOT/src/libveins.so \
    omnetpp.ini || {
    echo "Error: OMNeT++ simulation failed"
    exit 1
}

# Start performance monitoring
echo "Starting performance monitoring..."
python3 "$PROJECT_ROOT/src/performance_monitor.py" &
MONITOR_PID=$!

# Run the VANET application
echo "Running VANET application..."
cd "$PROJECT_ROOT"
python3 -m src.custom_vanet_appl || {
    echo "Error: VANET application failed"
    exit 1
}

# Process and save results
echo "Processing simulation results..."
python3 "$PROJECT_ROOT/src/visualization.py" results/
mv performance_metrics.png results/
mv performance_report.txt results/

echo "Simulation completed successfully"
echo "Results are available in the 'results' directory"