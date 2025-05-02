#ifndef POSITIONS_H
#define POSITIONS_H

// Structure for shoulder variables
typedef struct {
    int starting;
    int vertical;
    int ground;
    int PVC;
    int strafe;
    int potato;
    int drop;
} shoulderPositions;

// Structure for elbow variables
typedef struct {
    int starting;
    int parallelToShoulder;
    int perpendicularToShoulder;
    int ground;
    int PVC;
    int strafe;
    int potato;
    int drop;
} elbowPositions;

// Structure for wrist variables
typedef struct {
    int starting;
    int parallelToArm;
    int perpendicularUpwards;
    int perpedincularDownwards;
    int ground;
    int PVC;
    int strafe;
    int potato;
    int drop;
} wristPositions;

// Structure for claw variables
typedef struct {
    int open;
    int closedPoms;
    int closedPotato;
    int closedBox;
} clawPositions;

// All values are in ticks; backLeft corner of the robot
typedef struct {
    float x;
    float y;
    float theta;
} RobotState;

// Declare the global variable for variables
extern shoulderPositions shoulderPos;
extern elbowPositions elbowPos;
extern wristPositions wristPos;
extern clawPositions clawPos;
extern RobotState robotState;

#endif // POSITIONS_H