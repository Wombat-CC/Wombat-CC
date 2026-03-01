//! Cross-platform KIPR SDK extractor.
//!
//! Extracts headers and the pre-built `libkipr.so` from the KIPR `.deb`
//! package shipped inside the wombat-os repository.  Parses the Debian `ar`
//! archive and gzip-compressed tar in pure Zig — no external tools required,
//! so `zig build` works identically on Linux, macOS, and Windows.
//!
//! Usage (called automatically by the build system):
//!     extract_kipr <kipr.deb> <output_dir>

const std = @import("std");
const flate = std.compress.flate;
const tar = std.tar;

// ── ar archive format ────────────────────────────────────────────────
// Global header:  "!<arch>\n"  (8 bytes)
// Per-member:     60-byte header, then `size` bytes of content,
//                 padded to 2-byte alignment.

const ar_magic = "!<arch>\n";
const ar_header_len = 60;

const ArEntry = struct {
    size: u64,
};

const Stamp = struct {
    size: u64,
    mtime: i128,
};

fn fileExists(dir: *std.fs.Dir, path: []const u8) bool {
    return dir.access(path, .{}) catch false;
}

fn loadStamp(dir: *std.fs.Dir) !?Stamp {
    const file = dir.openFile(".kipr-stamp", .{}) catch |err| switch (err) {
        error.FileNotFound => return null,
        else => return err,
    };
    defer file.close();

    var buf: [128]u8 = undefined;
    const n = try file.readAll(&buf);
    const trimmed = std.mem.trim(u8, buf[0..n], " \t\r\n");

    var it = std.mem.splitScalar(u8, trimmed, ' ');
    const size_str = it.next() orelse return null;
    const mtime_str = it.next() orelse return null;

    const size = std.fmt.parseInt(u64, size_str, 10) catch return null;
    const mtime = std.fmt.parseInt(i128, mtime_str, 10) catch return null;

    return Stamp{ .size = size, .mtime = mtime };
}

fn writeStamp(dir: *std.fs.Dir, stamp: Stamp) !void {
    var file = try dir.createFile(".kipr-stamp", .{ .truncate = true });
    defer file.close();
    try file.writer().print("{d} {d}\n", .{ stamp.size, stamp.mtime });
}

fn reuseIfCurrent(out_path: []const u8, expected: Stamp) !bool {
    var dir = std.fs.cwd().openDir(out_path, .{}) catch return false;
    defer dir.close();

    const stamp = try loadStamp(&dir) orelse return false;
    if (stamp.size != expected.size or stamp.mtime != expected.mtime) return false;

    if (!fileExists(&dir, "usr/include/kipr/wombat.h")) return false;
    if (!fileExists(&dir, "usr/lib/libkipr.so")) return false;

    std.log.info("Reusing cached KIPR SDK at {s}", .{out_path});
    return true;
}

/// Walk the ar archive and return the first member whose name starts with
/// "data.tar" (the payload inside a .deb package).
fn findDataTar(reader: *std.Io.Reader) !ArEntry {
    // Validate global header
    var magic_buf: [ar_magic.len]u8 = undefined;
    try reader.readSliceAll(&magic_buf);
    if (!std.mem.eql(u8, &magic_buf, ar_magic))
        return error.BadArMagic;

    // Walk entries
    while (true) {
        var hdr_buf: [ar_header_len]u8 = undefined;
        const n = try reader.readSliceShort(&hdr_buf);
        if (n < ar_header_len) return error.EndOfArchive;

        const raw_name = std.mem.trimRight(u8, hdr_buf[0..16], &[_]u8{ ' ', '/' });
        const raw_size = std.mem.trimRight(u8, hdr_buf[48..58], &[_]u8{' '});
        const size = try std.fmt.parseInt(u64, raw_size, 10);

        if (std.mem.startsWith(u8, raw_name, "data.tar")) {
            return .{ .size = size };
        }

        // Skip to next entry (content + optional padding byte)
        const skip = size + (size % 2);
        _ = try reader.discard(.limited64(skip));
    }
}

pub fn main() !void {
    // Use argsWithAllocator for cross-platform support (required on Windows).
    var args = try std.process.argsWithAllocator(std.heap.page_allocator);
    defer args.deinit();
    _ = args.next(); // argv[0]
    const deb_path = args.next() orelse return error.MissingDebArg;
    const out_path = args.next() orelse return error.MissingOutArg;

    const deb_stat = try std.fs.cwd().statFile(deb_path);
    const expected_stamp = Stamp{
        .size = deb_stat.size,
        .mtime = deb_stat.mtime,
    };

    if (try reuseIfCurrent(out_path, expected_stamp)) return;

    std.fs.cwd().deleteTree(out_path) catch |err| switch (err) {
        error.FileNotFound => {},
        else => return err,
    };

    // Open the .deb file
    const deb_file = try std.fs.cwd().openFile(deb_path, .{});
    defer deb_file.close();

    var file_buf: [8192]u8 = undefined;
    var file_reader = deb_file.reader(&file_buf);

    // Locate data.tar.gz inside the ar archive
    const entry = try findDataTar(&file_reader.interface);

    // Limit reading to just this member
    var limit_buf: [4096]u8 = undefined;
    var limited = file_reader.interface.limited(.limited64(entry.size), &limit_buf);

    // Decompress gzip
    var decompress_buf: [flate.max_window_len]u8 = undefined;
    var decompressor = flate.Decompress.init(&limited.interface, .gzip, &decompress_buf);

    // Create output directory
    var out_dir = try std.fs.cwd().makeOpenPath(out_path, .{});
    defer out_dir.close();

    std.log.info("Extracting KIPR SDK to {s}", .{out_path});

    // Extract tar — strip_components=1 removes the leading "./"
    try tar.pipeToFileSystem(out_dir, &decompressor.reader, .{
        .strip_components = 1,
    });

    if (decompressor.err) |err| return err;
    try writeStamp(&out_dir, expected_stamp);
}
