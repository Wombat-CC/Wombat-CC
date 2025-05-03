# Project Architecture

## Overview

The architecture of Project X is designed to support autonomous navigation and task execution using a combination of sensors, motors, and servos. The project is built using C and CMake, and it is designed to run on the KIPR Wombat controller. The main components of the project include the following:

- **Sensors**: Used for obstacle detection and alignment.
- **Motors**: Used for movement and navigation.
- **Servos**: Used for precise movements and task execution.
- **Threads**: Used for concurrent task execution.

## Main Components

### Sensors

The project uses various sensors for obstacle detection and alignment. The sensors are connected to the KIPR Wombat controller and are used to gather data about the environment. The main sensors used in the project include:

- **Under Light Sensor**: Used for detecting the tape on the ground.
- **Left Range Sensor**: Used for detecting obstacles on the left side.
- **Right Range Sensor**: Used for detecting obstacles on the right side.
- **Front Light Sensor**: Used for detecting the tape in front of the robot.
- **Start Light Sensor**: Used for detecting the start signal.

### Motors

The project uses four motors for movement and navigation. The motors are connected to the KIPR Wombat controller and are used to control the wheels of the robot. The main motors used in the project include:

- **Front Left Motor**: Connected to port 3.
- **Front Right Motor**: Connected to port 0.
- **Back Left Motor**: Connected to port 2.
- **Back Right Motor**: Connected to port 1.

### Servos

The project uses four servos for precise movements and task execution. The servos are connected to the KIPR Wombat controller and are used to control the arm and claw of the robot. The main servos used in the project include:

- **Shoulder Servo**: Connected to port 0.
- **Elbow Servo**: Connected to port 1.
- **Wrist Servo**: Connected to port 2.
- **Claw Servo**: Connected to port 3.

### Threads

The project uses multiple threads for concurrent task execution. The threads are used to perform tasks such as moving the robot, controlling the servos, and processing sensor data. The main threads used in the project include:

- **Drive Threads**: Used for moving the robot forward, backward, left, and right.
- **Servo Threads**: Used for controlling the servos.
- **Sensor Threads**: Used for processing sensor data.

## Design Patterns

The project uses several design patterns to ensure maintainability and scalability. Some of the notable design patterns used in the project include:

- **Singleton Pattern**: Used for managing the global state of the robot.
- **Observer Pattern**: Used for monitoring sensor data and triggering actions based on the data.
- **Command Pattern**: Used for executing commands such as moving the robot and controlling the servos.

## Data Flow

The data flow in the project is designed to ensure efficient communication between the main components. The main data flow in the project includes the following steps:

1. **Sensor Data Collection**: The sensors collect data about the environment and send it to the KIPR Wombat controller.
2. **Data Processing**: The KIPR Wombat controller processes the sensor data and determines the appropriate actions to take.
3. **Command Execution**: The KIPR Wombat controller sends commands to the motors and servos to perform the appropriate actions.
4. **Task Execution**: The motors and servos execute the commands and perform the tasks.

## Important Algorithms

The project uses several important algorithms to ensure efficient and accurate task execution. Some of the notable algorithms used in the project include:

- **PID Control**: Used for precise control of the motors and servos.
- **Path Planning**: Used for determining the optimal path for the robot to take.
- **Obstacle Avoidance**: Used for detecting and avoiding obstacles in the environment.

