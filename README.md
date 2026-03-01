# Project XBOT

Cross-compilation build system for the [KIPR Wombat](https://www.kipr.org/kipr/hardware-software/wombat) robot controller. Write your code in **C**, **C++**, or **Zig** and produce an `aarch64-linux` binary that runs directly on the Wombat — no Docker required.

## Quick Start

### Prerequisites

- **[Zig](https://ziglang.org/download/)** (≥ 0.14)
- **[Nix](https://nixos.org/download.html)** + **[direnv](https://direnv.net/)** *(optional, but recommended for a reproducible environment)*

With Nix and direnv installed, simply `cd` into the project directory and the environment activates automatically. Otherwise, install Zig manually.

### Build

```sh
# Debug build (default) — fast compile, safety checks
zig build

# Production build — maximum performance
zig build -Doptimize=ReleaseFast

# Build for the host machine (useful for local testing without Wombat hardware)
zig build -Dtarget=native
```

The output binary is at `zig-out/bin/botball_user_program`.

### Project Layout

```
your-project/
├── build.zig          # Build configuration (cross-compilation settings)
├── build.zig.zon      # Package manifest and dependencies
├── flake.nix          # Nix flake for reproducible dev environment
├── .envrc             # direnv — auto-activates the Nix shell
├── include/           # Header files (libwallaby stubs included)
│   └── kipr/
│       └── wombat.h
├── src/               # Your source code (C, C++, or Zig)
│   ├── main.cpp
│   └── _init_helper.c
└── docs/
    └── build.md       # Detailed build documentation
```

### Adding Source Files

Place `.c`, `.cpp`, `.cc`, or `.cxx` files in the `src/` directory — the build system discovers them automatically. Header files go in `include/`.

## Using Full libwallaby Headers

A minimal stub header is provided in `include/kipr/wombat.h`. To use the complete libwallaby v1.0.0 headers:

```sh
zig fetch --save=libwallaby https://github.com/kipr/libwallaby/archive/refs/tags/v1.0.0.tar.gz
```

This downloads the headers and records the dependency hash in `build.zig.zon`. The build system automatically uses them on the next build.

## Adding Libraries

User-made libraries hosted on GitHub (or any URL) can be added as Zig dependencies:

```sh
zig fetch --save=my_library https://github.com/user/my-library/archive/refs/tags/v1.0.0.tar.gz
```

Then reference the dependency in `build.zig`:

```zig
if (b.lazyDependency("my_library", .{})) |dep| {
    exe.addIncludePath(dep.path("include"));
}
```

Dependencies are version-locked via the hash in `build.zig.zon`. Update a library by re-running `zig fetch --save` with a new URL.

## GitHub Actions

CI automatically builds on every push and pull request. Tagged releases (`v*`) create a GitHub Release with the compiled binary.

## Platform Support

| Platform            | Status |
|---------------------|--------|
| Linux (x86_64)      | ✅     |
| macOS (Apple Silicon)| ✅    |
| macOS (Intel)       | ✅     |
| Windows (WSL + Nix) | ✅     |
| Windows (native Zig)| ✅     |

The cross-compilation targets `aarch64-linux-gnu` regardless of the host platform.

## Documentation

See [`docs/build.md`](docs/build.md) for detailed build instructions, configuration options, and troubleshooting.