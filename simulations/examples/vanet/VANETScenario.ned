//
// VANET simulation scenario using Veins framework
//
package examples.vanet;

import veins.nodes.Car;
import veins.nodes.RSU;
import veins.base.connectionManager.ConnectionManager;
import veins.base.modules.BaseWorldUtility;
import veins.modules.mobility.traci.TraCIScenarioManagerLaunchd;
import veins.modules.obstacle.ObstacleControl;
import veins.modules.world.annotations.AnnotationManager;

network VANETScenario
{
    parameters:
        double playgroundSizeX @unit(m);
        double playgroundSizeY @unit(m);
        double playgroundSizeZ @unit(m);
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
                moduleType = "veins.nodes.Car";  // Use standard Veins car module
                moduleName = "node";
                moduleDisplayString = "";
                trafficLightModuleType = "veins.nodes.TrafficLight";
                trafficLightModuleName = "tls";
                trafficLightModuleDisplayString = "";
                host = "localhost";
                port = 9999;
                seed = 0;
                autoShutdown = true;
                margin = 25;
                roiRoads = "";
                roiRects = "";
                    launchConfig = xmldoc("sumo-launchd.launch.xml");
        }
        node[0]: veins.nodes.Car {
            @display("p=250,250");
        }
    connections allowunconnected:
}