# Build Instructions

## Overview

Project XBOT uses **Zig** as both its build system and cross-compiler. The KIPR SDK (headers + pre-built `libkipr.so`) is **fetched automatically** from the official [KIPR Wombat OS](https://github.com/kipr/wombat-os) repository at build time using a **pure-Zig extraction tool** — no shell commands, no platform-specific tools.

This means `zig build` works identically on **Windows**, **macOS**, and **Linux**.
Build output now reports whether the cached SDK is reused or freshly extracted.

## Prerequisites

### Option A: Install Zig directly (recommended)

Download Zig 0.15.2 or later from [ziglang.org/download](https://ziglang.org/download/) and add it to your `PATH`. Works on all platforms (Windows, macOS, Linux).

### Option B: Nix + direnv (Linux / macOS only)

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

### Clean

```sh
zig build clean
```

Removes `zig-out/`, `zig-cache/`, and any extracted KIPR SDK cache created by the build.

### All Optimization Modes

| Flag                       | Description                              |
|----------------------------|------------------------------------------|
| *(none)*                   | Debug — fast compile, safety checks      |
| `-Doptimize=ReleaseSafe`   | Optimized with safety checks             |
| `-Doptimize=ReleaseFast`   | Maximum performance                      |
| `-Doptimize=ReleaseSmall`  | Optimized for binary size                |

## How It Works

On the first build, the Zig package manager downloads the pinned wombat-os release tarball (cached after first fetch). Then:

1. **`build/extract_kipr.zig`** is compiled for the host and executed
2. It parses the `ar` archive format, decompresses gzip, and extracts the tar — all in pure Zig
3. Headers land in the build cache at `usr/include/kipr/`; `libkipr.so` at `usr/lib/`
4. Your source files are cross-compiled to `aarch64-linux-gnu`
5. The binary is linked against `libkipr.so` for symbol resolution

At runtime on the Wombat, `libkipr.so` is already installed at `/usr/lib/libkipr.so`.

### Static vs Dynamic Linking

The build is as static as possible. The only dynamic dependencies are the ones required by the Wombat runtime:

| Library | Linking | Why |
|---------|---------|-----|
| Zig standard library | **Static** | Compiled into the binary |
| libc++ (C++ runtime) | **Static** | Only included when `.cpp` files are present; omitted in pure-Zig mode |
| `libkipr.so` | Dynamic | Pre-built shared library on the Wombat |
| `libc.so.6` / `libpthread.so.0` | Dynamic | glibc — required by `libkipr.so` on the Wombat |

In pure-Zig mode (no `.cpp` files), the binary has **zero** static C++ overhead.

## Language Support

### Zig (default)

Write your code in `src/main.zig`. KIPR bindings are generated at compile time via `@cImport`:

```zig
const wombat = @cImport(@cInclude("kipr/wombat.h"));

pub fn main() void {
    wombat.motor(0, 100);
    wombat.msleep(1000);
    wombat.ao();
}
```

The bindings update automatically when the SDK version changes — no manual maintenance.

### C / C++

Delete `src/main.zig` and add `.c` / `.cpp` / `.cc` / `.cxx` files to `src/`. They are discovered and compiled automatically.

- `.c` files are compiled as C11
- `.cpp`, `.cc`, `.cxx` files are compiled as C++17

Use `#include <kipr/wombat.h>` to access the KIPR API.

### Mixed (Zig + C/C++)

When `src/main.zig` exists, it becomes the entry point. Any C/C++ files in `src/` are still compiled and linked alongside the Zig code — useful for gradual migration or calling C helpers.

## Updating the KIPR SDK

```sh
zig fetch --save=wombat_os https://github.com/kipr/wombat-os/archive/refs/tags/<NEW_TAG>.tar.gz
```

This updates the URL and content hash in `build.zig.zon`.

## GitHub Actions

| Workflow | Trigger | What it does |
|----------|---------|--------------|
| CI | Push to `main`, pull requests | Builds with ReleaseFast, uploads artifact |
| Release | Push `v*` tag | Builds with ReleaseFast, creates GitHub Release |

## Troubleshooting

### First build is slow

The first build downloads the wombat-os tarball (~50 MB). Subsequent builds use the Zig package cache.

### Build fails with "Could not open source directory"

Ensure `src/` exists and contains at least one source file (`.zig`, `.c`, `.cpp`, `.cc`, or `.cxx`).

### Zig not found

Install Zig from [ziglang.org/download](https://ziglang.org/download/) or use `nix develop`.

### "undefined symbol" errors

The function may not exist in the current libwallaby version. Update the SDK with `zig fetch --save=wombat_os …`.

### Windows: "use initWithAllocator instead"

If you see this error, you are running an older version of the extractor. Pull the latest code — the build tools use `argsWithAllocator` for cross-platform arg parsing.

### Windows: installing Zig

The recommended way to install Zig on Windows is via [WinGet](https://learn.microsoft.com/en-us/windows/package-manager/winget/):

```powershell
winget install zig.zig
```

Alternatively, download the `.zip` from [ziglang.org/download](https://ziglang.org/download/) and add the folder to your `PATH`.
