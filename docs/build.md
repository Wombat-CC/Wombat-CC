# Build Instructions

This document provides detailed instructions on how to build the project.

## Build System

The recommended build path is a direct g++ invocation inside the published Docker image `sillyfreak/wombat-cross` (which contains the full cross toolchain and KIPR libraries). This works on macOS, Windows, and Linux with Docker installed.

## Configuration

The build system uses configuration files in the `configs/` directory to customize compiler flags, optimization levels, and other build options. By default, the build system uses `configs/config.dev.yaml` for development builds.

### Pre-configured Build Profiles

The project includes three pre-configured build profiles in the `configs/` directory:

- **config.dev.yaml**: Development configuration (DEFAULT)
    - Debug optimization (`-Og`) optimized for debugging experience
    - Debug symbols enabled for debugging with gdb
    - Extra warnings (`-Wall -Wextra -Wpedantic`) to catch issues early
    - Best for active development and testing

- **config.prod.yaml**: Production configuration
    - Aggressive optimization (`-O3`) for maximum performance
    - No debug symbols for smaller binary size
    - Essential warnings only (`-Wall`)
    - Best for final builds and deployment

- **config.example.yaml**: Example configuration template
    - Comprehensive documentation of all available options
    - Copy and customize this file for your own configurations

### Using Build Profiles

**Default development build (uses config.dev.yaml):**

```sh
python3 build.py
```

**Production build:**

```sh
python3 build.py --config configs/config.prod.yaml
```

**Custom configuration:**

```sh
python3 build.py --config configs/my-custom-config.yaml
```

### Creating a Custom Configuration

1. Copy an existing configuration or the example:

    ```sh
    cp configs/config.dev.yaml configs/my-config.yaml
    # or
    cp configs/config.example.yaml configs/my-config.yaml
    ```

2. Edit your new configuration file to customize build settings.

3. Use it with the `--config` flag:

    ```sh
    python3 build.py --config configs/my-config.yaml
    ```

### Configuration Options

The configuration file supports the following options:

- **docker_image**: Docker image to use for cross-compilation (default: `sillyfreak/wombat-cross`)

- **compiler**:
    - **cross_compiler**: Cross-compiler executable (default: `aarch64-linux-gnu-g++`)
    - **flags**: Compiler warning and other flags (default: `-Wall`)
    - **optimization**: Optimization level `-Og` (debug), `-O0`, `-O1`, `-O2`, `-O3`, `-Os`, or `-Ofast` (default: `-O2`)
    - **debug**: Include debug symbols (default: `true`)
    - **c_standard**: C language standard, e.g., `c11`, `c17` (default: `c11`)
    - **cpp_standard**: C++ language standard, e.g., `c++17`, `c++20` (default: `c++17`)

- **linker**:
    - **libraries**: Space-separated library names without `-l` prefix (default: `kipr pthread m z`)
    - **flags**: Additional linker flags (default: empty)

- **directories**:
    - **source**: Source directory (default: `src`)
    - **include**: Include directory (default: `include`)
    - **output**: Output directory (default: `out`)
    - **objects**: Object files subdirectory (default: `obj`)
    - **build**: Build artifacts subdirectory (default: `build`)

- **output_name**: Name of the output executable (default: `botball_user_program`)

- **extra_args**: Additional compiler/linker arguments as a list (default: `[]`)

### Example Configurations

**Debug build:**

```yaml
compiler:
    optimization: "-Og"
    debug: true
    flags: "-Wall -Wextra"
```

**Release build:**

```yaml
compiler:
    optimization: "-O3"
    debug: false
    flags: "-Wall"
```

**Custom preprocessor defines:**

```yaml
extra_args:
    - "-DDEBUG"
    - "-DVERSION=1.0"
```

## Required Tools and Dependencies

To build the project, you will need:

- Docker
- Python 3 (no external packages required)
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

- `--clean`: removes `out/` before building, then builds fresh into `out/build`.
- `--clean-only`: removes `out/` and exits without building.
- `--verbose` or `-v`: prints the full compiler and docker commands and enables compiler verbosity.
- `--ci`: run the container as root (for CI runners where mounted workspace perms are restrictive).
- `--config <path>`: specify a custom configuration file path (default: `configs/config.dev.yaml`).

You can still pass extra compiler/linker flags after `--`:

Example:

```sh
# Default development build (uses configs/config.dev.yaml)
python3 build.py

# Development build with verbose output
python3 build.py --verbose

# Production build with clean
python3 build.py --config configs/config.prod.yaml --clean

# Development build with custom preprocessor defines
python3 build.py -- -DDEBUG -DVERSION=1.0

# Clean only
python3 build.py --clean-only

# CI build (production)
python3 build.py --config configs/config.prod.yaml --ci
```

Note: The legacy CMake and custom Dockerfile flow are deprecated and no longer used.
