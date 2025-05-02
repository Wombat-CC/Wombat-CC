#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <unistd.h>
#include <math.h>
#include <time.h>

#define TAPE_THRESHOLD 1500
#define DEGREES_TO_TICKS 9.013888889
#define STRAFE_CM_TO_TICKS 233.830066338
#define STRAIGHT_CM_TO_TICKS 232.216295546
#define MAX_COMMAND_LENGTH 100

#define RESET_COLOR "\033[0m"
#define GREEN_COLOR "\033[32m"
#define RED_COLOR "\033[31m"
#define YELLOW_COLOR "\033[33m"
#define CYAN_COLOR "\033[36m"
#define MAGENTA_COLOR "\033[35m"

void displayWelcomeHeader();
void displayPrompt();
void displaySuccess(const char *message);
void driveDirection(const char *params);

// Function prototypes for commands
void executeCommand(const char *command, const char *params);
void turnRight(const char *params);
void turnLeft(const char *params);
void driveForward(const char *params);
void driveBackward(const char *params);
void driveRight(const char *params);
void driveLeft(const char *params);
void lowerArm(const char *params);
void moveArm(const char *params);
void newServoPos(const char *params);
void strafeArm(const char *params);
void pvcArm(const char *params);
void potatoArm(const char *params);
void groundArm(const char *params);
void openPos(const char *params);
void closePos(const char *params);
void closeBox(const char *params);
void helpCommand(const char *params);
void clearCommand(const char *params);
void batteryLevel(const char *params);
void tapeDetection(const char *params);