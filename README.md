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

### Libraries via `zig fetch` (C, C++, Zig)

You can fetch helper libraries as Zig package dependencies and use them directly in **Zig**, **C**, or **C++** projects.

> All dependency compilation is performed by Zig's build graph (no CMake/Make), so the workflow stays cross-platform on Windows/macOS/Linux.

1. Fetch and save the dependency in `build.zig.zon`:

```sh
zig fetch --save=wombat_drivetrain https://github.com/cdenihan/Wombat-DriveTrain/archive/refs/heads/main.tar.gz
```

2. Use the library in your code.

For a Zig library dependency:

```zig
// Zig library (project created with `zig init`)
const drivetrain = @import("wombat_drivetrain");
```

For a C/C++ library dependency:

```zig
const drivetrain_c = @cImport({
    @cInclude("your_library_header.h");
});
```

3. Build normally with `zig build`.

#### Detailed integration behavior

At build time, Project XBOT reads all dependencies in `build.zig.zon` (except `wombat_os`) and:

1. **Zig module wiring**
   - If a dependency exports a module whose name matches the dependency key, it is imported via `@import("<dependency_key>")`.
2. **C/C++ source discovery**
   - If dependency `src/` contains `.c`, `.cpp`, `.cc`, or `.cxx`, those files are discovered automatically.
3. **Zig-built static library creation**
   - Project XBOT compiles each C/C++ dependency into its own static library using Zig (`b.addLibrary(..., .linkage = .static)`), then links it into your program.
4. **Include path setup**
   - `include/` and `src/` are added so headers can be included from your app sources.
5. **C++ runtime handling**
   - libc++ is linked only when C++ sources are present (in your app or dependencies).

#### Supported dependency layouts

Zig library (recommended: `zig init` style):

```text
<library>/
├── build.zig
└── src/
    └── root.zig
```

C/C++ library:

```text
<library>/
├── include/
└── src/  # .c/.cpp/.cc/.cxx
```

#### Project-language compatibility

- **Zig project (`src/main.zig`)**: can use `@import("<dep>")` and/or `@cImport` headers from fetched libraries.
- **C project (`src/main.c`)**: can include dependency headers from `include/` and link against the Zig-built static dependency libs automatically.
- **C++ project (`src/main.cpp/.cc/.cxx`)**: same as C, with automatic libc++ support when needed.

#### Caching and speed

Builds stay fast because Zig caches both:
- dependency downloads (`zig fetch` package cache)
- compiled outputs (including per-dependency static libraries)

Only changed inputs are rebuilt.

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
- **Sync Template** — checks weekly for upstream template and SDK updates, opens PRs

## Platform Support

| Platform              | Status |
| --------------------- | ------ |
| Linux (x86_64)        | ✅     |
| macOS (Apple Silicon) | ✅     |
| macOS (Intel)         | ✅     |
| Windows (native)      | ✅     |

The same `zig build` command works on all platforms — Zig handles cross-compilation natively.

## Automatic Updates

This project was created from the [Project XBOT](https://github.com/cdenihan/Project-XBOT) template. A GitHub Actions workflow runs weekly to keep your project up to date automatically — you just focus on writing code.

### What gets updated

| What | How | PR branch |
| --- | --- | --- |
| **Build scripts, CI, configs, docs** | Synced from the latest tagged template release | `auto/sync-template` |
| **KIPR SDK (`wombat_os`)** | Updated when a new [wombat-os](https://github.com/kipr/wombat-os) release is published | `auto/update-wombat-os` |

- **Automatic** — runs every Monday; creates a PR only when updates are available
- **Manual** — trigger from the Actions tab → *Sync Template* → *Run workflow*
- **Stable** — always syncs from tagged releases, never from unstable branches
- **Safe** — your source code in `src/`, project metadata in `build.zig.zon`, and `README.md` are never overwritten by the template sync

The `.xbot-version` file tracks which template version your project is based on.

> **Note:** The workflow requires the repository setting *Allow GitHub Actions to create and approve pull requests* to be enabled under **Settings → Actions → General**.

## Documentation

See [`docs/build.md`](docs/build.md) for detailed build instructions, configuration options, and troubleshooting.
