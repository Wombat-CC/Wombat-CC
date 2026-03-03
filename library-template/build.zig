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
        .files = &.{ "LibraryTemplate.cpp" },
        .flags = &.{ "-std=c++17", "-Wall", "-Wextra" },
    });

    b.addNamedLazyPath("include", b.path("include"));
    b.installArtifact(lib);
}
