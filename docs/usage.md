# Usage

## Main Features

### Autonomous Navigation and Task Execution
The robot can navigate autonomously and perform various tasks using its sensors and motors.

### Sensor Integration
The robot integrates multiple sensors for obstacle detection and alignment.

### Servo Control
The robot uses servos for precise movements.

### Multi-threaded Execution
The robot can execute multiple tasks concurrently using multi-threading.

### Docker-based Build Environment
The project uses Docker for cross-compilation, ensuring a consistent build environment.

## Accessing Main Features

### Autonomous Navigation
To enable autonomous navigation, the robot uses a combination of sensors and motors. The main entry point for the project is `src/main.c`, which contains the logic for autonomous navigation.

### Sensor Integration
The sensors are defined in `include/ports.h` and `src/ports.c`. The robot uses analog and digital ports to read sensor data.

### Servo Control
The servos are controlled using functions defined in `include/servos.h` and `src/servos.c`. The robot uses multiple servos for precise movements.

### Multi-threaded Execution
The project uses multi-threading to execute multiple tasks concurrently. The threading logic is defined in `include/threads.h` and `src/threads.c`.

### Docker-based Build Environment
The project uses Docker for cross-compilation. The Dockerfile is located in the root directory, and the build process is managed by `build.py`.

## Common Usage Scenarios and Examples

### Scenario 1: Autonomous Navigation
1. Build the project using Docker:
   ```sh
   python build.py
   ```
2. Upload the `botball_user_program` executable to the KIPR Wombat controller.
3. Run the program on the Wombat controller to enable autonomous navigation.

### Scenario 2: Sensor Integration
1. Define the sensor ports in `include/ports.h` and `src/ports.c`.
2. Read sensor data using the functions provided by the KIPR library.
3. Use the sensor data to make decisions in the main program.

### Scenario 3: Servo Control
1. Define the servo ports in `include/ports.h` and `src/ports.c`.
2. Control the servos using the functions defined in `include/servos.h` and `src/servos.c`.
3. Use the servos to perform precise movements in the main program.

### Scenario 4: Multi-threaded Execution
1. Define the threading logic in `include/threads.h` and `src/threads.c`.
2. Create and manage threads in the main program to execute multiple tasks concurrently.

### Scenario 5: Docker-based Build Environment
1. Build the Docker image:
   ```sh
   docker build -t project-x-build .
   ```
2. Build the project using the Docker container:
   ```sh
   python build.py
   ```
3. Upload the `botball_user_program` executable to the KIPR Wombat controller.
4. Run the program on the Wombat controller.
