import argparse
import os
import platform
import shutil
import subprocess
import sys


def run_command(cmd):
    try:
        subprocess.run(cmd, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {e}", file=sys.stderr)
        return False


def docker_image_exists(name: str) -> bool:
    try:
        subprocess.run(
            ["docker", "image", "inspect", name],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
        return True
    except subprocess.CalledProcessError:
        return False


def ensure_image(name: str):
    if docker_image_exists(name):
        return True
    print(f"Pulling Docker image '{name}'...")
    return run_command(["docker", "pull", name])


def main():
    parser = argparse.ArgumentParser(
        description="Cross-compile for Wombat using Docker + aarch64-linux-gnu-g++"
    )
    parser.add_argument(
        "--clean", action="store_true", help="Remove out/build before building"
    )
    parser.add_argument(
        "--clean-only",
        action="store_true",
        help="Only clean out/ and exit without building",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Print commands and enable compiler verbosity",
    )
    # Capture any extra compiler/linker flags after a '--'
    args, extra_args = parser.parse_known_args()

    image = "sillyfreak/wombat-cross"

    # Verify Docker is available
    try:
        subprocess.run(["docker", "--version"], check=True, stdout=subprocess.DEVNULL)
    except Exception:
        print("Docker is required but not available on PATH.", file=sys.stderr)
        sys.exit(1)

    # Get current directory in proper format for Docker volume mounting
    current_dir = os.getcwd()
    if platform.system() == "Windows":
        # Convert Windows path to Docker-compatible format, handle drive letters
        drive, path = os.path.splitdrive(current_dir)
        if drive:
            drive_letter = drive[0].lower()
            current_dir = f"/{drive_letter}{path.replace('\\', '/')}"
        else:
            current_dir = current_dir.replace("\\", "/")

    # Optionally clean output directory first
    host_out_dir = os.path.join(os.getcwd(), "out")
    if args.clean or args.clean_only:
        if os.path.isdir(host_out_dir):
            print(f"Cleaning output directory: {host_out_dir}")
            shutil.rmtree(host_out_dir)
        else:
            print("Nothing to clean (out/ does not exist)")
        if args.clean_only:
            print("Clean completed. Exiting (--clean-only).")
            return

    if not ensure_image(image):
        print("Failed to prepare Docker image.", file=sys.stderr)
        sys.exit(1)

    # Verify the cross C++ compiler exists inside the image
    print("Checking cross C++ toolchain in container...")
    if not run_command(
        [
            "docker",
            "run",
            "--rm",
            image,
            "bash",
            "-lc",
            "command -v aarch64-linux-gnu-g++ && aarch64-linux-gnu-g++ --version | head -n 1",
        ]
    ):
        print(
            "aarch64-linux-gnu-g++ not found in the image. Please ensure the image provides the cross C++ compiler.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Discover sources
    src_dir = os.path.join(os.getcwd(), "src")
    if not os.path.isdir(src_dir):
        print("src/ directory not found.", file=sys.stderr)
        sys.exit(1)

    c_files = [f for f in sorted(os.listdir(src_dir)) if f.endswith(".c")]
    cpp_files = [
        f for f in sorted(os.listdir(src_dir)) if f.endswith((".cc", ".cpp", ".cxx"))
    ]

    if not c_files and not cpp_files:
        print(
            "No source files found in src/ (expected .c, .cc, .cpp, .cxx).",
            file=sys.stderr,
        )
        sys.exit(1)

    # Compose compile+link command: use g++ for everything; force C files as C and C++ as C++
    out_dir = "/work/out/build"
    target = f"{out_dir}/botball_user_program"
    include_arg = (
        "-Iinclude" if os.path.isdir(os.path.join(os.getcwd(), "include")) else ""
    )

    # Allow extra args to be passed through to the compiler (e.g., -D flags)
    extra = " ".join(extra_args) if extra_args else ""

    # Build source lists for the container path
    c_list = " ".join(f"src/{name}" for name in c_files)
    cpp_list = " ".join(f"src/{name}" for name in cpp_files)

    gxx_flags = "-Wall -O2 -g"
    if args.verbose:
        gxx_flags = f"-v {gxx_flags}"

    # Build objects per language to avoid cross-language -std warnings, then link
    obj_dir = "/work/out/obj"
    compile_script = f"""
set -e
mkdir -p {obj_dir} {out_dir}

c_objs=""
for f in src/*.c; do
  [ -e "$f" ] || continue
  name="${{f##*/}}"; base="${{name%.*}}"
  aarch64-linux-gnu-g++ {gxx_flags} {include_arg} -x c -std=c11 -c "$f" -o "{obj_dir}/$base.o" {extra}
  c_objs="$c_objs {obj_dir}/$base.o"
done

cpp_objs=""
for f in src/*.cc src/*.cpp src/*.cxx; do
  [ -e "$f" ] || continue
  name="${{f##*/}}"; base="${{name%.*}}"
  aarch64-linux-gnu-g++ {gxx_flags} {include_arg} -x c++ -std=c++17 -c "$f" -o "{obj_dir}/$base.o" {extra}
  cpp_objs="$cpp_objs {obj_dir}/$base.o"
done

aarch64-linux-gnu-g++ $c_objs $cpp_objs -o {target} -lkipr -lpthread -lm -lz {extra}
"""

    compile_cmd = compile_script

    print("Building project inside Docker container using aarch64-linux-gnu-g++...")
    docker_cmd = ["docker", "run", "--rm"]
    # On Apple Silicon (arm64 hosts), force linux/amd64 image to suppress warnings
    host_arch = platform.machine().lower()
    if host_arch in ("arm64", "aarch64", "arm64e"):
        docker_cmd += ["--platform", "linux/amd64"]
    docker_cmd += [
        "-v",
        f"{current_dir}:/work",
        "-w",
        "/work",
        image,
        "bash",
        "-lc",
        compile_cmd,
    ]

    if args.verbose:
        print("Compile script:")
        print(compile_cmd)
        print("Docker command:")
        print(" ".join(docker_cmd))

    if not run_command(docker_cmd):
        print("Build failed. See error messages above.", file=sys.stderr)
        sys.exit(1)

    build_dir = os.path.join(os.getcwd(), "out", "build")
    print("Build completed successfully.")
    print(f"Executable location: {os.path.join(build_dir, 'botball_user_program')}")


if __name__ == "__main__":
    main()
