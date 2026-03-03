# Wombat-CC Library Template

Use this folder as a starting point for reusable libraries.

## Steps

1. Copy `library-template` to a new repo/folder (for example `Wombat-CC-MyLib`).
2. Rename package in `build.zig.zon`.
3. Keep artifact name `lib` and named lazy path `include`.
4. Add dependency in your project:

```zig
.wombat_cc_lib_my_lib = .{ .path = "../Wombat-CC-MyLib" },
```

Then run:

```sh
zig build
```
