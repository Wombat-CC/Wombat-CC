#ifndef VARIABLES_H
#define VARIABLES_H

// Structure for wheel ports
typedef struct {
    int frontLeft;   // Corresponds to port 3
    int frontRight;  // Corresponds to port 0
    int backLeft;    // Corresponds to port 2
    int backRight;   // Corresponds to port 1
} WheelPorts;

// Structure for servo ports
typedef struct {
    int shoulder; // Port 0
    int elbow;   // Port 1
    int wrist;  // Port 2
    int claw;    // Port 3
} servoPorts;

// Structure for analog ports (range)
typedef struct {
    int underLight;
    int leftRange; // 2400 max, 900 blank
    int rightRange;
    int frontLight;
    int startLight;
} AnalogPorts;

// Structure for digital ports (0, 1)
typedef struct {
    
} DigitalPorts;


// Declare the global variable for ports
extern WheelPorts wheels;
extern servoPorts servos;
extern AnalogPorts analogPorts;
extern DigitalPorts digitalPorts;

#endif // VARIABLES_H