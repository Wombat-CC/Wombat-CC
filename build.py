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


def parse_simple_yaml(content):
    """Parse a simple subset of YAML (no external dependencies needed)."""
    config = {}
    current_section = None
    current_dict = config

    for line in content.split("\n"):
        line = line.rstrip()
        if not line or line.strip().startswith("#"):
            continue

        # Count leading spaces
        indent = len(line) - len(line.lstrip())
        line = line.strip()

        if ":" in line:
            key, _, value = line.partition(":")
            key = key.strip()
            value = value.strip()

            if indent == 0:
                # Top-level key
                if value == "":
                    # Start of a section
                    current_section = key
                    config[current_section] = {}
                    current_dict = config[current_section]
                else:
                    # Top-level key-value
                    config[key] = parse_value(value)
                    current_dict = config
            elif indent > 0 and current_section:
                # Nested key in current section
                current_dict[key] = parse_value(value)
        elif line.startswith("- "):
            # List item
            value = line[2:].strip()
            if current_section and isinstance(current_dict, dict):
                # Convert last key to list if needed
                last_key = list(current_dict.keys())[-1] if current_dict else None
                if last_key and not isinstance(current_dict[last_key], list):
                    current_dict[last_key] = []
                if last_key:
                    current_dict[last_key].append(parse_value(value))

    return config


def parse_value(value):
    """Parse a YAML value to appropriate Python type."""
    value = value.strip()
    if value.startswith('"') and value.endswith('"'):
        return value[1:-1]
    elif value.startswith("'") and value.endswith("'"):
        return value[1:-1]
    elif value.lower() == "true":
        return True
    elif value.lower() == "false":
        return False
    elif value == "[]":
        return []
    elif value.isdigit():
        return int(value)
    else:
        return value


def load_config(config_path="configs/config.dev.yaml"):
    """Load configuration from YAML file with defaults."""
    default_config = {
        "docker_image": "sillyfreak/wombat-cross",
        "compiler": {
            "cross_compiler": "aarch64-linux-gnu-g++",
            "flags": "-Wall",
            "optimization": "-O2",
            "debug": True,
            "c_standard": "c11",
            "cpp_standard": "c++17",
        },
        "linker": {
            "libraries": "kipr pthread m z",
            "flags": "",
        },
        "directories": {
            "source": "src",
            "include": "include",
            "output": "out",
            "objects": "obj",
            "build": "build",
        },
        "output_name": "botball_user_program",
        "extra_args": [],
    }

    if os.path.exists(config_path):
        try:
            with open(config_path, "r") as f:
                user_config = parse_simple_yaml(f.read()) or {}
            # Merge user config with defaults (user config takes precedence)
            config = default_config.copy()
            for key, value in user_config.items():
                if (
                    isinstance(value, dict)
                    and key in config
                    and isinstance(config[key], dict)
                ):
                    config[key].update(value)
                else:
                    config[key] = value
            return config
        except Exception as e:
            print(
                f"Warning: Could not load config from {config_path}: {e}",
                file=sys.stderr,
            )
            print("Using default configuration.", file=sys.stderr)
            return default_config
    else:
        print(
            f"Note: {config_path} not found, using default configuration.",
            file=sys.stderr,
        )
        return default_config


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
    # Load configuration
    config = load_config()

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
    parser.add_argument(
        "--ci",
        action="store_true",
        help="CI mode: run container as root (for write perms on mounted workspace)",
    )
    parser.add_argument(
        "--config",
        default="configs/config.dev.yaml",
        help="Path to configuration file (default: configs/config.dev.yaml)",
    )
    # Capture any extra compiler/linker flags after a '--'
    args, extra_args = parser.parse_known_args()

    # Reload config if custom path specified
    if args.config != "configs/config.dev.yaml":
        config = load_config(args.config)

    image = config["docker_image"]

    # Verify Docker is available
    try:
        subprocess.run(["docker", "--version"], check=True, stdout=subprocess.DEVNULL)
    except Exception:
        print("Docker is required but not available on PATH.", file=sys.stderr)
        sys.exit(1)

    host_arch = platform.machine().lower()

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
    host_out_dir = os.path.join(os.getcwd(), config["directories"]["output"])
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

    # Verify the cross C++ compiler exists inside the image (only if --verbose)
    if args.verbose:
        print("Checking cross C++ toolchain in container...")
        cross_compiler = config["compiler"]["cross_compiler"]
        preflight_cmd = ["docker", "run", "--rm"]
        if args.ci:
            preflight_cmd += ["--user", "root"]
        if host_arch in ("arm64", "aarch64", "arm64e"):
            preflight_cmd += ["--platform", "linux/amd64"]
        preflight_cmd += [
            image,
            "bash",
            "-lc",
            f"command -v {cross_compiler} && {cross_compiler} --version | head -n 1",
        ]
        if not run_command(preflight_cmd):
            print(
                f"{cross_compiler} not found in the image. Please ensure the image provides the cross C++ compiler.",
                file=sys.stderr,
            )
            sys.exit(1)

    # Discover sources
    src_dir = os.path.join(os.getcwd(), config["directories"]["source"])
    if not os.path.isdir(src_dir):
        print(
            f"{config['directories']['source']}/ directory not found.", file=sys.stderr
        )
        sys.exit(1)

    c_files = [f for f in sorted(os.listdir(src_dir)) if f.endswith(".c")]
    cpp_files = [
        f for f in sorted(os.listdir(src_dir)) if f.endswith((".cc", ".cpp", ".cxx"))
    ]

    if not c_files and not cpp_files:
        print(
            f"No source files found in {config['directories']['source']}/ (expected .c, .cc, .cpp, .cxx).",
            file=sys.stderr,
        )
        sys.exit(1)

    # Compose compile+link command: use g++ for everything; force C files as C and C++ as C++
    out_dir = (
        f"/work/{config['directories']['output']}/{config['directories']['build']}"
    )
    target = f"{out_dir}/{config['output_name']}"

    include_dir = config["directories"]["include"]
    include_path = os.path.join(os.getcwd(), include_dir)
    include_arg = f"-I{include_dir}" if os.path.isdir(include_path) else ""

    # Merge config extra_args with command line extra_args
    config_extra = config.get("extra_args", [])
    if isinstance(config_extra, list):
        config_extra = " ".join(config_extra)
    all_extra_args = f"{config_extra} {' '.join(extra_args)}".strip()

    # Build source lists for the container path
    source_dir = config["directories"]["source"]
    c_list = " ".join(f"{source_dir}/{name}" for name in c_files)
    cpp_list = " ".join(f"{source_dir}/{name}" for name in cpp_files)

    # Build compiler flags from config
    compiler_flags = config["compiler"]["flags"]
    optimization = config["compiler"]["optimization"]
    debug_flag = "-g" if config["compiler"]["debug"] else ""
    gxx_flags = f"{compiler_flags} {optimization} {debug_flag}".strip()

    if args.verbose:
        gxx_flags = f"-v {gxx_flags}"

    cross_compiler = config["compiler"]["cross_compiler"]
    c_standard = config["compiler"]["c_standard"]
    cpp_standard = config["compiler"]["cpp_standard"]

    # Build linker flags
    libraries = config["linker"]["libraries"]
    lib_flags = " ".join(f"-l{lib}" for lib in libraries.split())
    linker_flags = config["linker"]["flags"]

    # Build objects per language to avoid cross-language -std warnings, then link
    obj_dir = (
        f"/work/{config['directories']['output']}/{config['directories']['objects']}"
    )
    compile_script = f"""
set -e
mkdir -p {obj_dir} {out_dir}

c_objs=""
for f in {source_dir}/*.c; do
  [ -e "$f" ] || continue
  name="${{f##*/}}"; base="${{name%.*}}"
  {cross_compiler} {gxx_flags} {include_arg} -x c -std={c_standard} -c "$f" -o "{obj_dir}/$base.o" {all_extra_args}
  c_objs="$c_objs {obj_dir}/$base.o"
done

cpp_objs=""
for f in {source_dir}/*.cc {source_dir}/*.cpp {source_dir}/*.cxx; do
  [ -e "$f" ] || continue
  name="${{f##*/}}"; base="${{name%.*}}"
  {cross_compiler} {gxx_flags} {include_arg} -x c++ -std={cpp_standard} -c "$f" -o "{obj_dir}/$base.o" {all_extra_args}
  cpp_objs="$cpp_objs {obj_dir}/$base.o"
done

{cross_compiler} $c_objs $cpp_objs -o {target} {lib_flags} {linker_flags} {all_extra_args}
"""

    compile_cmd = compile_script

    print("Building project inside Docker container...")
    docker_cmd = ["docker", "run", "--rm"]
    if args.ci:
        docker_cmd += ["--user", "root"]
    # On Apple Silicon (arm64 hosts), force linux/amd64 image to suppress warnings
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

    build_dir = os.path.join(
        os.getcwd(), config["directories"]["output"], config["directories"]["build"]
    )
    print("Build completed successfully.")
    print(f"Executable location: {os.path.join(build_dir, config['output_name'])}")


if __name__ == "__main__":
    main()
