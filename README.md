# Wombat CC

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
your-project/
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

## Library Packages

The root build auto-links library dependencies whose `build.zig.zon` dependency keys (entry names) start with `wombat_cc_lib_`. Each such dependency is expected to provide:

- artifact name: `lib`
- named lazy path: `include`

This makes future fetched libraries work cleanly from day one:

```sh
zig fetch --save=wombat_cc_lib_<name> <url>
```

Use local path dependencies with the same naming and exported build interface for in-repo libraries.

### Example: local in-repo library

Add to `build.zig.zon`:

```zig
.dependencies = .{
    .wombat_cc_lib_arm = .{ .path = "lib/Arm" },
};
```

Create `lib/Arm/build.zig` that exports `lib` and `include`:

```zig
const std = @import("std");

pub fn build(b: *std.Build) void {
    const target = b.standardTargetOptions(.{});
    const optimize = b.standardOptimizeOption(.{});
    const kipr_include = b.option(std.Build.LazyPath, "kipr_include", "Path to KIPR headers") orelse
        @panic("missing required build option: -Dkipr_include");

    const lib = b.addLibrary(.{
        .linkage = .static,
        .name = "lib",
        .root_module = b.createModule(.{
            .root_source_file = null,
            .target = target,
            .optimize = optimize,
            .link_libc = true,
            .link_libcpp = true,
        }),
    });

    lib.addIncludePath(b.path("include"));
    lib.addIncludePath(kipr_include);
    lib.addCSourceFiles(.{
        .root = b.path("src"),
        .files = &.{"Arm.cpp"},
        .flags = &.{ "-std=c++17", "-Wall", "-Wextra" },
    });

    b.addNamedLazyPath("include", b.path("include"));
    b.installArtifact(lib);
}
```

### Example: fetched library

```sh
zig fetch --save=wombat_cc_lib_line_follow https://example.com/line-follow.tar.gz
zig build
```

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

This repository is a GitHub template. A GitHub Actions workflow runs weekly to keep generated projects up to date automatically — you just focus on writing code.

### What gets updated

| What | How | PR branch |
| --- | --- | --- |
| **Build scripts, CI, configs, docs** | Synced from the latest tagged template release | `auto/sync-template` |
| **KIPR SDK (`wombat_os`)** | Updated when a new [wombat-os](https://github.com/kipr/wombat-os) release is published | `auto/update-wombat-os` |

- **Automatic** — runs every Monday; creates a PR only when updates are available
- **Manual** — trigger from the Actions tab → *Sync Template* → *Run workflow*
- **Stable** — always syncs from tagged releases, never from unstable branches
- **Safe** — your source code in `src/`, project metadata in `build.zig.zon`, and `README.md` are never overwritten by the template sync

The `.wombat-cc-version` file tracks which template version your project is based on. In this template repository, it is updated automatically by the tag-release workflow.

> **Note:** The workflow requires the repository setting *Allow GitHub Actions to create and approve pull requests* to be enabled under **Settings → Actions → General**.

## Documentation

See [`docs/build.md`](docs/build.md) for detailed build instructions, configuration options, and troubleshooting.
