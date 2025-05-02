#ifndef SERVOS_H
#define SERVOS_H

// Struct to hold parameters for servoPosition
typedef struct {
    int port;
    int endPosition;
    int stepDelay;
} ServoParams;

void* servoThread(void* dataPtr);
void runServoThreads(ServoParams params[], int numServos);

extern ServoParams servoParams[3]; // Array to hold servo parameters

#endif