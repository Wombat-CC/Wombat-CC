# Wombat CC Library Template

Use this folder as a starting point for reusable libraries.

## Steps

1. Copy `library-template` to a new repo/folder (for example `Wombat-CC-MyLib`).
2. Rename the package in `build.zig.zon` — the `.name` field is optional, but the **dependency key** you register in the consuming project's `build.zig.zon` (under `.dependencies`) **must** start with `wombat_cc_lib_` for auto-linking to work.
3. Keep artifact name `lib` and named lazy path `include`.
4. Add dependency in your project using a `wombat_cc_lib_` prefixed key:

```zig
.wombat_cc_lib_my_lib = .{ .path = "../Wombat-CC-MyLib" },
```

Then run:

```sh
zig build
```
