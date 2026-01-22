cmake_minimum_required(VERSION 3.10)

# Simple cross-compilation setup - set these before project() call
set(CMAKE_SYSTEM_NAME Linux)
set(CMAKE_SYSTEM_PROCESSOR aarch64)
set(CMAKE_C_COMPILER aarch64-linux-gnu-gcc)
set(CMAKE_CXX_COMPILER aarch64-linux-gnu-g++)

# Library paths for ARM64
link_directories("/usr/lib/aarch64-linux-gnu" "/lib/aarch64-linux-gnu")

# Project definition
project(Project-X C CXX)

# Compiler flags matching the command line approach
set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -Wall")
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wall")

# C standard
set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)

# C++ standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Output directory
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR})

# Add source files
file(GLOB SOURCES
    "src/*.c"
    "src/*.cpp"
)

# Add header files
include_directories(include)

# Create executable with fixed name "botball_user_program"
add_executable(botball_user_program ${SOURCES})

# Link libraries matching the command line approach exactly
target_link_libraries(botball_user_program
    PRIVATE
    kipr
    pthread
    m
    z
)
