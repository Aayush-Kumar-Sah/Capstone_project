package vanetscenario;

import org.car2x.veins.nodes.Car;
import org.car2x.veins.nodes.RSU;
import org.car2x.veins.base.connectionManager.ConnectionManager;
import org.car2x.veins.base.modules.BaseWorldUtility;
import org.car2x.veins.modules.mobility.traci.TraCIScenarioManagerLaunchd;
import org.car2x.veins.modules.obstacle.ObstacleControl;
import org.car2x.veins.modules.world.annotations.AnnotationManager;

module ClusterableVehicle extends Car
{
    parameters:
        @display("i=veins/node/car;is=vs");
        string applType = default("org.car2x.veins.modules.application.ieee80211p.DemoBaseApplLayer");
        string nicType = default("org.car2x.veins.modules.nic.Nic80211p");
        bool isClusterHead = default(false);
        bool isRelayNode = default(false);
        bool isBoundaryNode = default(false);
    gates:
        input clusterIn;
        output clusterOut;
}

network VANETScenario
{
    parameters:
        double playgroundSizeX @unit(m);
        double playgroundSizeY @unit(m);
        double playgroundSizeZ @unit(m);
        int numVehicles = default(100);
        @display("bgb=$playgroundSizeX,$playgroundSizeY");
    submodules:
        obstacles: ObstacleControl {
            @display("p=240,50");
        }
        annotations: AnnotationManager {
            @display("p=260,50");
        }
        connectionManager: ConnectionManager {
            parameters:
                @display("p=150,0;i=abstract/multicast");
        }
        world: BaseWorldUtility {
            parameters:
                playgroundSizeX = parent.playgroundSizeX;
                playgroundSizeY = parent.playgroundSizeY;
                playgroundSizeZ = parent.playgroundSizeZ;
                @display("p=30,0;i=misc/globe");
        }
        manager: TraCIScenarioManagerLaunchd {
            parameters:
                @display("p=512,128");
        }
        node[numVehicles]: ClusterableVehicle {
            parameters:
                @display("p=150,150;i=veins/node/car;is=vs");
        }
    connections allowunconnected:
}