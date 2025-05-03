# CI/CD Setup

This document provides an overview of the project's continuous integration and continuous deployment (CI/CD) setup.

## CI/CD Pipeline

The CI/CD pipeline for this project is defined using GitHub Actions. The pipeline consists of the following stages:

1. **Build**: This stage is responsible for building the project. It runs on the `ubuntu-latest` environment and uses a Docker container with the `sillyfreak/wombat-cross` image. The build process includes installing dependencies, configuring the project with CMake, and building the project.

2. **Release**: This stage is responsible for creating a release and uploading the built binary. It runs on the `ubuntu-latest` environment and uses a Docker container with the `sillyfreak/wombat-cross` image. The release process includes installing dependencies, configuring the project with CMake, building the project, creating a release, and uploading the built binary.

## Configuring and Running the CI/CD Pipeline Locally

To configure and run the CI/CD pipeline locally, follow these steps:

1. **Install Docker**: Ensure that Docker is installed on your local machine. You can download and install Docker from [here](https://www.docker.com/products/docker-desktop).

2. **Build the Docker Image**: Navigate to the root directory of the project and build the Docker image using the following command:
   ```sh
   docker build -t project-x-build .
   ```

3. **Run the CI/CD Pipeline**: Use the following command to run the CI/CD pipeline locally:
   ```sh
   docker run --rm -v $(pwd):/app project-x-build bash -c "mkdir -p /app/out/build && cd /app/out/build && cmake -DCMAKE_BUILD_TYPE=Release -DCMAKE_C_COMPILER=aarch64-linux-gnu-gcc /app && cmake --build ."
   ```

This command mounts the current directory to the Docker container, configures the project with CMake, and builds the project.

