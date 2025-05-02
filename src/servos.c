#include "../include/servos.h"
#include <kipr/wombat.h>
#include <stdio.h>
#include <pthread.h>
#include <stdlib.h>

// Define a barrier for synchronization
pthread_barrier_t servoBarrier;

// Thread function to move the servo gradually
void* servoThread(void* dataPtr) {
    ServoParams* params = (ServoParams*)dataPtr;

    // Wait at the barrier until all threads are ready
    pthread_barrier_wait(&servoBarrier);

    int startPosition = get_servo_position(params->port);
    // Determine the direction of movement
    int step = (params->endPosition > startPosition) ? 15 : -15; // Step size
    int currentPosition = startPosition;

    // Gradually move the servo to the target position
    while ((step > 0 && currentPosition < params->endPosition) || 
           (step < 0 && currentPosition > params->endPosition)) {
        currentPosition += step;

        // Prevent overshooting
        if ((step > 0 && currentPosition > params->endPosition) || 
            (step < 0 && currentPosition < params->endPosition)) {
            currentPosition = params->endPosition;
        }

        set_servo_position(params->port, currentPosition);
        msleep(params->stepDelay);
    }

    return NULL;
}

// Function to run servo threads with gradual movement
void runServoThreads(ServoParams params[], int numServos) {
    enable_servos(); // Enable servos before starting threads
    pthread_t threads[3]; // Array to hold thread IDs (up to 3)

    // Initialize the barrier for the number of servos
    pthread_barrier_init(&servoBarrier, NULL, numServos);

    // Create threads for each servo
    for (int i = 0; i < numServos; i++) {
        pthread_create(&threads[i], NULL, servoThread, &params[i]);
    }

    // Wait for all threads to finish
    for (int i = 0; i < numServos; i++) {
        pthread_join(threads[i], NULL);
    }

    // Destroy the barrier
    pthread_barrier_destroy(&servoBarrier);
    disable_servos(); // Disable servos after movement
    return;
}