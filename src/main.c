#include "../include/library.h"
#include <math.h>
#include <pthread.h>

typedef struct {
    int distance;
    double speed;
} driveArgs;

void* driveForwardThread(void* args) {
    driveArgs* arguments = (driveArgs*)args;
    driveForward(arguments->distance, arguments->speed);
    return NULL;
}

void* driveBackwardThread(void* args) {
    driveArgs* arguments = (driveArgs*)args;
    driveBackward(arguments->distance, arguments->speed);
    return NULL;
}

#define TAPE_THRESHOLD 1500
#define DEGREES_TO_TICKS 9.013888889
#define STRAFE_CM_TO_TICKS 233.830066338
#define STRAIGHT_CM_TO_TICKS 232.216295546
// 3425 seems to be 360 degrees

int main() {
    printf("Are you ready? Press enter to proceed. Good Luck!");
    getchar();
    printf("==============================================================\n");

    /* ##################################################################
    |  Pre - Run Tasks
    | ################################################################### */

    pthread_t driveThread, servoThread;

    {
        // Arguments for driveForward
        driveArgs arguments = {1500, 50 / STRAIGHT_CM_TO_TICKS};

        // Create threads
        pthread_create(&driveThread, NULL, driveForwardThread, (void*)&arguments);
        pthread_create(&servoThread, NULL, (void *(*)(void *))openPos, NULL);

        // Wait for both threads to finish
        pthread_join(driveThread, NULL);

        driveDirection(90, 4000, 1500);
        pthread_join(servoThread, NULL);
    }
    printf("scuff 1");
    {
        // Arguments for driveBackwards
        driveArgs arguments = {1500, 50 / STRAIGHT_CM_TO_TICKS};

        // Create threads
        pthread_create(&driveThread, NULL, driveBackwardThread, (void*)&arguments);
        pthread_create(&servoThread, NULL, (void* (*)(void*))openPos, NULL);

        // Wait for both threads to finish
        pthread_join(driveThread, NULL);
        pthread_join(servoThread, NULL);
    }

    return 0;




























































    // startUp();
    // while (analog(analogPorts.startLight) > 1200) {
    //     msleep(10);
    // }
    // printf("Alright, I'm ready to go!\n");
    // getchar();
    // shut_down_in(119);


    /* ##################################################################
    |  Starting Alignment
    | ################################################################### */

    robotState = (RobotState) {
        .x = 23.20 * STRAIGHT_CM_TO_TICKS,
        .y = 0.00,
        .theta = 1622.50
    };
    printf("Current Position: x: %.2f, y: %.2f, theta: %.2f\n", robotState.x, robotState.y, robotState.theta);

    forwardDrive(150, 1500);
    robotState.x += 150;

    /* ##################################################################
    |  Box Exit
    | ################################################################### */

    runServoThreads((ServoParams[]) {
        {servos.shoulder, shoulderPos.strafe, 2},
        {servos.elbow, elbowPos.strafe, 2},
        {servos.wrist, wristPos.strafe, 2}
    }, 3);
    msleep(200);
    rightDrive(22.63 * STRAFE_CM_TO_TICKS, 1500);
    robotState.y += 22.63 * STRAFE_CM_TO_TICKS;
    printf("Current Position: x: %.2f, y: %.2f, theta: %.2f\n", robotState.x, robotState.y, robotState.theta);
    

    /* ##################################################################
    |  First Pom Set Alignment
    | ################################################################### */

    { // Open the claw and rotate to face the poms
        int motorParams[] = {1820, 1500};
        ServoThreadArgs servoArgs = {(ServoParams[]) {
                {servos.claw, clawPos.open, 2}
            }, 1 };
        executeMovementandServoThreads(rotateThread, motorParams, &servoArgs);
    }

    alignRotation(1, 1000);
    rotate((int)(DEGREES_TO_TICKS*(-6)), -1500); // Small correction
    robotState.theta = 0;

    alignBack(1000);
    printf("Current Position: x: %.2f, y: %.2f, theta: %.2f\n", robotState.x, robotState.y, robotState.theta);

    msleep(140);
    backStop(1000);
    /* ---------- Floor the Claw ---------- */
    runServoThreads((ServoParams[]) {
        {servos.elbow, elbowPos.ground, 2},
        {servos.wrist, wristPos.ground, 2},
        {servos.shoulder, shoulderPos.ground, 2}
    }, 3); // Set up so the robot doesn't break itself when it moves the servos
    
    msleep(400);

    /* ##################################################################
    |  Approach First Pom Set
    | ################################################################### */
    
    // Collect the poms
    forwardDrive(2300, 1500);
    forwardDrive(250, 1000);
    rotate(-200, -1000);
    runServoThreads((ServoParams[]) {
        {servos.elbow, 2000, 2},
        {servos.wrist, wristPos.ground, 2},
        {servos.shoulder, shoulderPos.ground, 2}
    }, 3); // Set up so the robot doesn't break itself when it moves the servos
    closeClaw(0);
    msleep(100);


    /* ##################################################################
    |  Drop off First Pom Set
    | ################################################################### */

    backwardDrive(200, 1500);

    { // Turn to face the first box
        int motorParams[] = {-589, -1500};
        ServoThreadArgs servoArgs = {
            (ServoParams[]) {
                {servos.elbow, elbowPos.PVC, 2},
                {servos.wrist, wristPos.PVC, 2}
            }, 2
        };

        // Execute threads
        executeMovementandServoThreads(rotateThread, motorParams, &servoArgs);
    }
    forwardDrive(400, 1500);
    msleep(100);
    openClaw();
    msleep(50);


    /* ##################################################################
    |  Second Pom Set Alignment
    | ################################################################### */

    {
        pthread_t strafeThread, backupThread;
    
        // Arguments for the backward drive
        int motorParams[] = {400, 1500};
    
        // Create thread for `strafePosition`
        pthread_create(&strafeThread, NULL, (void* (*)(void*))strafePosition, NULL);
    
        pthread_create(&backupThread, NULL, backwardDriveThread, (void*)motorParams);
    
        // Wait for both threads to finish
        pthread_join(strafeThread, NULL);
        pthread_join(backupThread, NULL);
    }


    /* ##################################################################
    |  Approach Second Pom Set
    | ################################################################### */

    rotate(DEGREES_TO_TICKS * 40, 1500);
    alignRotation(-1, 1000);
    leftDrive(800, 1500);
    forwardDrive(200, 1500);
    runServoThreads((ServoParams[]) {
        {servos.shoulder, shoulderPos.ground, 2},
        {servos.elbow, elbowPos.ground, 2},
        {servos.wrist, wristPos.ground, 2}
    }, 3);

    closeClaw(0);

    return 0;



    /* ##################################################################
    |  Drop off Third Pom Set
    | ################################################################### */








    /* ##################################################################
    |  Third Pom Set Alignment
    | ################################################################### */







    // Assume that we are in strafing, parallel to the long side of the game board

    /* ##################################################################
    |  Approach Third Pom Set
    | ################################################################### */

    robotState = (RobotState) {
        .x = 23.20 * STRAIGHT_CM_TO_TICKS,
        .y = 0.00,
        .theta = 0
    };
    // Collect the poms
    forwardDrive(2300, 1500);
    forwardDrive(250, 1000);
    rotate(-200, -1000);
    runServoThreads((ServoParams[]) {
        {servos.elbow, 2000, 2},
        {servos.wrist, wristPos.ground, 2},
        {servos.shoulder, shoulderPos.ground, 2}
    }, 3); // Set up so the robot doesn't break itself when it moves the servos
    closeClaw(0);
    msleep(100);


    /* ##################################################################
    |  Drop off Third Pom Set
    | ################################################################### */

    backwardDrive(200, 1500);

    { // Turn to face the first box
        int motorParams[] = {-589, -1500};
        ServoThreadArgs servoArgs = {
            (ServoParams[]) {
                {servos.elbow, elbowPos.PVC, 2},
                {servos.wrist, wristPos.PVC, 2}
            }, 2
        };

        // Execute threads
        executeMovementandServoThreads(rotateThread, motorParams, &servoArgs);
    }
    msleep(100);
    openClaw();
    msleep(50);

    /* ##################################################################
    |  Drop off Basket
    | ################################################################### */







    /* ##################################################################
    |  Potato Grab
    | ################################################################### */

    backwardDrive(500, 1500);

    /* ##################################################################
    |  Drop off Potato
    | ################################################################### */










    rotate(DEGREES_TO_TICKS*(4), 1500);
    rotate(DEGREES_TO_TICKS*(-5), -1500);
    rightDrive(900, 1500);
    forwardDrive(300, 1500);
    rotate(DEGREES_TO_TICKS*(-25), 1500);
    rightDrive(900, 1500);
    forwardDrive(300, 1500);
    rotate(DEGREES_TO_TICKS*(-25), 1500);
    closeClaw(0);
    return 0;



}