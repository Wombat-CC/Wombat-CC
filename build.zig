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
    const optimize = b.standardOptimizeOption(.{});

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

    // ── User executable ──────────────────────────────────────────────
    const has_cpp = cpp_files.len > 0;

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
        exe.addCSourceFiles(.{
            .root = b.path("src"),
            .files = cpp_files,
            .flags = &.{ "-std=c++17", "-Wall", "-Wextra" },
        });
    }

    b.installArtifact(exe);

    // ── Run step ─────────────────────────────────────────────────────
    const run_cmd = b.addRunArtifact(exe);
    run_cmd.step.dependOn(b.getInstallStep());
    if (b.args) |args| run_cmd.addArgs(args);
    const run_step = b.step("run", "Run the executable");
    run_step.dependOn(&run_cmd.step);
}

// ── Helpers ──────────────────────────────────────────────────────────

const SourceSet = struct {
    has_zig_main: bool,
    c_files: []const []const u8,
    cpp_files: []const []const u8,
};

/// Scan `dir_path` once for `main.zig`, C, and C++ source files.
fn collectSources(b: *std.Build, dir_path: []const u8) SourceSet {
    var c_files: std.ArrayList([]const u8) = .{};
    var cpp_files: std.ArrayList([]const u8) = .{};
    var has_zig_main = false;

    var dir = std.fs.cwd().openDir(dir_path, .{ .iterate = true }) catch
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
