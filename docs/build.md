# Build Instructions

This document provides detailed instructions on how to build the project.

## Build System

The recommended build path is a direct g++ invocation inside the published Docker image `sillyfreak/wombat-cross` (which contains the full cross toolchain and KIPR libraries). This works on macOS, Windows, and Linux with Docker installed.

## Required Tools and Dependencies

To build the project, you will need:

- Docker
- Internet access to pull `sillyfreak/wombat-cross`

## Build Steps

1. Clone the repository:

    ```sh
    git clone https://github.com/GMHS-BotBall-Team-504/Project-X.git
    cd Project-X
    ```

2. Create the build directory:

    ```sh
    mkdir -p out/build
    ```

3. Build using the helper script (cross-platform):

    ```sh
    python3 build.py
    ```

4. Alternatively, run Docker manually (Unix shells):

    ```sh
    docker run --rm -v "$(pwd)":/work -w /work \
      sillyfreak/wombat-cross bash -lc \
      'mkdir -p out/build && aarch64-linux-gnu-g++ -Wall -O2 -g -Iinclude \
        -x c -std=c11 src/*.c -x c++ -std=c++17 src/*.cc src/*.cpp src/*.cxx \
        -o out/build/botball_user_program -lkipr -lpthread -lm -lz'
    ```

5. On Windows (PowerShell):

    ```powershell
    docker run --rm -v ${PWD}:/work -w /work `
      sillyfreak/wombat-cross bash -lc `
      "mkdir -p out/build && aarch64-linux-gnu-g++ -Wall -O2 -g -Iinclude `
        -x c -std=c11 src/*.c -x c++ -std=c++17 src/*.cc src/*.cpp src/*.cxx `
        -o out/build/botball_user_program -lkipr -lpthread -lm -lz"
    ```

6. The built executable will be located in the `out/build` directory:

    ```sh
    ls out/build/botball_user_program
    ```

## Common Build Issues and Troubleshooting

### Issue: Docker not found

**Solution:** Ensure that Docker is installed and running on your system. You can download Docker from [https://www.docker.com/](https://www.docker.com/).

### Issue: KIPR libraries not found or link errors

**Solution:** Use the `sillyfreak/wombat-cross` image as shown; it includes the correct ARM64 toolchain and libraries. If you maintain your own image, ensure `-lkipr -lpthread -lm -lz` resolve for aarch64 within the container.

### Note on mixed C/C++ sources

The build uses `aarch64-linux-gnu-g++` as the driver. `.c` files are compiled as C with `-x c -std=c11`; C++ sources use `-x c++ -std=c++17`. Linking is done with the C++ driver to satisfy C++ runtime dependencies.

### Issue: Build fails with missing dependencies

**Solution:** Ensure that all required dependencies are installed. Refer to the "Required Tools and Dependencies" section above for a list of dependencies.

### Issue: Build fails with permission denied errors

**Solution:** Ensure that you have the necessary permissions to run Docker and access the project directory. You may need to run the Docker commands with `sudo` or adjust the permissions of the project directory.

If you prefer CMake, a legacy `CMakeLists.txt` is present, but the Make-based flow above is simpler and aligns with the container’s quick start.

## Options

- --clean: removes `out/` before building, then builds fresh into `out/build`.
- --clean-only: removes `out/` and exits without building.
- --verbose or -v: prints the full compiler and docker commands and enables compiler verbosity.

Example:

```sh
python3 build.py --clean --verbose -DDEBUG
python3 build.py --clean-only
```

Note: The legacy CMake and custom Dockerfile flow are deprecated and no longer used.
