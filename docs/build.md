# Build Instructions

This document provides detailed instructions on how to build the project using the Zig build system.

## Build System

Project XBOT uses **Zig** as its build system and cross-compiler. Zig compiles C, C++, and Zig source code and has built-in cross-compilation support — no Docker, no separate toolchain installation.

An optional **Nix flake** is provided for a fully reproducible development environment.

## Prerequisites

### Option A: Nix + direnv (recommended)

Install [Nix](https://nixos.org/download.html) and [direnv](https://direnv.net/), then:

```sh
cd Project-XBOT
direnv allow   # activates the Nix shell automatically
```

This provides Zig and ZLS (Zig Language Server) at a pinned version.

### Option B: Manual Zig Installation

Download Zig (≥ 0.14) from [ziglang.org/download](https://ziglang.org/download/) and add it to your `PATH`. Works on Linux, macOS, and Windows.

### Option C: Nix without direnv

```sh
nix develop   # enter the dev shell manually
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

### Build for Host Machine

Useful for running locally (without Wombat hardware):

```sh
zig build -Dtarget=native
```

### All Optimization Modes

| Flag                       | Description                              |
|----------------------------|------------------------------------------|
| *(none)*                   | Debug — fast compile, safety checks      |
| `-Doptimize=ReleaseSafe`   | Optimized with safety checks             |
| `-Doptimize=ReleaseFast`   | Maximum performance                      |
| `-Doptimize=ReleaseSmall`  | Optimized for binary size                |

## Cross-Compilation

The default target is `aarch64-linux-gnu`, which matches the KIPR Wombat's ARM64 Linux environment. Zig handles cross-compilation natively — the same command works on x86_64 Linux, Apple Silicon macOS, Intel macOS, and Windows.

To verify the output binary:

```sh
file zig-out/bin/botball_user_program
# ELF 64-bit LSB executable, ARM aarch64 ...
```

## Source Files

Place your source files in the `src/` directory. The build system automatically discovers:

- `.c` files — compiled as C11
- `.cpp`, `.cc`, `.cxx` files — compiled as C++17

Header files should go in the `include/` directory.

## Dependencies

### libwallaby

A minimal stub header is included at `include/kipr/wombat.h`. For the full libwallaby v1.0.0 headers:

```sh
zig fetch --save=libwallaby https://github.com/kipr/libwallaby/archive/refs/tags/v1.0.0.tar.gz
```

This records the dependency in `build.zig.zon` with a content hash. The build system automatically adds the dependency's include path.

### User Libraries

Add any GitHub-hosted library as a dependency:

```sh
zig fetch --save=my_lib https://github.com/user/my-lib/archive/refs/tags/v1.0.0.tar.gz
```

Then reference it in `build.zig`:

```zig
if (b.lazyDependency("my_lib", .{})) |dep| {
    exe.addIncludePath(dep.path("include"));
}
```

### Updating Dependencies

Re-run `zig fetch --save=<name>` with the new URL. The hash in `build.zig.zon` updates automatically.

## GitHub Actions

### CI (every push / pull request)

Builds with `-Doptimize=ReleaseFast` and uploads the binary as an artifact.

### Release (on `v*` tag push)

Builds with `-Doptimize=ReleaseFast` and creates a GitHub Release with the binary attached.

## Nix Flake

The `flake.nix` provides a development shell with Zig and ZLS. It works on:

- Linux (x86_64, aarch64)
- macOS (Apple Silicon, Intel)
- Windows via WSL

### Commands in the Nix Shell

```sh
nix develop                # enter the shell
zig build                  # build the project
zig build -Doptimize=ReleaseFast   # production build
```

## Migrating from the Old Build System

The previous Docker + Python build system (`build.py`, `configs/`) has been replaced:

| Old                                       | New                                    |
|-------------------------------------------|----------------------------------------|
| `python3 build.py`                        | `zig build`                            |
| `python3 build.py --config config.prod.yaml` | `zig build -Doptimize=ReleaseFast`  |
| `python3 build.py --clean`                | `rm -rf zig-out .zig-cache`            |
| `python3 build.py --ci`                   | `zig build -Doptimize=ReleaseFast`     |
| Docker required                           | No Docker needed                       |
| `out/build/botball_user_program`          | `zig-out/bin/botball_user_program`     |

## Troubleshooting

### Build fails with "Could not open source directory"

Ensure the `src/` directory exists and contains at least one `.c`, `.cpp`, `.cc`, or `.cxx` file.

### Missing libwallaby headers

Run `zig fetch --save=libwallaby https://github.com/kipr/libwallaby/archive/refs/tags/v1.0.0.tar.gz` or ensure the stub header exists at `include/kipr/wombat.h`.

### Zig not found

Install Zig from [ziglang.org/download](https://ziglang.org/download/) or use `nix develop` to enter the Nix shell.
