//
// Custom VANET message type definitions
//
cplusplus {{
#include "veins/base/utils/Coord.h"
#include "veins/modules/messages/BaseFrame1609_4_m.h"
}}

class noncobject veins::Coord;
packet veins::BaseFrame1609_4;

enum VANETMessageType {
    BEACON = 0;
    CLUSTER_HEAD_ANNOUNCEMENT = 1;
    JOIN_REQUEST = 2;
    JOIN_RESPONSE = 3;
    RELAY_ANNOUNCEMENT = 4;
    DATA_BROADCAST = 5;
}

packet CustomVANETMessage extends BaseFrame1609_4 {
    int messageType @enum(VANETMessageType);
    string sourceId;
    string destinationId;
    Coord position;
    double speed;
    double direction;
    int hopCount = 0;
    double timestamp;
    
    // Clustering specific fields
    bool isClusterHead = false;
    string clusterId;
    double clusterRadius;
    int memberCount;
    
    // Data fields
    string payload;
    int priority;
    bool requiresAck = false;
}