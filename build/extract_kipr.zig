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

    // Extract tar — strip_components=1 removes the leading "./"
    try tar.pipeToFileSystem(out_dir, &decompressor.reader, .{
        .strip_components = 1,
    });

    if (decompressor.err) |err| return err;
}
