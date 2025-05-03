# Build Instructions

This document provides detailed instructions on how to build the project.

## Build System

The project uses CMake as its build system. CMake is a cross-platform tool that automates the build process for software projects. It generates native build files for various platforms, such as Makefiles for Unix-based systems or Visual Studio project files for Windows.

## Required Tools and Dependencies

To build the project, you will need the following tools and dependencies:

- CMake (version 3.10 or higher)
- Docker (for cross-compilation)
- A C compiler (e.g., GCC)
- A C++ compiler (e.g., G++)

## Build Instructions

1. Clone the repository:

   ```sh
   git clone https://github.com/GMHS-BotBall-Team-504/Project-X.git
   cd Project-X
   ```

2. Create the build directory:

   ```sh
   mkdir -p out/build
   ```

3. Build the Docker image:

   ```sh
   docker build -t project-x-build .
   ```

4. Run the build process inside the Docker container:

   ```sh
   docker run --rm -v $(pwd):/app project-x-build bash -c 'mkdir -p /app/out/build && cd /app/out/build && cmake -DCMAKE_BUILD_TYPE=Release -DCMAKE_C_COMPILER=aarch64-linux-gnu-gcc /app && cmake --build .'
   ```

5. The built executable will be located in the `out/build` directory:

   ```sh
   ls out/build/botball_user_program
   ```

## Common Build Issues and Troubleshooting

### Issue: Docker not found

**Solution:** Ensure that Docker is installed and running on your system. You can download Docker from [https://www.docker.com/](https://www.docker.com/).

### Issue: CMake not found

**Solution:** Ensure that CMake is installed and available in your system's PATH. You can download CMake from [https://cmake.org/](https://cmake.org/).

### Issue: Cross-compilation toolchain not found

**Solution:** Ensure that the cross-compilation toolchain (e.g., `gcc-aarch64-linux-gnu`) is installed on your system. You can install it using your system's package manager. For example, on Ubuntu, you can run:

```sh
sudo apt-get install gcc-aarch64-linux-gnu g++-aarch64-linux-gnu libc6-dev-arm64-cross
```

### Issue: Build fails with missing dependencies

**Solution:** Ensure that all required dependencies are installed. Refer to the "Required Tools and Dependencies" section above for a list of dependencies.

### Issue: Build fails with permission denied errors

**Solution:** Ensure that you have the necessary permissions to run Docker and access the project directory. You may need to run the Docker commands with `sudo` or adjust the permissions of the project directory.

If you encounter any other issues or need further assistance, please refer to the project's documentation or reach out to the project maintainers.
