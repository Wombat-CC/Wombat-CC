{
  description = "Project XBOT – Cross-compilation build environment for KIPR Wombat";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { inherit system; };
      in
      {
        devShells.default = pkgs.mkShell {
          buildInputs = [
            pkgs.zig   # Zig compiler and build system
            pkgs.zls   # Zig Language Server for editor integration
          ];

          shellHook = ''
            echo "Project XBOT dev shell"
            echo "  zig $(zig version)"
            echo ""
            echo "Commands:"
            echo "  zig build                         — build (debug, aarch64-linux)"
            echo "  zig build -Doptimize=ReleaseFast  — build (release, aarch64-linux)"
            echo "  zig build -Dtarget=native          — build for the host machine"
          '';
        };
      }
    );
}
