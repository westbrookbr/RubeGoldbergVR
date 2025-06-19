import subprocess
import os
import argparse
import time
import shutil

parser = argparse.ArgumentParser(description="Create and setup a Unity project for VR development.")
parser.add_argument("--unity-editor-path", type=str, default="dummy_unity.sh",
                    help="Path to the Unity Editor executable (e.g., 'C:/Program Files/Unity/Editor/Unity.exe' or 'dummy_unity.sh')")
parser.add_argument("--project-name", type=str, default="RubeGoldbergVR",
                    help="Name of the Unity project to create.")
parser.add_argument("--unity-version", type=str, default="2023.2.14f1",
                    help="Unity LTS version to use (e.g., 2023.2.14f1)")

script_dir = os.path.dirname(os.path.realpath(__file__))
default_cs_script_source = os.path.abspath(os.path.join(script_dir, os.path.pardir, "JulesBuildAutomation.cs"))
parser.add_argument("--cs-script-source", type=str, default=default_cs_script_source,
                    help="Source path of the C# Editor script to be deployed (relative to script location).")

args = parser.parse_args()

project_path = os.path.abspath(args.project_name)
unity_editor_path = args.unity_editor_path
cs_script_source_path = args.cs_script_source
cs_script_dest_path = os.path.join(project_path, "Assets", "Editor", "JulesBuildAutomation.cs")

def run_command(command_list, log_file_name=None, cwd=None):
    print(f"Executing command: {' '.join(command_list)}")
    log_file_path = None
    if log_file_name:
        log_dir = os.path.join(project_path, "Logs")
        os.makedirs(log_dir, exist_ok=True)
        log_file_path = os.path.join(log_dir, log_file_name)

    try:
        process = subprocess.run(command_list, check=True, capture_output=True, text=True, cwd=cwd)
        if log_file_path:
            with open(log_file_path, "w") as f:
                f.write(process.stdout)
                f.write(process.stderr)
        print("STDOUT:", process.stdout)
        if process.stderr:
            print("STDERR:", process.stderr)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {e}")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        if log_file_path:
            with open(log_file_path, "w") as f:
                f.write(e.stdout)
                f.write(e.stderr)
        return False
    except FileNotFoundError:
        print(f"Error: Executable not found. Please ensure '{command_list[0]}' is in your system's PATH or provide the full path.")
        return False

# Step 1: Create the Unity project (only if it doesn't exist to allow incremental work)
if not os.path.exists(project_path):
    print(f"Step 1: Creating Unity project '{args.project_name}'...")
    create_project_command = [
        unity_editor_path,
        "-quit",
        "-batchmode",
        "-createProject",
        project_path,
        "-logFile",
        os.path.join(project_path, "Logs", "unity_create_project.log"), # This log is for Unity itself
        "-version",
        args.unity_version
    ]
    # The run_command function will also create a log (e.g., unity_create_project.log) in project_path/Logs for stdout/stderr of the command itself.
    if not run_command(create_project_command, "unity_create_project.log"):
        exit(1)
    print(f"Unity project '{args.project_name}' created successfully.")
else:
    print(f"Unity project '{args.project_name}' already exists. Skipping project creation.")


# Step 2: Deploy the C# Editor script
print("Step 2: Deploying JulesBuildAutomation.cs...")
os.makedirs(os.path.dirname(cs_script_dest_path), exist_ok=True)
try:
    if not os.path.exists(cs_script_source_path):
        print(f"Error: Source C# script not found at '{cs_script_source_path}'.")
        exit(1)

    shutil.copy(cs_script_source_path, cs_script_dest_path)
    print(f"JulesBuildAutomation.cs deployed to {cs_script_dest_path}.")
except Exception as e:
    print(f"Error deploying C# script: {e}")
    exit(1)

time.sleep(2) # Give a moment for file system to sync

# Step 3: Open the Unity project in batchmode and execute SetupRubeGoldbergGame
print("Step 3: Executing SetupRubeGoldbergGame...")
setup_game_command = [
    unity_editor_path,
    "-batchmode",
    "-quit",
    "-projectPath",
    project_path,
    "-executeMethod",
    "JulesBuildAutomation.SetupRubeGoldbergGame",
    "-logFile",
    os.path.join(project_path, "Logs", "unity_setup_game_log.txt")
]
if not run_command(setup_game_command, "unity_setup_game_log.txt"):
    print("SetupRubeGoldbergGame failed.")
    exit(1)
print("SetupRubeGoldbergGame completed.")

print("All automation steps completed successfully.")
