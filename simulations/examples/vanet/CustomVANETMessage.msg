//
// Custom VANET message type definitions with comprehensive clustering support
//
cplusplus {{
#include "veins/base/utils/Coord.h"
#include "veins/modules/messages/BaseFrame1609_4_m.h"
}}

class noncobject veins::Coord;
packet veins::BaseFrame1609_4;

enum VANETMessageType {
    // Basic messages
    BEACON = 0;
    DATA_BROADCAST = 1;
    
    // Cluster formation messages
    CLUSTER_HEAD_ANNOUNCEMENT = 10;
    CLUSTER_JOIN_REQUEST = 11;
    CLUSTER_JOIN_RESPONSE = 12;
    CLUSTER_LEAVE_NOTIFICATION = 13;
    
    // Cluster maintenance messages
    CLUSTER_HEARTBEAT = 20;
    CLUSTER_HEAD_ELECTION = 21;
    CLUSTER_HEAD_HANDOVER = 22;
    CLUSTER_MERGE_REQUEST = 23;
    CLUSTER_MERGE_RESPONSE = 24;
    CLUSTER_SPLIT_NOTIFICATION = 25;
    
    // Cluster data dissemination
    INTRA_CLUSTER_DATA = 30;
    INTER_CLUSTER_DATA = 31;
    CLUSTER_GATEWAY_DATA = 32;
    
    // Emergency and priority messages
    EMERGENCY_BROADCAST = 40;
    CLUSTER_EMERGENCY = 41;
    
    // Network management
    NEIGHBOR_DISCOVERY = 50;
    LINK_STATE_UPDATE = 51;
    ROUTE_REQUEST = 52;
    ROUTE_RESPONSE = 53;
}

enum ClusterState {
    CLUSTER_FORMING = 0;
    CLUSTER_STABLE = 1;
    CLUSTER_MERGING = 2;
    CLUSTER_SPLITTING = 3;
    CLUSTER_DISSOLVING = 4;
}

enum JoinResponseCode {
    JOIN_ACCEPTED = 0;
    JOIN_REJECTED_FULL = 1;
    JOIN_REJECTED_INCOMPATIBLE = 2;
    JOIN_REJECTED_DUPLICATE = 3;
}

enum MergeResponseCode {
    MERGE_ACCEPTED = 0;
    MERGE_REJECTED_SIZE = 1;
    MERGE_REJECTED_INCOMPATIBLE = 2;
    MERGE_REJECTED_BUSY = 3;
}

packet CustomVANETMessage extends BaseFrame1609_4 {
    // Basic message fields
    int messageType @enum(VANETMessageType);
    string sourceId;
    string destinationId;
    Coord position;
    double speed;
    double direction;
    int hopCount = 0;
    double timestamp;
    int sequenceNumber = 0;
    
    // Vehicle properties
    string laneId;
    double acceleration;
    string vehicleType;
    
    // Basic clustering fields
    bool isClusterHead = false;
    string clusterId;
    string clusterHeadId;
    double clusterRadius;
    int memberCount;
    int clusterState @enum(ClusterState) = CLUSTER_FORMING;
    
    // Advanced clustering fields
    double clusterStability;
    double clusterQuality;
    double clusterLifetime;
    string[] memberList;
    string[] neighborClusters;
    
    // Cluster head election fields
    double connectivityScore;
    double mobilityScore;
    double positionScore;
    double compositeScore;
    int electionRound = 0;
    
    // Join/Leave fields
    int joinResponseCode @enum(JoinResponseCode) = JOIN_ACCEPTED;
    string rejectionReason;
    double compatibilityScore;
    
    // Merge/Split fields
    string mergeTargetCluster;
    int mergeResponseCode @enum(MergeResponseCode) = MERGE_ACCEPTED;
    string[] splitGroups;
    string splitReason;
    
    // Data dissemination fields
    string payload;
    int priority = 0;
    bool requiresAck = false;
    string dataType;
    double dataTimestamp;
    bool isEmergency = false;
    
    // Network topology fields
    string[] neighborIds;
    double[] neighborDistances;
    double[] neighborSignalStrengths;
    
    // QoS and reliability fields
    int retryCount = 0;
    double expiryTime;
    bool isReliable = false;
    string originalSource;
    
    // Geographic routing fields
    Coord destinationPosition;
    double maxHopDistance;
    string routingMode;
    
    // Security fields (placeholders for future implementation)
    bool isSigned = false;
    string securityHash;
    double certificateExpiry;
}