const std = @import("std");

pub fn build(b: *std.Build) void {
    // ── Target & optimisation ────────────────────────────────────────
    // Default: aarch64-linux-gnu (KIPR Wombat).  Override with -Dtarget=…
    const target = b.standardTargetOptions(.{
        .default_target = .{
            .cpu_arch = .aarch64,
            .os_tag = .linux,
            .abi = .gnu,
        },
    });
    const optimize = b.option(std.builtin.OptimizeMode, "optimize", "Prioritize performance, safety, or binary size") orelse .ReleaseFast;
    std.log.info("Build target: {s}-{s}-{s}, optimize: {s}", .{
        @tagName(target.result.cpu.arch),
        @tagName(target.result.os.tag),
        @tagName(target.result.abi),
        @tagName(optimize),
    });

    // ── Extract KIPR SDK (cross-platform, pure Zig) ──────────────────
    // Compiles a small host-native tool that unpacks the headers and
    // pre-built libkipr.so from the wombat-os kipr.deb — no `sh`, `ar`,
    // or `tar` CLI needed, so this works on Windows, macOS, and Linux.
    const wombat_dep = b.dependency("wombat_os", .{});

    const extractor = b.addExecutable(.{
        .name = "extract_kipr",
        .root_module = b.createModule(.{
            .root_source_file = b.path("build/extract_kipr.zig"),
            .target = b.graph.host,
        }),
    });

    const extract_step = b.addRunArtifact(extractor);
    extract_step.addFileArg(wombat_dep.path("updateFiles/pkgs/kipr.deb"));
    const sdk_root = extract_step.addOutputDirectoryArg("kipr_sdk");

    const kipr_include = sdk_root.path(b, "usr/include");
    const kipr_lib = sdk_root.path(b, "usr/lib");

    // ── Detect language mode and source files ────────────────────────
    // Single scan for entrypoint + C/C++ files to reduce build-script work.
    const sources = collectSources(b, "src");
    const has_zig_main = sources.has_zig_main;
    const c_files = sources.c_files;
    const cpp_files = sources.cpp_files;
    const libraries = collectLibraries(b);

    // ── User executable ──────────────────────────────────────────────
    const has_cpp = cpp_files.len > 0 or hasCppLib(libraries);

    const exe = b.addExecutable(.{
        .name = "botball_user_program",
        .root_module = b.createModule(.{
            .root_source_file = if (has_zig_main) b.path("src/main.zig") else null,
            .target = target,
            .optimize = optimize,
            // libc is always needed (libkipr.so depends on it).
            // libc++ is only linked when C++ source files are present,
            // keeping pure-Zig builds as static as possible.
            .link_libc = true,
            .link_libcpp = if (has_cpp) true else null,
        }),
    });

    // KIPR SDK paths (extracted at build time)
    exe.addIncludePath(kipr_include);
    exe.addLibraryPath(kipr_lib);
    exe.addRPath(.{ .cwd_relative = "/usr/lib" });
    exe.linkSystemLibrary("kipr");

    // Compile any C source files in src/
    if (c_files.len > 0) {
        exe.addCSourceFiles(.{
            .root = b.path("src"),
            .files = c_files,
            .flags = &.{ "-std=c11", "-Wall", "-Wextra" },
        });
    }

    // Link C++ source files (already collected above)
    if (has_cpp) {
        exe.linkLibCpp();
    }
    if (cpp_files.len > 0) {
        exe.addCSourceFiles(.{
            .root = b.path("src"),
            .files = cpp_files,
            .flags = &.{ "-std=c++17", "-Wall", "-Wextra" },
        });
    }

    // Compile/import linked package dependencies fetched via `zig fetch`.
    for (libraries) |lib| {
        std.log.info("Including library dependency: {s}", .{lib.name});

        if (lib.zig_module) |mod| {
            exe.root_module.addImport(lib.name, mod);
        }

        if (lib.c_files.len > 0 or lib.cpp_files.len > 0) {
            exe.addIncludePath(lib.include_root);
            exe.addIncludePath(lib.src_root);
            const dep_static = b.addLibrary(.{
                .linkage = .static,
                .name = b.fmt("{s}_lib", .{lib.name}),
                .root_module = b.createModule(.{
                    .target = target,
                    .optimize = optimize,
                    .link_libc = true,
                    .link_libcpp = if (lib.cpp_files.len > 0) true else null,
                }),
            });

            dep_static.addIncludePath(kipr_include);
            dep_static.addIncludePath(lib.include_root);
            dep_static.addIncludePath(lib.src_root);
            if (lib.cpp_files.len > 0) dep_static.linkLibCpp();

            if (lib.c_files.len > 0) {
                dep_static.addCSourceFiles(.{
                    .root = lib.src_root,
                    .files = lib.c_files,
                    .flags = &.{ "-std=c11", "-Wall", "-Wextra" },
                });
            }

            if (lib.cpp_files.len > 0) {
                dep_static.addCSourceFiles(.{
                    .root = lib.src_root,
                    .files = lib.cpp_files,
                    .flags = &.{ "-std=c++17", "-Wall", "-Wextra" },
                });
            }

            exe.linkLibrary(dep_static);
        }
    }

    b.installArtifact(exe);

    // ── Run step ─────────────────────────────────────────────────────
    // Only define a `run` step when the build target matches the host.
    const tgt = target.result;
    const host = b.graph.host.result;

    if (tgt.cpu.arch == host.cpu.arch and
        tgt.os.tag == host.os.tag and
        tgt.abi == host.abi)
    {
        const run_cmd = b.addRunArtifact(exe);
        run_cmd.step.dependOn(b.getInstallStep());
        if (b.args) |args| run_cmd.addArgs(args);
        const run_step = b.step("run", "Run the executable");
        run_step.dependOn(&run_cmd.step);
    }

    // ── Validate source set ───────────────────────────────────────────
    if (!has_zig_main and c_files.len == 0 and cpp_files.len == 0) {
        std.debug.print(
            \\error: no executable entry point found in src/.
            \\       Add at least one of:
            \\         src/main.zig                         (Zig entry point)
            \\         src/*.c / *.cpp / *.cc / *.cxx      (C/C++ sources)
            \\
        , .{});
        std.process.exit(1);
    }

    const clean_step = b.step("clean", "Remove build artifacts and cached SDK");
    clean_step.makeFn = cleanArtifacts;
}

// ── Helpers ──────────────────────────────────────────────────────────

const SourceSet = struct {
    has_zig_main: bool,
    c_files: []const []const u8,
    cpp_files: []const []const u8,
};

const LibraryDependency = struct {
    name: []const u8,
    include_root: std.Build.LazyPath,
    src_root: std.Build.LazyPath,
    c_files: []const []const u8,
    cpp_files: []const []const u8,
    zig_module: ?*std.Build.Module,
};

fn hasCppLib(libs: []const LibraryDependency) bool {
    for (libs) |lib| {
        if (lib.cpp_files.len > 0) return true;
    }
    return false;
}

/// Collect library dependencies from build.zig.zon (except wombat_os).
/// Expected package layout:
///   src/root.zig (for Zig modules, as in `zig init`)
///   include/  (public headers)
///   src/      (C/C++ sources)
fn collectLibraries(b: *std.Build) []const LibraryDependency {
    var libs: std.ArrayList(LibraryDependency) = .{};

    for (b.available_deps) |dep_info| {
        const dep_name = dep_info[0];
        const dep_hash = dep_info[1];
        if (std.mem.eql(u8, dep_name, "wombat_os")) continue;

        const dep_root = b.pathJoin(&.{ ".zig-cache", "p", dep_hash });
        const dep_src = b.pathJoin(&.{ dep_root, "src" });
        const dep_include = b.pathJoin(&.{ dep_root, "include" });
        const dep_sources = collectSources(b, dep_src);
        const dep_root_zig = b.pathJoin(&.{ dep_src, "root.zig" });
        const zig_module = if (fileExists(dep_root_zig))
            b.createModule(.{
                .root_source_file = .{ .cwd_relative = dep_root_zig },
            })
        else
            null;
        if (dep_sources.c_files.len == 0 and dep_sources.cpp_files.len == 0 and zig_module == null) continue;

        libs.append(
            b.allocator,
            .{
                .name = dep_name,
                .include_root = .{ .cwd_relative = dep_include },
                .src_root = .{ .cwd_relative = dep_src },
                .c_files = dep_sources.c_files,
                .cpp_files = dep_sources.cpp_files,
                .zig_module = zig_module,
            },
        ) catch @panic("OOM");
    }

    appendClonedLibraries(b, &libs);

    return libs.toOwnedSlice(b.allocator) catch &.{};
}

fn appendClonedLibraries(b: *std.Build, libs: *std.ArrayList(LibraryDependency)) void {
    var lib_dir = std.fs.cwd().openDir("lib", .{ .iterate = true }) catch return;
    defer lib_dir.close();

    var it = lib_dir.iterate();
    while (it.next() catch null) |entry| {
        if (entry.kind != .directory) continue;

        const root = b.pathJoin(&.{ "lib", entry.name });
        const src_path = b.pathJoin(&.{ root, "src" });
        const include_path = b.pathJoin(&.{ root, "include" });
        const sources = collectSources(b, src_path);
        if (sources.c_files.len == 0 and sources.cpp_files.len == 0) continue;

        libs.append(
            b.allocator,
            .{
                .name = b.allocator.dupe(u8, entry.name) catch @panic("OOM"),
                .include_root = .{ .cwd_relative = include_path },
                .src_root = .{ .cwd_relative = src_path },
                .c_files = sources.c_files,
                .cpp_files = sources.cpp_files,
                .zig_module = null,
            },
        ) catch @panic("OOM");
    }
}

fn fileExists(path: []const u8) bool {
    std.fs.cwd().access(path, .{}) catch return false;
    return true;
}

/// Scan `dir_path` once for `main.zig`, C, and C++ source files.
fn collectSources(b: *std.Build, dir_path: []const u8) SourceSet {
    var c_files: std.ArrayList([]const u8) = .{};
    var cpp_files: std.ArrayList([]const u8) = .{};
    var has_zig_main = false;

    var dir = (if (std.fs.path.isAbsolute(dir_path))
        std.fs.openDirAbsolute(dir_path, .{ .iterate = true })
    else
        std.fs.cwd().openDir(dir_path, .{ .iterate = true })) catch
        return .{
            .has_zig_main = false,
            .c_files = &.{},
            .cpp_files = &.{},
        };
    defer dir.close();

    var it = dir.iterate();
    while (it.next() catch null) |entry| {
        if (entry.kind != .file) continue;
        if (std.mem.eql(u8, entry.name, "main.zig")) has_zig_main = true;

        const ext = std.fs.path.extension(entry.name);
        if (std.mem.eql(u8, ext, ".c")) {
            c_files.append(
                b.allocator,
                b.allocator.dupe(u8, entry.name) catch @panic("OOM"),
            ) catch @panic("OOM");
            continue;
        }

        const is_cpp = std.mem.eql(u8, ext, ".cpp") or
            std.mem.eql(u8, ext, ".cc") or
            std.mem.eql(u8, ext, ".cxx");
        if (!is_cpp) continue;

        cpp_files.append(
            b.allocator,
            b.allocator.dupe(u8, entry.name) catch @panic("OOM"),
        ) catch @panic("OOM");
    }

    return .{
        .has_zig_main = has_zig_main,
        .c_files = c_files.toOwnedSlice(b.allocator) catch &.{},
        .cpp_files = cpp_files.toOwnedSlice(b.allocator) catch &.{},
    };
}

fn cleanArtifacts(step: *std.Build.Step, options: std.Build.Step.MakeOptions) !void {
    _ = options;
    const b = step.owner;
    const cwd = std.fs.cwd();
    const paths = [_][]const u8{
        "zig-out",
        ".zig-cache",
        "zig-cache",
    };

    for (paths) |path| {
        cwd.deleteTree(path) catch {
            std.log.info("Clean: {s} (not present)", .{path});
            continue;
        };
        std.log.info("Clean: removed {s}", .{path});
    }

    std.log.info("Clean complete.", .{});
    _ = b; // unused for now; reserved for future cache-aware cleanups
}
