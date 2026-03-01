const std = @import("std");

pub fn build(b: *std.Build) void {
    // Default cross-compilation target: aarch64-linux-gnu for KIPR Wombat.
    // Override with: zig build -Dtarget=<triple>
    const target = b.standardTargetOptions(.{
        .default_target = .{
            .cpu_arch = .aarch64,
            .os_tag = .linux,
            .abi = .gnu,
        },
    });

    const optimize = b.standardOptimizeOption(.{});

    // --- Extract KIPR headers and library from wombat-os dependency ---
    // The wombat-os tarball contains updateFiles/pkgs/kipr.deb which has
    // the pre-built libkipr.so and real libwallaby headers.
    const wombat_dep = b.dependency("wombat_os", .{});
    const extract = b.addSystemCommand(&.{
        "sh", "-c",
        \\set -e
        \\DEB="$1"; INCDIR="$2"; LIBDIR="$3"
        \\WORK=$(mktemp -d)
        \\trap 'rm -rf "$WORK"' EXIT
        \\cd "$WORK"
        \\ar x "$DEB"
        \\tar xzf data.tar.*
        \\cp -r usr/include/* "$INCDIR/"
        \\cp usr/lib/libkipr.so "$LIBDIR/"
        ,
        "extract_kipr",
    });
    extract.addFileArg(wombat_dep.path("updateFiles/pkgs/kipr.deb"));
    const kipr_include = extract.addOutputDirectoryArg("include");
    const kipr_lib = extract.addOutputDirectoryArg("lib");

    // --- Check if user wants to write in Zig ---
    const has_zig_main = blk: {
        std.fs.cwd().access("src/main.zig", .{}) catch |err| {
            if (err != error.FileNotFound)
                std.log.warn("Could not access src/main.zig: {}; falling back to C/C++ mode", .{err});
            break :blk false;
        };
        break :blk true;
    };

    // --- User executable ---
    const exe = b.addExecutable(.{
        .name = "botball_user_program",
        .root_module = b.createModule(.{
            .root_source_file = if (has_zig_main) b.path("src/main.zig") else null,
            .target = target,
            .optimize = optimize,
            .link_libc = true,
            .link_libcpp = true,
        }),
    });

    // KIPR headers and library (extracted from wombat-os at build time)
    exe.addIncludePath(kipr_include);
    exe.addLibraryPath(kipr_lib);
    exe.addRPath(.{ .cwd_relative = "/usr/lib" });
    exe.linkSystemLibrary("kipr");

    // Discover and compile C source files from src/
    const c_files = collectSourceFiles(b, "src", .c);
    if (c_files.len > 0) {
        exe.addCSourceFiles(.{
            .root = b.path("src"),
            .files = c_files,
            .flags = &.{ "-std=c11", "-Wall", "-Wextra" },
        });
    }

    // Discover and compile C++ source files from src/
    const cpp_files = collectSourceFiles(b, "src", .cpp);
    if (cpp_files.len > 0) {
        exe.addCSourceFiles(.{
            .root = b.path("src"),
            .files = cpp_files,
            .flags = &.{ "-std=c++17", "-Wall", "-Wextra" },
        });
    }

    b.installArtifact(exe);

    // 'zig build run' — run the compiled executable (only works on matching host)
    const run_cmd = b.addRunArtifact(exe);
    run_cmd.step.dependOn(b.getInstallStep());
    if (b.args) |args| {
        run_cmd.addArgs(args);
    }
    const run_step = b.step("run", "Run the executable");
    run_step.dependOn(&run_cmd.step);
}

/// Scan a directory for C or C++ source files and return their names.
fn collectSourceFiles(b: *std.Build, dir_path: []const u8, language: enum { c, cpp }) []const []const u8 {
    var files: std.ArrayList([]const u8) = .{};

    var dir = std.fs.cwd().openDir(dir_path, .{ .iterate = true }) catch |err| {
        std.log.warn("Could not open source directory '{s}': {}", .{ dir_path, err });
        return files.toOwnedSlice(b.allocator) catch &.{};
    };
    defer dir.close();

    var iter = dir.iterate();
    while (iter.next() catch null) |entry| {
        if (entry.kind != .file) continue;
        const ext = std.fs.path.extension(entry.name);
        const match = switch (language) {
            .c => std.mem.eql(u8, ext, ".c"),
            .cpp => std.mem.eql(u8, ext, ".cpp") or
                std.mem.eql(u8, ext, ".cc") or
                std.mem.eql(u8, ext, ".cxx"),
        };
        if (match) {
            files.append(
                b.allocator,
                b.allocator.dupe(u8, entry.name) catch @panic("OOM"),
            ) catch @panic("OOM");
        }
    }

    return files.toOwnedSlice(b.allocator) catch &.{};
}
