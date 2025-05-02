#ifndef THREADS_H
#define THREADS_H

typedef struct {
    ServoParams* params; // Pointer to the array of ServoParams
    int count;           // Number of servos to move
} ServoThreadArgs;

void* forwardDriveThread(void* arg);
void* backwardDriveThread(void* arg);
void* rotateThread(void* arg);
void* centerDriveThread(void* arg);
void* rightDriveThread(void* arg);
void* leftDriveThread(void* arg);
void* driveDirectionThread(void* arg);

void* runServoThreadsWrapper(void* arg);
void* verticalArmWrapper(void* arg);
void executeMovementandServoThreads(void* (*motorThreadFunc)(void*), int motorParams[], ServoThreadArgs* servoArgs);

#endif // THREADS_H