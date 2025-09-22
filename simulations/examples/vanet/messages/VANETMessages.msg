//
// Custom message types for VANET communication
//
cplusplus {{
#include "veins/base/utils/Coord.h"
#include "veins/modules/messages/BaseFrame1609_4_m.h"
#include "veins/base/utils/SimpleAddress.h"
}}

class noncobject veins::Coord;
class noncobject veins::LAddress::L2Type;
packet veins::BaseFrame1609_4;

enum VANETMessageType {
    BEACON = 0;                      // Regular beacon message
    EMERGENCY = 1;                   // Emergency vehicle announcement
    HAZARD_NOTIFICATION = 2;         // Road hazard warning
    TRAFFIC_UPDATE = 3;             // Traffic condition update
    CLUSTER_FORMATION = 4;          // Cluster formation message
    CLUSTER_JOIN = 5;               // Request to join cluster
    CLUSTER_LEAVE = 6;              // Notification of leaving cluster
    DATA_SHARING = 7;               // General data sharing
}

//
// Basic beacon message for vehicle presence announcement
//
packet BeaconMessage extends BaseFrame1609_4 {
    int messageType @enum(VANETMessageType) = BEACON;
    string vehicleId;               // Unique identifier of the sending vehicle
    Coord position;                 // Current position
    double speed;                   // Current speed in m/s
    double direction;               // Heading in degrees
    double acceleration;            // Current acceleration in m/s²
    int laneId;                    // Current lane ID
    bool emergency;                // Whether this is an emergency vehicle
}

//
// Message for cluster operations
//
packet ClusterMessage extends BaseFrame1609_4 {
    int messageType @enum(VANETMessageType);  // CLUSTER_FORMATION, CLUSTER_JOIN, or CLUSTER_LEAVE
    string clusterId;              // Unique identifier of the cluster
    string vehicleId;              // ID of the sending vehicle
    Coord position;                // Position of the sending vehicle
    double clusterRadius;          // Radius of the cluster
    int memberCount;               // Number of vehicles in the cluster
    double averageSpeed;           // Average speed of cluster members
    bool isClusterHead;           // Whether the sender is a cluster head
}

//
// Message for hazard and traffic notifications
//
packet TrafficMessage extends BaseFrame1609_4 {
    int messageType @enum(VANETMessageType);  // HAZARD_NOTIFICATION or TRAFFIC_UPDATE
    string sourceId;               // ID of the originating vehicle
    Coord location;                // Location of the reported incident
    int severity;                  // Severity level (1-5)
    string description;            // Text description of the incident
    double timestamp;              // Time when the incident was detected
    int hopCount;                 // Number of hops this message has traveled
    bool requiresAck;             // Whether acknowledgment is required
}

//
// General purpose data sharing message
//
packet DataMessage extends BaseFrame1609_4 {
    int messageType @enum(VANETMessageType) = DATA_SHARING;
    string sourceId;               // ID of the sending vehicle
    string targetId;               // ID of the target vehicle (if any)
    int priority;                  // Priority level of the data
    string dataType;              // Type of data being shared
    string payload;               // Actual data content
    double validityPeriod;        // How long the data is valid (in seconds)
    bool encrypted;               // Whether the payload is encrypted
}