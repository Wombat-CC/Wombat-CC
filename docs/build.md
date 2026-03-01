# Build Instructions

## Build System

Project XBOT uses **Zig** as its build system and cross-compiler. The KIPR headers and pre-built `libkipr.so` are **automatically fetched** from the official [KIPR Wombat OS](https://github.com/kipr/wombat-os) repository at build time — no manual downloads, no Docker, no CMake.

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

On the first build, the Zig package manager:

1. **Downloads** the pinned [wombat-os](https://github.com/kipr/wombat-os) release tarball (cached after first fetch)
2. **Extracts** the `kipr.deb` package from the tarball
3. **Unpacks** the official libwallaby headers and `libkipr.so` from the deb

Then, on every build:

4. **Compiles** your source files in `src/` using Zig's cross-compiler targeting `aarch64-linux-gnu`
5. **Links** against `libkipr.so` for symbol resolution at build time
6. **Produces** a binary that dynamically links only against `libkipr.so` and standard system libraries

The C++ standard library is statically linked by Zig. At runtime on the Wombat, `libkipr.so` is already installed at `/usr/lib/libkipr.so`.

## Language Support

### C / C++ (default)

Place your source files in `src/`. The build system automatically discovers:

- `.c` files — compiled as C11
- `.cpp`, `.cc`, `.cxx` files — compiled as C++17

Use `#include <kipr/wombat.h>` to access the KIPR API.

### Zig

Create `src/main.zig` to use Zig as your main language. Import the KIPR C API with:

```zig
const c = @cImport(@cInclude("kipr/wombat.h"));

pub fn main() void {
    c.ao();  // Call any libwallaby function
}
```

When `src/main.zig` exists, it becomes the entry point. C/C++ helper files in `src/` are still compiled and linked alongside it.

## Updating the KIPR SDK

The wombat-os version is pinned in `build.zig.zon`. To update:

```sh
zig fetch --save=wombat_os https://github.com/kipr/wombat-os/archive/refs/tags/<NEW_TAG>.tar.gz
```

This updates the URL and hash. The next build uses the new version automatically.

## GitHub Actions

### CI (pushes to main / pull requests)

Builds with `-Doptimize=ReleaseFast` and uploads the binary as an artifact.

### Release (on `v*` tag push)

Builds with `-Doptimize=ReleaseFast` and creates a GitHub Release with the binary attached.

## Troubleshooting

### Build fails with "Could not open source directory"

Ensure the `src/` directory exists and contains at least one source file (`.c`, `.cpp`, `.cc`, `.cxx`, or `.zig`).

### Zig not found

Install Zig from [ziglang.org/download](https://ziglang.org/download/) or use `nix develop` to enter the Nix shell.

### "undefined symbol" errors

Make sure the function you're calling exists in the libwallaby headers. Run `zig fetch --save=wombat_os ...` to update the KIPR SDK if needed.

### First build is slow

The first build downloads the wombat-os tarball (~94 MB). Subsequent builds use the cached version and are fast.
