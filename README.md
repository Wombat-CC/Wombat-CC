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
├── build.zig          # Build configuration (auto-fetches KIPR dependencies)
├── build.zig.zon      # Package manifest (pins wombat-os version)
├── flake.nix          # Nix flake (optional dev environment)
├── .envrc             # direnv auto-activation
├── src/               # Your source code
│   ├── main.cpp       # C++ entry point (default)
│   ├── _init_helper.c # Init helper
│   └── main.zig       # OR: Zig entry point (create this to use Zig instead)
└── docs/
    └── build.md
```

## Language Support

### C / C++ (default)

Place `.c`, `.cpp`, `.cc`, or `.cxx` files in `src/`. The build system discovers them automatically. Use `#include <kipr/wombat.h>` to access the KIPR API.

### Zig

Create `src/main.zig` to write your main program in Zig. Use `@cImport` to access the KIPR C API:

```zig
const std = @import("std");
const c = @cImport(@cInclude("kipr/wombat.h"));

pub fn main() void {
    std.debug.print("Hello from Zig!\n", .{});
    c.ao(); // Call any libwallaby function
}
```

When `src/main.zig` exists, it becomes the entry point. You can still have C/C++ helper files alongside it — they are compiled and linked automatically.

## How It Works

The build system:
1. **Auto-fetches** the [KIPR Wombat OS](https://github.com/kipr/wombat-os) package at build time (pinned to a specific release tag)
2. **Extracts** the official `libkipr.so` and headers from the `kipr.deb` package
3. **Cross-compiles** your source code targeting `aarch64-linux-gnu` using Zig
4. **Links** against `libkipr.so` which is already installed on every Wombat at `/usr/lib/libkipr.so`

No KIPR files are committed to this repository — they are fetched and cached automatically by Zig's package manager on the first build.

## Updating the KIPR SDK

To update to a newer wombat-os release:

```sh
zig fetch --save=wombat_os https://github.com/kipr/wombat-os/archive/refs/tags/<NEW_TAG>.tar.gz
```

This updates the URL and hash in `build.zig.zon`. The next build will use the new version.

## Adding Libraries

User-made libraries hosted on GitHub can be added as Zig dependencies:

```sh
zig fetch --save=my_library https://github.com/user/my-library/archive/refs/tags/v1.0.0.tar.gz
```

Then reference the dependency in `build.zig`. Dependencies are version-locked via the hash in `build.zig.zon`.

## GitHub Actions

CI automatically builds on pushes to `main` and on pull requests. Tagged releases (`v*`) create a GitHub Release with the compiled binary.

## Platform Support

| Platform              | Status |
|-----------------------|--------|
| Linux (x86_64)        | ✅     |
| macOS (Apple Silicon)  | ✅    |
| macOS (Intel)         | ✅     |
| Windows (WSL + Nix)   | ✅     |
| Windows (native Zig)  | ✅     |

Zig handles cross-compilation natively — the same `zig build` command works on all platforms.

## Documentation

See [`docs/build.md`](docs/build.md) for detailed build instructions, configuration options, and troubleshooting.