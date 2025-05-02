FROM sillyfreak/wombat-cross

USER root
# Install cmake and build essentials without interactive prompts
ENV DEBIAN_FRONTEND=noninteractive

# Install cross-compilation toolchain and dependencies
RUN apt-get update && \
    # Configure tzdata non-interactively
    echo 'Etc/UTC' > /etc/timezone && \
    apt-get install -y --no-install-recommends tzdata && \
    # Install required packages and cross-compilation tools
    apt-get install -y \
    cmake \
    build-essential \
    gcc-aarch64-linux-gnu \
    g++-aarch64-linux-gnu \
    libc6-dev-arm64-cross \
    crossbuild-essential-arm64 \
    binutils-aarch64-linux-gnu \
    libstdc++-10-dev-arm64-cross \
    gcc-10-aarch64-linux-gnu \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Find and display information about KIPR libraries and ARM libraries for debugging
RUN echo "Searching for KIPR libraries..." && \
    find / -name "libkipr*" 2>/dev/null || echo "No libkipr files found" && \
    echo "Checking ARM library directories:" && \
    ls -la /usr/aarch64-linux-gnu/lib || echo "Directory not found" && \
    ls -la /usr/lib/aarch64-linux-gnu || echo "Directory not found" && \
    echo "Looking for C library:" && \
    find / -name "libc.so.6" | grep aarch64 || echo "No ARM libc found" && \
    echo "Checking additional library locations:" && \
    ls -la /usr/local/lib || echo "Directory not found" && \
    ls -la /usr/local/lib/aarch64-linux-gnu || echo "Directory not found" && \
    echo "All .so files in /usr/lib:" && \
    find /usr/lib -name "*.so" | sort && \
    echo "Information about libkipr.so:" && \
    file /usr/lib/libkipr.so || echo "File not found" && \
    echo "All available ARM libraries:" && \
    find / -name "*.so" | grep aarch64 || echo "No ARM libraries found"

# Create ARM64 library directories and copy libkipr.so to the correct ARM64 location
RUN mkdir -p /usr/lib/aarch64-linux-gnu && \
    cp /usr/lib/libkipr.so /usr/lib/aarch64-linux-gnu/ && \
    # Create a symlink if needed
    ln -sf /usr/lib/aarch64-linux-gnu/libkipr.so /usr/lib/aarch64-linux-gnu/libkipr.so.0 && \
    # Verify the copy was successful and check file format
    ls -la /usr/lib/aarch64-linux-gnu/libkipr* && \
    file /usr/lib/aarch64-linux-gnu/libkipr.so && \
    # Ensure the directory is in the library path
    echo "/usr/lib/aarch64-linux-gnu" > /etc/ld.so.conf.d/aarch64-libs.conf && \
    # Create additional symlinks to standard library paths
    mkdir -p /usr/aarch64-linux-gnu/lib && \
    ln -sf /usr/lib/aarch64-linux-gnu/libkipr.so /usr/aarch64-linux-gnu/lib/libkipr.so && \
    # Update library cache
    ldconfig

WORKDIR /app
COPY . .

# Verify aarch64-linux-gnu-gcc works with the correct libraries
RUN echo "Testing ARM64 compiler and library setup:" && \
    echo '#include <stdio.h>\nint main() { printf("Hello ARM64\\n"); return 0; }' > /tmp/test.c && \
    aarch64-linux-gnu-gcc -v /tmp/test.c -o /tmp/test && \
    file /tmp/test && \
    echo "Verifying library path configuration:" && \
    aarch64-linux-gnu-gcc -print-search-dirs | grep libraries && \
    echo "Ready for cross-compilation with aarch64-linux-gnu-gcc"
