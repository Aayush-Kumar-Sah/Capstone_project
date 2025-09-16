#!/bin/bash

# Check if SUMO_HOME is set
if [ -z "$SUMO_HOME" ]; then
    echo "Error: SUMO_HOME is not set"
    exit 1
fi

# Start SUMO
sumo-gui -c simulations/config.sumo.cfg &
SUMO_PID=$!

# Wait for SUMO to initialize
sleep 2

# Start Python bridge
python3 src/simulation_bridge.py &
BRIDGE_PID=$!

# Start OMNeT++
cd simulations && opp_run -m -u Cmdenv -c General -n . omnetpp.ini &
OMNET_PID=$!

# Wait for user input to terminate
echo "Press Enter to terminate the simulation..."
read

# Kill all processes
kill $SUMO_PID
kill $BRIDGE_PID
kill $OMNET_PID