#include "../include/translation.h"
#include "../include/ports.h"
#include "../include/positions.h"
#include "../include/servos.h"
#include <kipr/wombat.h>
#include <pthread.h>
#include <stdlib.h>
#include <math.h>
#define constant 1
#define TAPE_THRESHOLD 1500
#define DEGREES_TO_TICKS 9.013888889
#define STRAFE_CM_TO_TICKS 233.830066338
#define STRAIGHT_CM_TO_TICKS 232.216295546
#define MAX_COMMAND_LENGTH 100

/* ----- Translational Movement ----- */

void crash(int backLeft, int backRight, int frontLeft, int frontRight) {
    mav(wheels.backLeft, (-1) * backLeft);
    mav(wheels.backRight, (-1) * backRight);
    mav(wheels.frontLeft, (-1) * frontLeft);
    mav(wheels.frontRight, (-1) * frontRight);
    msleep(30);
    ao();

}

/*! @brief Aligns the robot to the tape
 * @param direction Direction to align (1 for left, -1 for right)
 * @param ticksPerSecond Speed in ticksDegrees/sec
 * @details The robot will move towards the tape until it detects it.
 */
void alignRotation(int direction, int ticksPerSecond) {
    int speed = (direction == 1) ? -1 * ticksPerSecond : ticksPerSecond;
    move_at_velocity(wheels.frontLeft, speed);
    move_at_velocity(wheels.backLeft, speed);
    move_at_velocity(wheels.frontRight, (-1) * speed);
    move_at_velocity(wheels.backRight, (-1) * speed);
    while (analog(analogPorts.frontLight) < TAPE_THRESHOLD) {
        msleep(10);
    }
    crash(speed, (-1) * speed, speed, (-1) * speed);
    printf("Hit rotational tape\n");
}

/*! @brief Aligns the robot to the tape
 * @param ticksPerSecond Speed in ticksDegrees/sec
 * @details The robot will move towards the tape until it detects it.
*/
void alignBack(int ticksPerSecond) {
    mav(wheels.frontLeft, -ticksPerSecond);
    mav(wheels.backLeft, -ticksPerSecond);
    mav(wheels.frontRight, -ticksPerSecond);
    mav(wheels.backRight, -ticksPerSecond);
    while (analog(analogPorts.underLight) < TAPE_THRESHOLD) {
        msleep(5);
    }
    crash(-ticksPerSecond, -ticksPerSecond , -ticksPerSecond, -ticksPerSecond);
    printf("Hit back tape\n");
    return;
}

/// @brief Moves the robot forward
/// @param units Target ticks traveled
/// @param speed Speed in ticks/s
/// @details The robot will move forward at the given speed for the given number of ticks
void forwardDrive(int units, int maxSpeed) {
    printf("started\n");
    // Clear motor position counters
    clear_motor_position_counter(wheels.frontLeft);
    clear_motor_position_counter(wheels.backLeft);
    clear_motor_position_counter(wheels.frontRight);
    clear_motor_position_counter(wheels.backRight);

    int currentSpeed = 0;
    int acceleration_distance = units * 0.15; // 15% of distance for acceleration
    int deceleration_distance = units * 0.15; // 15% of distance for deceleration
    int constant_speed_distance = units - acceleration_distance - deceleration_distance;

    // Adjust distances for very short drives
    if (units < 200) { // For shorter distances, use a fixed smaller acceleration/deceleration distance
        acceleration_distance = units / 3;
        deceleration_distance = units / 3;
        constant_speed_distance = units - acceleration_distance - deceleration_distance;
        if (constant_speed_distance < 0) constant_speed_distance = 0;
    } else { // For longer distances, ensure minimum acceleration/deceleration distance
        if (acceleration_distance < 100) acceleration_distance = 100;
        if (deceleration_distance < 100) deceleration_distance = 100;
        constant_speed_distance = units - acceleration_distance - deceleration_distance;
        if (constant_speed_distance < 0) constant_speed_distance = 0;
    }

    printf("accelerating for %d ticks\n", acceleration_distance);
    // Gradual acceleration
    while (get_motor_position_counter(wheels.frontLeft) < acceleration_distance)
    {
        if (currentSpeed > maxSpeed) currentSpeed = maxSpeed;
        if (currentSpeed < 400 && get_motor_position_counter(wheels.frontLeft) >= 0) currentSpeed = 400; // Ensure minimum speed

        mav(wheels.frontLeft, constant * currentSpeed);
        mav(wheels.backLeft, constant * currentSpeed);
        mav(wheels.frontRight, currentSpeed);
        mav(wheels.backRight, currentSpeed);
        printf("current pos: %d\n", get_motor_position_counter(wheels.frontLeft));
        msleep(10);
        currentSpeed += 40;
    }

    // Drive at max speed
    printf("max\n");
    while (get_motor_position_counter(wheels.frontLeft) < acceleration_distance + constant_speed_distance) {
        mav(wheels.frontLeft, constant * maxSpeed);
        mav(wheels.backLeft, constant * maxSpeed);
        mav(wheels.frontRight, maxSpeed);
        mav(wheels.backRight, maxSpeed);
        msleep(10);
    }

    // Gradual deceleration
    printf("slowing\n");
    while (get_motor_position_counter(wheels.frontLeft) < units) {
        currentSpeed = maxSpeed - 50;
        if (currentSpeed < 400) currentSpeed = 400;

        mav(wheels.frontLeft, constant * currentSpeed);
        mav(wheels.backLeft, constant * currentSpeed);
        mav(wheels.frontRight, currentSpeed);
        mav(wheels.backRight, currentSpeed);
        msleep(10);
    }

    // Stop the motors
    stop(maxSpeed); // Use the stop function to apply a brief counter-movement
    return;
}

void backwardDrive(int units, int maxSpeed) {
    printf("started\n");
    // Clear motor position counters
    clear_motor_position_counter(wheels.frontLeft);
    clear_motor_position_counter(wheels.backLeft);
    clear_motor_position_counter(wheels.frontRight);
    clear_motor_position_counter(wheels.backRight);

    int currentSpeed = 0;
    int acceleration_distance = -units * 0.15; // 15% of distance for acceleration
    int deceleration_distance = -units * 0.15; // 15% of distance for deceleration
    int constant_speed_distance = -units + acceleration_distance + deceleration_distance;

    // Adjust distances for very short drives
    if (units < 200) { // For shorter distances, use a fixed smaller acceleration/deceleration distance
        acceleration_distance = -units / 3;
        deceleration_distance = -units / 3;
        constant_speed_distance = -units + acceleration_distance + deceleration_distance;
        if (constant_speed_distance > 0) constant_speed_distance = 0;
    } else { // For longer distances, ensure minimum acceleration/deceleration distance
        if (acceleration_distance > -100) acceleration_distance = -100;
        if (deceleration_distance > -100) deceleration_distance = -100;
        constant_speed_distance = -units + acceleration_distance + deceleration_distance;
        if (constant_speed_distance > 0) constant_speed_distance = 0;
    }

    printf("accelerating for %d ticks\n", acceleration_distance);
    // Gradual acceleration
    maxSpeed = -maxSpeed;
    while (get_motor_position_counter(wheels.frontLeft) > acceleration_distance)
    {
        if (currentSpeed < maxSpeed) currentSpeed = maxSpeed;
        if (currentSpeed > -50 && get_motor_position_counter(wheels.frontLeft) <= 0) currentSpeed = -400; // Ensure minimum speed

        mav(wheels.frontLeft, constant * currentSpeed);
        mav(wheels.backLeft, constant * currentSpeed);
        mav(wheels.frontRight, currentSpeed);
        mav(wheels.backRight, currentSpeed);
        printf("current pos: %d\n", get_motor_position_counter(wheels.frontLeft));
        msleep(10);
        currentSpeed -= 40;
    }

    // Drive at max speed
    printf("max\n");
    while (get_motor_position_counter(wheels.frontLeft) > acceleration_distance + constant_speed_distance) {
        mav(wheels.frontLeft, constant * maxSpeed);
        mav(wheels.backLeft, constant * maxSpeed);
        mav(wheels.frontRight, maxSpeed);
        mav(wheels.backRight, maxSpeed);
        msleep(10);
    }

    // Gradual deceleration
    printf("slowing\n");
    while (get_motor_position_counter(wheels.frontLeft) > units) {
        currentSpeed = maxSpeed + 50;
        if (currentSpeed > -400) currentSpeed = -400;
        
        mav(wheels.frontLeft, constant * currentSpeed);
        mav(wheels.backLeft, constant * currentSpeed);
        mav(wheels.frontRight, currentSpeed);
        mav(wheels.backRight, currentSpeed);
        msleep(10);
    }

    // Stop the motors
    stop(maxSpeed); // Use the stop function to apply a brief counter-movement
    return;
}

void rightDrive(int units, int maxSpeed) {
    // Clear motor position counters
    clear_motor_position_counter(wheels.frontLeft);
    clear_motor_position_counter(wheels.backLeft);
    clear_motor_position_counter(wheels.frontRight);
    clear_motor_position_counter(wheels.backRight);

    int currentSpeed = 0;
    int acceleration_distance = abs(units) * 0.15; // 15% of distance for acceleration
    int deceleration_distance = abs(units) * 0.15; // 15% of distance for deceleration
    int constant_speed_distance = abs(units) - acceleration_distance - deceleration_distance;

    // Adjust distances for very short drives
    if (abs(units) < 200) { // For shorter distances, use a fixed smaller acceleration/deceleration distance
        acceleration_distance = abs(units) / 3;
        deceleration_distance = abs(units) / 3;
        constant_speed_distance = abs(units) - acceleration_distance - deceleration_distance;
        if (constant_speed_distance < 0) constant_speed_distance = 0;
    } else { // For longer distances, ensure minimum acceleration/deceleration distance
        if (acceleration_distance < 100) acceleration_distance = 100;
        if (deceleration_distance < 100) deceleration_distance = 100;
        constant_speed_distance = abs(units) - acceleration_distance - deceleration_distance;
        if (constant_speed_distance < 0) constant_speed_distance = 0;
    }

    // Gradual acceleration
    while (abs(get_motor_position_counter(wheels.frontLeft)) < acceleration_distance) {
        if (currentSpeed > maxSpeed) currentSpeed = maxSpeed;
        if (currentSpeed < 400 && get_motor_position_counter(wheels.frontLeft) >= 0) currentSpeed = 400; // Ensure minimum speed

        mav(wheels.frontLeft, -currentSpeed);
        mav(wheels.backLeft, currentSpeed);
        mav(wheels.frontRight, currentSpeed);
        mav(wheels.backRight, -currentSpeed);
        msleep(10);
    }

    // Drive at max speed
    while (abs(get_motor_position_counter(wheels.frontLeft)) < acceleration_distance + constant_speed_distance) {
        mav(wheels.frontLeft, -maxSpeed);
        mav(wheels.backLeft, maxSpeed);
        mav(wheels.frontRight, maxSpeed);
        mav(wheels.backRight, -maxSpeed);
        msleep(10);
    }

    // Gradual deceleration
    while (abs(get_motor_position_counter(wheels.frontLeft)) < abs(units)) {
        currentSpeed = maxSpeed - 50;
        if (currentSpeed < 400) currentSpeed = 400;

        mav(wheels.frontLeft, -currentSpeed);
        mav(wheels.backLeft, currentSpeed);
        mav(wheels.frontRight, currentSpeed);
        mav(wheels.backRight, -currentSpeed);
        msleep(10);
    }

    // Stop the motors
    ao();
    return;
}

void leftDrive(int units, int maxSpeed) {
    // Clear motor position counters
    clear_motor_position_counter(wheels.frontLeft);
    clear_motor_position_counter(wheels.backLeft);
    clear_motor_position_counter(wheels.frontRight);
    clear_motor_position_counter(wheels.backRight);

    int currentSpeed = 0;
    int acceleration_distance = abs(units) * 0.15; // 15% of distance for acceleration
    int deceleration_distance = abs(units) * 0.15; // 15% of distance for deceleration
    int constant_speed_distance = abs(units) - acceleration_distance - deceleration_distance;

    // Adjust distances for very short drives
    if (abs(units) < 200) { // For shorter distances, use a fixed smaller acceleration/deceleration distance
        acceleration_distance = abs(units) / 3;
        deceleration_distance = abs(units) / 3;
        constant_speed_distance = abs(units) - acceleration_distance - deceleration_distance;
        if (constant_speed_distance < 0) constant_speed_distance = 0;
    } else { // For longer distances, ensure minimum acceleration/deceleration distance
        if (acceleration_distance < 100) acceleration_distance = 100;
        if (deceleration_distance < 100) deceleration_distance = 100;
        constant_speed_distance = abs(units) - acceleration_distance - deceleration_distance;
        if (constant_speed_distance < 0) constant_speed_distance = 0;
    }

    // Gradual acceleration
    while (abs(get_motor_position_counter(wheels.frontLeft)) < acceleration_distance) {
        if (currentSpeed > maxSpeed) currentSpeed = maxSpeed;
        if (currentSpeed < 400 && get_motor_position_counter(wheels.frontLeft) >= 0) currentSpeed = 400; // Ensure minimum speed
        mav(wheels.frontLeft, currentSpeed);
        mav(wheels.backLeft, -currentSpeed);
        mav(wheels.frontRight, -currentSpeed);
        mav(wheels.backRight, currentSpeed);
        msleep(10);
    }

    // Drive at max speed
    while (abs(get_motor_position_counter(wheels.frontLeft)) < acceleration_distance + constant_speed_distance) {
        mav(wheels.frontLeft, maxSpeed);
        mav(wheels.backLeft, -maxSpeed);
        mav(wheels.frontRight, -maxSpeed);
        mav(wheels.backRight, maxSpeed);
        msleep(10);
    }

    // Gradual deceleration
    while (abs(get_motor_position_counter(wheels.frontLeft)) < abs(units)) {
        currentSpeed = maxSpeed - 50;
        if (currentSpeed < 400) currentSpeed = 400;

        mav(wheels.frontLeft, currentSpeed);
        mav(wheels.backLeft, -currentSpeed);
        mav(wheels.frontRight, -currentSpeed);
        mav(wheels.backRight, currentSpeed);
        msleep(10);
    }

    // Stop the motors
    ao();
    return;
}

void rotate(int degrees, int speed) {
    for (int i = 0; i < 4; i++ ) {
        cmpc(i);
    }
    move_relative_position(wheels.frontLeft, speed / 4, -5 * DEGREES_TO_TICKS);
    move_relative_position(wheels.backLeft, speed / 4, -5 * DEGREES_TO_TICKS);
    move_relative_position(wheels.frontRight, -speed / 4, 5 * DEGREES_TO_TICKS);
    move_relative_position(wheels.backRight, -speed / 4, 5 * DEGREES_TO_TICKS);
    while (get_motor_done(wheels.frontLeft) == 0 && get_motor_done(wheels.frontRight) == 0 && get_motor_done(wheels.backLeft) == 0 && get_motor_done(wheels.backRight) == 0) {
        msleep(10);
        printf("%d\n", gmpc(wheels.frontLeft));
    }
    printf("first\n");
    move_relative_position(wheels.frontLeft, speed, degrees - (15 * DEGREES_TO_TICKS));
    move_relative_position(wheels.backLeft, speed, degrees - (15 * DEGREES_TO_TICKS));
    move_relative_position(wheels.frontRight, (-1) * speed, (-1) * degrees + (15 * DEGREES_TO_TICKS));
    move_relative_position(wheels.backRight, (-1) * speed, (-1) * degrees + (15 * DEGREES_TO_TICKS));
    while (get_motor_done(wheels.frontLeft) == 0 && get_motor_done(wheels.frontRight) == 0 && get_motor_done(wheels.backLeft) == 0 && get_motor_done(wheels.backRight) == 0) {
        msleep(10);
        printf("%d\n", gmpc(wheels.frontLeft));
    }
    printf("second\n");
    move_relative_position(wheels.frontLeft, speed / 2, (10 * DEGREES_TO_TICKS));
    move_relative_position(wheels.backLeft, speed / 2, (10 * DEGREES_TO_TICKS));
    move_relative_position(wheels.frontRight, (-1) * speed / 2, -(10 * DEGREES_TO_TICKS));
    move_relative_position(wheels.backRight, (-1) * speed / 2, -(10 * DEGREES_TO_TICKS));
    
    mav(wheels.frontLeft, (-1) * speed);
    mav(wheels.backLeft, (-1) * speed);
    mav(wheels.frontRight, speed);
    mav(wheels.backRight, speed);
    msleep(50);
    ao();
    printf("done\n");
    return;
}


// Revamped version of alloff so there's less drift
void stop(int motorSpeed) {
    for (int i = 0; i < 4; i++) {
        mav(i, (-1) * motorSpeed);
    }
    msleep(30);
    ao();
}

void backStop(int motorSpeed) {
    for (int i = 0; i < 4; i++) {
        mav(i, motorSpeed);
    }
    msleep(30);
    ao();
}

void rotateStop(int motorSpeed) {
    mav(wheels.backLeft, motorSpeed);
    mav(wheels.frontLeft, motorSpeed);
    mav(wheels.backRight, (-1) * motorSpeed);
    mav(wheels.frontRight, (-1) * motorSpeed);
    msleep(30);
    ao();
}

void centerDrive(int targetDistance, int baseSpeed, int kp) {
    int leftDistance, rightDistance, error, correction;
    int traveledDistance = 0;

    // Reset motor position counters
    for (int i = 0; i < 4; i++) {
        clear_motor_position_counter(i);
    }

    while (traveledDistance < targetDistance) {
        // Read rangefinder values
        leftDistance = analog(analogPorts.leftRange);
        rightDistance = analog(analogPorts.rightRange);

        // Calculate error and correction
        error = leftDistance - rightDistance;
        correction = kp * error;

        // Adjust motor speeds
        int leftSpeed = baseSpeed - correction;
        int rightSpeed = baseSpeed + correction;

        // Move the robot forward
        mav(wheels.frontLeft, leftSpeed);
        mav(wheels.backLeft, leftSpeed);
        mav(wheels.frontRight, rightSpeed);
        mav(wheels.backRight, rightSpeed);

        // Update traveled distance (assuming frontLeft motor is representative)
        traveledDistance = get_motor_position_counter(wheels.frontLeft);

        msleep(20); // Small delay for stability
    }

    // Stop the robot
    ao();
}

/* ----- Servo Movement ------- */

void strafePosition() {
    enable_servos();
    runServoThreads((ServoParams[]) {
        {servos.shoulder, shoulderPos.strafe, 2},
        {servos.elbow, elbowPos.strafe, 2},
        {servos.wrist, wristPos.strafe, 2}
    }, 3);
    msleep(200);
    disable_servos();
}

void servoPosition(int port, int position, int iterations) {
    enable_servo(port);
    float change = (float)(position - get_servo_position(port)) / iterations;
    for (int i = 0; i < iterations; i++) {
        set_servo_position(port, get_servo_position(port) + change);
        msleep(50);
    }
    while (get_servo_position(port) != position) {
        msleep(10);
    }
    disable_servo(port);

}

void openClaw() {
    enable_servo(servos.claw);
    set_servo_position(servos.claw, clawPos.open);
    msleep(500);
    disable_servo(servos.claw);
    printf("opened claw\n");
}

void closeClaw(int position) {
    enable_servo(servos.claw);
    if (position == 0) {
        set_servo_position(servos.claw, clawPos.closedPoms);
    }
    else {
        set_servo_position(servos.claw, clawPos.closedPotato);
    }
    msleep(500);
}

// We assume the robot is in the ground position
void verticalArm() {
    // turn on the necessary servos
    enable_servos();
    disable_servo(servos.claw);

    // enable the counterweight
    runServoThreads((ServoParams[]) {
        {servos.elbow, 200, 12},
        {servos.wrist, wristPos.perpendicularUpwards, 12}
    }, 2);
    disable_servo(servos.claw);
    // slowly move everything up
    runServoThreads((ServoParams[]) {
        {servos.shoulder, shoulderPos.vertical, 30},
        {servos.elbow, 720, 45}, // 218
        {servos.wrist, 650, 45}
    }, 3);
    disable_servo(servos.claw);
    msleep(200);
    closeClaw(0);
    printf("moved the arm up\n");
    return;
}


// Ran during the 1 minute before games start
void startUp() {
    alloff();
    disable_servos();
    msleep(500);

    for (int i = 0; i < 4; i++) {
        clear_motor_position_counter(i);
    }
    verticalArm();
    runServoThreads((ServoParams[]) {
        {servos.shoulder, shoulderPos.starting, 10},
        {servos.elbow, elbowPos.starting, 10},
        {servos.wrist, wristPos.starting, 10}
    }, 3);
    msleep(2000);
    return;
}

// ****************************************************************
// ****************************************************************
// ****************************************************************

// void turnRight(int speed, int degrees) {
//     if (speed > 0 && degrees > 0) {
//         rotate(DEGREES_TO_TICKS * -degrees, -speed);
//         printf("Turned right %d degrees at speed %d.\n", degrees, speed);
//     } else {
//         printf("Invalid parameters for turn_right.\nUsage: turn_right <speed> <degrees>\n");
//     }
// }

// void turnLeft(int speed, int degrees) {
//     if (speed > 0 && degrees > 0) {
//         rotate(DEGREES_TO_TICKS * degrees, speed);
//         printf("Turned left %d degrees at speed %d.\n", degrees, speed);
//     } else {
//         printf("Invalid parameters for turn_left. Usage: turn_left <speed> <degrees>\n");
//     }
// }

// void driveForward(int speed, int distance) {
//     if (speed > 0 && distance > 0) {
//         forwardDrive(distance * STRAIGHT_CM_TO_TICKS, speed);
//         printf("Drove forward %d inches at speed %d.\n", distance, speed);
//     } else {
//         printf("Invalid parameters for drive_forward.\nUsage: drive_forward <speed> <distance>\n");
//     }
// }

// void driveBackward(int speed, int distance) {
//     if (speed > 0 && distance > 0) {
//         backwardDrive(distance * STRAIGHT_CM_TO_TICKS, speed);
//         printf("Drove backward %d inches at speed %d.\n", distance, speed);
//     } else {
//         printf("Invalid parameters for drive_backward.\nUsage: drive_backward <speed> <distance>\n");
//     }
// }

// void driveRight(int speed, int distance) {
//     if (speed > 0 && distance > 0) {
//         rightDrive(distance * STRAFE_CM_TO_TICKS, speed);
//         printf("Drove right %d units at speed %d.\n", distance, speed);
//     } else {
//         printf("Invalid parameters for drive_right.\nUsage: drive_right <speed> <distance>\n");
//     }
// }

// void driveLeft(int speed, int distance) {
//     if (speed > 0 && distance > 0) {
//         leftDrive(distance * STRAFE_CM_TO_TICKS, speed);
//         printf("Drove left %d units at speed %d.\n", distance, speed);
//     } else {
//         printf("Invalid parameters for drive_left. Usage: drive_left <speed> <distance>\n");
//     }
// }

// void lowerArm() {
//     runServoThreads((ServoParams[]) {
//         {servos.shoulder, shoulderPos.ground, 2},
//         {servos.elbow, elbowPos.ground, 2},
//         {servos.wrist, wristPos.ground, 2}
//     }, 3);
//     printf("Lowered arm.\n");
// }

// void strafeArm() {
//     runServoThreads((ServoParams[]){
//         {servos.shoulder, shoulderPos.strafe, 2},
//         {servos.elbow, 100, 1},
//         {servos.wrist, wristPos.strafe, 2}},
//     3);
//     msleep(1700);
//     runServoThreads((ServoParams[]){
//                     {servos.shoulder, shoulderPos.strafe, 2},
//                     {servos.elbow, elbowPos.strafe, 2}},
//     2);
//     printf("Strafe arm position.\n");
//     return;
// }

// void pvcArm() {
//     // No parameters needed for this command
//     runServoThreads((ServoParams[]) {
//         {servos.shoulder, shoulderPos.PVC, 2},
//         {servos.elbow, elbowPos.PVC, 2},
//         {servos.wrist, wristPos.PVC, 2}
//     }, 3);
//     printf("PVC arm position.\n");
//     return;
// }

// void potatoArm() {
//     // No parameters needed for this command
//     runServoThreads((ServoParams[]) {
//         {servos.shoulder, shoulderPos.potato, 2},
//         {servos.elbow, elbowPos.potato, 2},
//         {servos.wrist, wristPos.potato, 2}
//     }, 3);
//     printf("Potato arm position.\n");
//     return;
// }

// void groundArm() {
//     runServoThreads((ServoParams[]) {
//         {servos.shoulder, shoulderPos.ground, 2},
//         {servos.elbow, elbowPos.ground, 2},
//         {servos.wrist, wristPos.ground, 2},
//     }, 3);
//     printf("Ground claw.\n");
//     return;
// }

// void openPos() {
//     openClaw();
//     return;
// }

// void closePos(int position) {
//     if (position == 0) {
//         closeClaw(0);
//     }
//     else {
//         closeClaw(1);
//     }
//     printf("Closed claw.\n");
//     return;
// }

// void closeBox() {
//     enable_servo(servos.claw);
//     set_servo_position(servos.claw, clawPos.closedBox);
//     msleep(500);
//     printf("Closed claw to Box.\n");
// }

// void driveDirection(int direction, int distance, int speed) {
//     if (direction < 0) {
//         direction = (direction % 360 + 360) % 360; // Convert negative direction to positive
//     }
//     if (direction >= 0 && direction <= 360 && distance > 0 && speed > 0) {
//         // Calculate wheel speeds based on direction
//         double rad = direction * (M_PI / 180.0);
//         double cos_dir = cos(rad);
//         double sin_dir = sin(rad);

//         int frontLeftSpeed = (int)(speed * (cos_dir - sin_dir));
//         int frontRightSpeed = (int)(speed * (cos_dir + sin_dir));
//         int rearLeftSpeed = (int)(speed * (cos_dir + sin_dir));
//         int rearRightSpeed = (int)(speed * (cos_dir - sin_dir));
//         int values[] = {frontLeftSpeed, frontRightSpeed, rearLeftSpeed, rearRightSpeed};

//         // Find the maximum calculated speed
//         int maxSpeed = fmax(values[0], fmax(values[1], fmax(values[2], values[3])));

//         // Calculate the scaling factor
//         double scaleFactor = 1.0;
//         if (maxSpeed > 1500) {
//             scaleFactor = 1500.0 / maxSpeed;
//         }
//         printf("scaleFactor: %f,\n", scaleFactor);
//         printf("maxSpeed: %d,\n", maxSpeed);

//         // Apply the scaling factor to all speeds
//         frontLeftSpeed = (int)(frontLeftSpeed * scaleFactor);
//         frontRightSpeed = (int)(frontRightSpeed * scaleFactor);
//         rearLeftSpeed = (int)(rearLeftSpeed * scaleFactor);
//         rearRightSpeed = (int)(rearRightSpeed * scaleFactor);
//         printf("frontLeftSpeed: %d,\nfrontRightSpeed: %d,\nrearLeftSpeed: %d,\nrearRightSpeed: %d,\n", frontLeftSpeed, frontRightSpeed, rearLeftSpeed, rearRightSpeed);

//         // Call the appropriate drive functions
//         move_relative_position(wheels.frontLeft, frontLeftSpeed, (frontLeftSpeed < 0) ? -distance : distance);
//         move_relative_position(wheels.frontRight, frontRightSpeed, (frontRightSpeed < 0) ? -distance : distance);
//         move_relative_position(wheels.backLeft, rearLeftSpeed, (rearLeftSpeed < 0) ? -distance : distance);
//         move_relative_position(wheels.backRight, rearRightSpeed, (rearRightSpeed < 0) ? -distance : distance);
//         while (get_motor_done(wheels.frontLeft) == 0 && get_motor_done(wheels.frontRight) == 0 && get_motor_done(wheels.backLeft) == 0 && get_motor_done(wheels.backRight) == 0) {
//             msleep(10);
//         }
//         mav(wheels.frontLeft, (-1) * frontLeftSpeed);
//         mav(wheels.frontRight, (-1) * frontRightSpeed);
//         mav(wheels.backLeft, (-1) * rearLeftSpeed);
//         mav(wheels.backRight, (-1) * rearRightSpeed);
//         msleep(30);
//         alloff(); // Stop the motors
//         printf("Drove in direction %d for %d units at speed %d.\n", direction, distance, speed);

//     } else {
//         printf("Invalid parameters for driveDirection. Usage: driveDirection <direction> <distance> <speed>\n");
//     }
// }

// void tapeDetection(int speed, int direction) {
//     alignRotation(direction, speed);
//     return;
// }
