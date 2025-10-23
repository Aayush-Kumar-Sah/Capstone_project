#!/usr/bin/env python3
"""
Test script for bidirectional VANET scenario
"""
import subprocess
import sys
import os

def test_bidirectional_scenario():
    """Test the bidirectional traffic scenario"""
    print("🛣️  Testing Bidirectional VANET Scenario")
    print("=" * 70)
    
    # Change to project directory
    os.chdir("/home/vboxuser/VANET_CAPStone")
    
    # Step 1: Validate network file exists
    print("\n📁 Step 1: Checking network files...")
    network_file = "simulations/scenarios/bidirectional.net.xml"
    if os.path.exists(network_file):
        print(f"✅ Network file exists: {network_file}")
    else:
        print(f"❌ Network file missing: {network_file}")
        print("   Generating network file...")
        try:
            subprocess.run([
                "netconvert",
                "-c", "simulations/scenarios/bidirectional.netccfg"
            ], check=True, cwd="/home/vboxuser/VANET_CAPStone/simulations/scenarios")
            print("✅ Network file generated successfully")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to generate network: {e}")
            return False
    
    # Step 2: Validate routes
    print("\n🚗 Step 2: Validating vehicle routes...")
    try:
        result = subprocess.run([
            "sumo",
            "-n", "simulations/scenarios/bidirectional.net.xml",
            "-r", "simulations/scenarios/bidirectional.rou.xml",
            "--no-step-log",
            "--duration-log.statistics",
            "--end", "10"
        ], capture_output=True, text=True, check=True)
        print("✅ Routes validated successfully")
        # Print vehicle statistics
        for line in result.stdout.split('\n'):
            if 'Inserted' in line or 'Running' in line or 'Vehicles' in line:
                print(f"   {line.strip()}")
    except subprocess.CalledProcessError as e:
        print(f"❌ Route validation failed: {e}")
        print(e.stderr)
        return False
    
    # Step 3: Run short SUMO simulation test
    print("\n🎬 Step 3: Testing SUMO simulation (30 seconds)...")
    try:
        result = subprocess.run([
            "sumo",
            "-c", "simulations/scenarios/bidirectional.sumo.cfg",
            "--end", "30",
            "--no-step-log"
        ], capture_output=True, text=True, timeout=60, check=True)
        print("✅ SUMO simulation test successful")
        
        # Extract and display statistics
        for line in result.stdout.split('\n'):
            if any(keyword in line for keyword in ['Vehicles', 'Inserted', 'Running', 'Waiting']):
                print(f"   {line.strip()}")
                
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        print(f"❌ SUMO simulation failed: {e}")
        return False
    
    # Step 4: Visual test with SUMO GUI
    print("\n🎨 Step 4: Visual verification...")
    print("   You can manually verify the scenario with:")
    print("   $ sumo-gui -c simulations/scenarios/bidirectional.sumo.cfg")
    
    print("\n" + "=" * 70)
    print("🎉 Bidirectional scenario setup completed successfully!")
    print("\n📊 Scenario Features:")
    print("   • 2 lanes with opposite traffic directions")
    print("   • ~100 vehicles (50 eastbound RED, 50 westbound BLUE)")
    print("   • 2km road length (2000 meters)")
    print("   • Speed limit: 25 m/s (~90 km/h)")
    print("   • Simulation duration: 1000 seconds")
    print("\n🚀 Next Steps:")
    print("   1. Run with SUMO GUI: sumo-gui -c simulations/scenarios/bidirectional.sumo.cfg")
    print("   2. Test with clustering: python3 clustering_demo.py --duration 60")
    print("   3. Update omnetpp.ini to use bidirectional scenario")
    
    return True

if __name__ == "__main__":
    success = test_bidirectional_scenario()
    sys.exit(0 if success else 1)
