# Project XBOT

Cross-compilation build system for the [KIPR Wombat](https://www.kipr.org/kipr/hardware-software/wombat) robot controller. Write your code in **Zig** (or C/C++) and produce an `aarch64-linux` binary that runs directly on the Wombat — no Docker required.

## Quick Start

### Prerequisites

| Platform    | Requirement                                  |
| ----------- | -------------------------------------------- |
| **Windows** | [Zig 0.15.2+](https://ziglang.org/download/) |
| **macOS**   | [Zig 0.15.2+](https://ziglang.org/download/) |
| **Linux**   | [Zig 0.15.2+](https://ziglang.org/download/) |

One tool, all platforms. Optionally, Linux and macOS users can use **[Nix](https://nixos.org/download.html)** + **[direnv](https://direnv.net/)** for a fully reproducible environment.

### Build

```sh
# Production build (ReleaseFast, default)
zig build

# Debug build
zig build -Doptimize=Debug

# Clean build outputs and cached SDK
zig build clean
```

The output binary is at `zig-out/bin/botball_user_program`.

### Project Layout

```
Project-XBOT/
├── build.zig          # Build configuration (auto-fetches KIPR SDK)
├── build.zig.zon      # Package manifest (pins wombat-os version)
├── build/
│   └── extract_kipr.zig   # Pure-Zig cross-platform SDK extractor
├── src/
│   ├── main.zig       # Your code — Zig entry point (default)
│   └── _init_helper.c # Stdout unbuffering for C/C++ mode
├── flake.nix          # Nix flake (optional dev environment)
└── docs/
    └── build.md       # Detailed build documentation
```

## Writing Code

### Zig (default)

Write your robot code in `src/main.zig`. The KIPR API bindings are **generated automatically** from the C headers at compile time via `@cImport` — as libwallaby evolves, the bindings evolve with it:

```zig
const std = @import("std");
const wombat = @cImport(@cInclude("kipr/wombat.h"));

pub fn main() void {
    std.debug.print("Hello from Zig!\n", .{});

    wombat.motor(0, 100);     // motor 0 at 100% power
    wombat.msleep(1000);      // wait 1 second
    wombat.ao();              // all off
}
```

### C / C++

Delete `src/main.zig` and place `.c`, `.cpp`, `.cc`, or `.cxx` files in `src/`. The build system discovers them automatically. Use `#include <kipr/wombat.h>` to access the KIPR API.

## How It Works

1. **Zig fetches** the pinned [wombat-os](https://github.com/kipr/wombat-os) release tarball (cached after first download)
2. **A pure-Zig build tool** extracts the `kipr.deb` package — no shell commands, works on Windows/macOS/Linux
3. **Headers and `libkipr.so`** are made available to the compiler automatically
4. **Zig cross-compiles** your code targeting `aarch64-linux-gnu`
5. **The binary** links against `libkipr.so` (already installed on every Wombat at `/usr/lib/libkipr.so`)

No KIPR files are committed to this repository. Everything is fetched and cached by the Zig package manager.
Build output clearly reports whether the cached SDK is being reused or freshly extracted.

## Updating the KIPR SDK

```sh
zig fetch --save=wombat_os https://github.com/kipr/wombat-os/archive/refs/tags/<NEW_TAG>.tar.gz
```

This updates the URL and content hash in `build.zig.zon`. The next build uses the new version.

## GitHub Actions

- **CI** — builds on pushes to `main` and on pull requests
- **Release** — tagged pushes (`v*`) create a GitHub Release with the compiled binary
- **Sync Template** — checks weekly for upstream template updates and opens a PR

## Platform Support

| Platform              | Status |
| --------------------- | ------ |
| Linux (x86_64)        | ✅     |
| macOS (Apple Silicon) | ✅     |
| macOS (Intel)         | ✅     |
| Windows (native)      | ✅     |

The same `zig build` command works on all platforms — Zig handles cross-compilation natively.

## Template Updates

This project was created from the [Project XBOT](https://github.com/cdenihan/Project-XBOT) template. When the template's build scripts, CI workflows, or documentation are updated, a GitHub Actions workflow automatically opens a pull request in your repository with the changes. Your source code in `src/` and project metadata in `build.zig.zon` are never overwritten.

- **Automatic** — the `Sync Template` workflow runs every Monday and creates a PR if updates are available
- **Manual** — trigger the workflow from the Actions tab → *Sync Template* → *Run workflow*
- **Selective** — only infrastructure files are synced; your code and project config stay untouched

The `.xbot-version` file tracks which template version your project is based on.

> **Note:** The sync workflow requires the repository setting *Allow GitHub Actions to create and approve pull requests* to be enabled under **Settings → Actions → General**.

## Documentation

See [`docs/build.md`](docs/build.md) for detailed build instructions, configuration options, and troubleshooting.
