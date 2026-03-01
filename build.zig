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

    // --- User executable ---
    const exe = b.addExecutable(.{
        .name = "botball_user_program",
        .root_module = b.createModule(.{
            .target = target,
            .optimize = optimize,
            .link_libc = true,
            .link_libcpp = true,
        }),
    });

    // Real libwallaby headers from the KIPR Wombat OS image
    exe.addIncludePath(b.path("include"));

    // Pre-built libkipr.so from the KIPR Wombat OS image
    exe.addLibraryPath(b.path("lib"));
    exe.addRPath(.{ .cwd_relative = "/usr/lib" });
    exe.linkSystemLibrary("kipr");

    // Discover and compile user source files from src/
    const c_files = collectSourceFiles(b, "src", .c);
    const cpp_files = collectSourceFiles(b, "src", .cpp);

    if (c_files.len > 0) {
        exe.addCSourceFiles(.{
            .root = b.path("src"),
            .files = c_files,
            .flags = &.{ "-std=c11", "-Wall", "-Wextra" },
        });
    }

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
