#ifndef MONITORDEF_H
#define MONITORDEF_H

enum MonitorStatus{
    noAlert,
    preAlert,
    snAlert,
    nearbyAlert
};

enum MonitorMessage{
    noMessage,
    newAlert,
    newDirection
};
#endif
