# Build Instructions

## Build System

Project XBOT uses **Zig** as its build system and cross-compiler. It links against the pre-built `libkipr.so` from the official [KIPR Wombat OS](https://github.com/kipr/wombat-os) image using the real libwallaby headers — no Docker, no CMake, no source compilation of libwallaby.

An optional **Nix flake** is provided for a reproducible development environment.

## Prerequisites

### Option A: Install Zig directly (recommended)

Download Zig (≥ 0.15) from [ziglang.org/download](https://ziglang.org/download/) and add it to your `PATH`. Works on Linux, macOS, and Windows.

### Option B: Nix + direnv

Install [Nix](https://nixos.org/download.html) and [direnv](https://direnv.net/), then:

```sh
cd Project-XBOT
direnv allow   # activates the Nix shell automatically
```

## Building

### Default Build (Debug, aarch64-linux)

```sh
zig build
```

Output: `zig-out/bin/botball_user_program`

### Production Build

```sh
zig build -Doptimize=ReleaseFast
```

### All Optimization Modes

| Flag                       | Description                              |
|----------------------------|------------------------------------------|
| *(none)*                   | Debug — fast compile, safety checks      |
| `-Doptimize=ReleaseSafe`   | Optimized with safety checks             |
| `-Doptimize=ReleaseFast`   | Maximum performance                      |
| `-Doptimize=ReleaseSmall`  | Optimized for binary size                |

## How It Works

The build system:

1. **Compiles** your C/C++ source files in `src/` using Zig's cross-compiler targeting `aarch64-linux-gnu`
2. **Links** against the pre-built `libkipr.so` (from `lib/`) for symbol resolution at build time
3. **Produces** a binary that dynamically links only against `libkipr.so` and standard system libraries

The C++ standard library is statically linked by Zig. At runtime on the Wombat, `libkipr.so` is already installed at `/usr/lib/libkipr.so`.

### Headers and Library

The `include/kipr/` directory contains the **real** libwallaby headers extracted from the official KIPR Wombat OS `kipr.deb` package. The `lib/libkipr.so` is the pre-built aarch64 shared library from the same package.

These come from: https://github.com/kipr/wombat-os

## Source Files

Place your source files in the `src/` directory. The build system automatically discovers:

- `.c` files — compiled as C11
- `.cpp`, `.cc`, `.cxx` files — compiled as C++17

Header files go in the `include/` directory.

## GitHub Actions

### CI (every push / pull request)

Builds with `-Doptimize=ReleaseFast` and uploads the binary as an artifact.

### Release (on `v*` tag push)

Builds with `-Doptimize=ReleaseFast` and creates a GitHub Release with the binary attached.

## Updating libwallaby

To update the headers and library to a newer version:

1. Download the latest `kipr.deb` from [kipr/wombat-os](https://github.com/kipr/wombat-os/tree/main/updateFiles/pkgs)
2. Extract it: `ar x kipr.deb && tar xzf data.tar.gz`
3. Copy headers: `cp -r usr/include/kipr include/kipr`
4. Copy library: `cp usr/lib/libkipr.so lib/`

## Troubleshooting

### Build fails with "Could not open source directory"

Ensure the `src/` directory exists and contains at least one `.c`, `.cpp`, `.cc`, or `.cxx` file.

### Zig not found

Install Zig from [ziglang.org/download](https://ziglang.org/download/) or use `nix develop` to enter the Nix shell.

### "undefined symbol" errors

Make sure the function you're calling exists in the libwallaby headers (`include/kipr/`). The `lib/libkipr.so` must match the headers.
