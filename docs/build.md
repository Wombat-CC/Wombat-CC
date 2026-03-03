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

### Default Build (ReleaseFast, aarch64-linux)

```sh
zig build
```

Output: `zig-out/bin/botball_user_program`

### Debug Build

```sh
zig build -Doptimize=Debug
```

### Clean

```sh
zig build clean
```

Removes `zig-out/`, `zig-cache/`, and any extracted KIPR SDK cache created by the build.

### All Optimization Modes

| Flag                       | Description                              |
|----------------------------|------------------------------------------|
| *(none)*                   | ReleaseFast — maximum performance        |
| `-Doptimize=Debug`         | Debug — fast compile, safety checks      |
| `-Doptimize=ReleaseSafe`   | Optimized with safety checks             |
| `-Doptimize=ReleaseFast`   | Maximum performance (explicit)           |
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

### Libraries fetched with Zig (C, C++, Zig)

Project XBOT supports external libraries fetched with Zig packages and consumed from Zig, C, or C++ app code.

All library compilation is handled by Zig's native build graph — no CMake/Make or platform-specific shell tooling.

#### Add a library dependency

```sh
zig fetch --save=wombat_drivetrain https://github.com/cdenihan/Wombat-DriveTrain/archive/refs/heads/main.tar.gz
```

This adds the dependency to `build.zig.zon`.

#### Library package format

For automatic integration, use one (or both) of these layouts:

```text
# Zig library (created with `zig init`)
<library>/
├── build.zig
└── src/
    └── root.zig

# C/C++ library
<library>/
├── include/          # public headers
└── src/              # .c/.cpp/.cc/.cxx sources
```

You can also have mixed dependencies (for example: a Zig module plus C/C++ sources in the same package).

#### What the build does automatically

During `zig build`, Project XBOT:

1. Reads dependencies from `build.zig.zon`
2. Skips the special `wombat_os` SDK dependency
3. For each remaining dependency:
   - imports the Zig module when the dependency exports a module with the same name as the dependency key
   - scans dependency `src/` for `.c`, `.cpp`, `.cc`, `.cxx`
   - adds `include/` and `src/` to include paths
   - compiles those C/C++ files into a Zig-built static library for the current target
   - links that static library into your application
4. Links libc++ only when any C++ sources are present

This design guarantees target compatibility for cross-compilation (for example, building `aarch64-linux-gnu` artifacts from macOS/Windows/Linux hosts).

#### Using fetched libraries in Zig projects (`src/main.zig`)

Import Zig modules and C headers directly:

```zig
const mylib = @import("wombat_drivetrain");

const mylib_c = @cImport({
    @cInclude("your_library_header.h");
});
```

Then call APIs as usual (`mylib.someFunction(...)` or `mylib_c.some_function(...)`).

#### Using fetched libraries in C/C++ projects (`src/main.c/.cpp`)

If your app entrypoint is C or C++, just include dependency headers normally:

```cpp
#include <DriveTrain.hpp>

int main() {
    DriveTrain dt(0, 1);
    dt.stop();
    return 0;
}
```

Project XBOT automatically links the dependency implementation, so no extra linker flags are needed.

#### Naming and module conventions (important)

- The dependency key used in `zig fetch --save=<key> ...` is the import name in Zig (`@import("<key>")`).
- For Zig-module auto-import, dependency build metadata should export a module matching that key.
- C/C++ dependencies should expose public headers in `include/` and implementation in `src/`.

#### Verified example: `Wombat-DriveTrain`

The following dependency has been validated with this build flow:

```sh
zig fetch --save=wombat_drivetrain https://github.com/cdenihan/Wombat-DriveTrain/archive/refs/heads/main.tar.gz
```

It is consumed as a C++ library (header in `include/DriveTrain.hpp`, implementation in `src/DriveTrain.cpp`) and is compiled/linked by Zig during the app build.

#### Performance and caching

No CMake/Make tooling is used. Everything is integrated through Zig's native build graph, which keeps builds fast and cross-platform:
- Package downloads are cached by Zig package manager
- Compiled artifacts (including per-dependency static libraries) are cached in Zig build cache
- Rebuilds are incremental and only recompile changed inputs

#### Troubleshooting library integration

##### `@import("<dep>")` fails

The dependency may not export a Zig module with the same key name. Confirm dependency build metadata/module naming.

##### Header not found (C/C++)

Ensure the dependency has headers under `include/` (or update includes to match actual header paths).

##### Undefined symbols at link time

Confirm the dependency implementation files are present in `src/` and match declared headers.

##### Build works on host but fails cross-target

Avoid prebuilt host-specific artifacts; rely on source-based dependency builds (the default in Project XBOT) so Zig compiles for the requested target.

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
| Sync Template | Weekly (Monday) / manual | Syncs infrastructure + checks for SDK updates, opens PRs |

### Sync Template workflow

The **Sync Template** workflow automatically keeps your project up to date so you can focus on writing code. It runs every Monday and can be triggered manually from the Actions tab.

It performs two independent checks:

#### 1. Template infrastructure sync

Syncs build scripts, CI workflows, and documentation from the **latest tagged release** of the upstream [Project XBOT](https://github.com/cdenihan/Project-XBOT) template.

**What gets synced:**
- `build.zig`, `build/` — build configuration and tools
- `.github/workflows/` — CI, release, and sync workflows
- `docs/` — documentation
- `.editorconfig`, `.envrc`, `.gitignore`, `flake.nix`, `flake.lock` — editor and environment configs

**What is never overwritten:**
- `src/` — your source code
- `build.zig.zon` — your project name, version, and dependency pins
- `README.md` — your project readme

When changes are detected, the workflow opens a pull request on the `auto/sync-template` branch. The `.xbot-version` file tracks which template tag your project is based on.

#### 2. KIPR SDK dependency update

Checks whether a newer [wombat-os](https://github.com/kipr/wombat-os) release is available. If so, it runs `zig fetch --save=wombat_os` to update the URL and content hash in `build.zig.zon` and opens a pull request on the `auto/update-wombat-os` branch.

After merging, the next `zig build` will download the new SDK version automatically.

#### Setup

Enable *Allow GitHub Actions to create and approve pull requests* under **Settings → Actions → General** for the workflow to create PRs.

**Manual trigger with a specific template tag:**
From the Actions tab, select *Sync Template* → *Run workflow* and optionally provide a tag name (leave empty for the latest tag).

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
