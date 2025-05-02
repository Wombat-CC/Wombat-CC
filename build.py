import os
import platform
import subprocess
import sys

def run_command(cmd):
    try:
        subprocess.run(cmd, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {e}", file=sys.stderr)
        return False

def main():
    # Create out/build directory if it doesn't exist
    build_dir = os.path.join(os.getcwd(), "out", "build")
    if not os.path.exists(build_dir):
        print(f"Creating build directory: {build_dir}")
        os.makedirs(build_dir, exist_ok=True)

    # Build the Docker image
    if not run_command(['docker', 'build', '-t', 'project-x-build', '.']):
        print("Failed to build Docker image. Exiting.")
        sys.exit(1)

    # Get current directory in proper format for Docker volume mounting
    current_dir = os.getcwd()
    if platform.system() == 'Windows':
        # Convert Windows path to Docker-compatible format
        # Handle any drive letter (not just C:)
        drive, path = os.path.splitdrive(current_dir)
        if drive:
            drive_letter = drive[0].lower()
            current_dir = f"/{drive_letter}{path.replace('\\', '/')}"
        else:
            current_dir = current_dir.replace('\\', '/')

    print(f"Building project with CMake in Docker container...")
    
    # Run CMake and build in Docker
    build_cmd = [
        'docker', 'run', '--rm',
        '-v', f'{current_dir}:/app',
        'project-x-build',
        'bash', '-c', 
        'mkdir -p /app/out/build && cd /app/out/build && ' + 
        'cmake -DCMAKE_BUILD_TYPE=Release -DCMAKE_C_COMPILER=aarch64-linux-gnu-gcc /app && ' + 
        'cmake --build .'
    ]
    
    if not run_command(build_cmd):
        print("Build failed. See error messages above.")
        sys.exit(1)
        
    print(f"Build completed successfully.")
    print(f"Executable location: {os.path.join(build_dir, 'botball_user_program')}")

if __name__ == '__main__':
    main()