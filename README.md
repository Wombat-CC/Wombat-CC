# Project XBOT

Cross-compilation build system for the [KIPR Wombat](https://www.kipr.org/kipr/hardware-software/wombat) robot controller. Write your code in **C**, **C++**, or **Zig** and produce an `aarch64-linux` binary that runs directly on the Wombat — no Docker required.

## Quick Start

### Prerequisites

- **[Zig](https://ziglang.org/download/)** (≥ 0.15)
- **[Nix](https://nixos.org/download.html)** + **[direnv](https://direnv.net/)** *(optional, for a reproducible environment)*

With Nix and direnv installed, simply `cd` into the project directory and the environment activates automatically. Otherwise, [install Zig directly](https://ziglang.org/download/).

### Build

```sh
# Debug build (default)
zig build

# Production build (recommended for deploying to Wombat)
zig build -Doptimize=ReleaseFast
```

The output binary is at `zig-out/bin/botball_user_program`.

### Project Layout

```
your-project/
├── build.zig          # Build configuration (cross-compilation settings)
├── build.zig.zon      # Package manifest
├── flake.nix          # Nix flake (optional dev environment)
├── .envrc             # direnv auto-activation
├── include/           # Real libwallaby headers from KIPR Wombat OS
│   └── kipr/
│       ├── wombat.h   # Main include for user code
│       ├── motor/motor.h
│       ├── servo/servo.h
│       └── ...
├── lib/               # Pre-built libkipr.so from KIPR Wombat OS
│   └── libkipr.so
├── src/               # Your source code (C, C++, or Zig)
│   ├── main.cpp
│   └── _init_helper.c
└── docs/
    └── build.md
```

### Adding Source Files

Place `.c`, `.cpp`, `.cc`, or `.cxx` files in the `src/` directory — the build system discovers them automatically. Header files go in `include/`.

## How It Works

The build system uses:
- **Real libwallaby headers** extracted from the official [KIPR Wombat OS](https://github.com/kipr/wombat-os) image
- **Pre-built `libkipr.so`** from the same image, for link-time symbol resolution
- **Zig** as a cross-compiler targeting `aarch64-linux-gnu`

Your code is compiled and linked against `libkipr.so` which is already installed on every Wombat at `/usr/lib/libkipr.so`. The C++ standard library is statically linked — the only runtime dependencies are `libkipr.so` and standard system libraries (`libc`, `libpthread`) that exist on the Wombat.

## Adding Libraries

User-made libraries hosted on GitHub can be added as Zig dependencies:

```sh
zig fetch --save=my_library https://github.com/user/my-library/archive/refs/tags/v1.0.0.tar.gz
```

Then reference the dependency in `build.zig`. Dependencies are version-locked via the hash in `build.zig.zon`.

## GitHub Actions

CI automatically builds on every push and pull request. Tagged releases (`v*`) create a GitHub Release with the compiled binary.

## Platform Support

| Platform             | Status |
|----------------------|--------|
| Linux (x86_64)       | ✅     |
| macOS (Apple Silicon) | ✅    |
| macOS (Intel)        | ✅     |
| Windows (WSL + Nix)  | ✅     |
| Windows (native Zig) | ✅     |

Zig handles cross-compilation natively — the same `zig build` command works on all platforms.

## Documentation

See [`docs/build.md`](docs/build.md) for detailed build instructions, configuration options, and troubleshooting.