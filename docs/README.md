# Project XBOT

## Overview

Project XBOT is a robotics project developed by the GMHS BotBall Team 504. The project aims to create a robot that can perform various tasks autonomously using a combination of sensors, motors, and servos. The project is built using C and CMake, and it is designed to run on the KIPR Wombat controller.

## Features

-   Autonomous navigation and task execution
-   Sensor integration for obstacle detection and alignment
-   Servo control for precise movements
-   Multi-threaded execution for concurrent tasks
-   Docker-based build environment for cross-compilation

## Getting Started

### Prerequisites

-   Docker
-   CMake
-   GCC for ARM64 cross-compilation

### Directory Structure

-   `src/`: Contains the source code for the project
    -   `_init_helper.c`: Initialization helper functions
    -   `main.c`: Main entry point for the project
    -   `ports.c`: Port definitions for motors and sensors
    -   `positions.c`: Predefined positions for servos
    -   `servos.c`: Servo control functions
    -   `threads.c`: Thread management functions
    -   `translation.c`: Movement and alignment functions
-   `include/`: Contains the header files for the project
    -   `library.h`: Main header file including all other headers
    -   `ports.h`: Port definitions for motors and sensors
    -   `positions.h`: Predefined positions for servos
    -   `second.h`: Additional utility functions
    -   `servos.h`: Servo control functions
    -   `tasks.h`: Task-specific functions
    -   `threads.h`: Thread management functions
    -   `translation.h`: Movement and alignment functions
-   `docs/`: Contains the documentation for the project
    -   `README.md`: Overview of the project
    -   `architecture.md`: Project architecture and design patterns
    -   `development.md`: Development guidelines and best practices
    -   `ci-cd.md`: CI/CD pipeline setup and configuration
    -   `build.md`: Build instructions and troubleshooting
    -   `usage.md`: Usage instructions and examples
    -   `faq.md`: Frequently asked questions
-   `.github/workflows/`: Contains GitHub Actions workflows for CI/CD
    -   `ci.yml`: Continuous integration workflow
    -   `release.yml`: Release workflow
-   `.editorconfig`: Editor configuration file
-   `.gitignore`: Git ignore file
-   `build.py`: Python script for building the project using Docker
-   `CMakeLists.txt`: CMake configuration file
-   `Dockerfile`: Dockerfile for creating the build environment

### Building the Project

1. Clone the repository:

    ```sh
    git clone https://github.com/GMHS-BotBall-Team-504/Project-X.git
    cd Project-X
    ```

2. Build the Docker image:

    ```sh
    docker build -t project-x-build .
    ```

3. Build the project using the Docker container:
    ```sh
    python build.py
    ```

### Running the Project

1. Connect the KIPR Wombat controller to your computer.

2. Upload the `botball_user_program` executable to the Wombat controller.

3. Run the program on the Wombat controller.

## License

This project is licensed under the MIT License. See the `LICENSE.md` file for more details.
