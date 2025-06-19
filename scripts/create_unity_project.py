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
parser.add_argument("--cs-script-source", type=str, default=os.path.join(os.path.pardir, "JulesBuildAutomation.cs"),
                    help="Source path of the C# Editor script to be deployed (relative to script location).")

args = parser.parse_args()

project_path = os.path.abspath(args.project_name)
unity_editor_path = args.unity_editor_path # Use as provided, allowing for names in PATH
cs_script_source_path = os.path.abspath(args.cs_script_source)
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
        print(f"Error: Executable '{command_list[0]}' not found. Please ensure it's in your system's PATH or provide the full path.")
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
        os.path.join(project_path, "Logs", "unity_create_project.log"), # Ensure Logs directory is part of the path
        "-version",
        args.unity_version
    ]
    # Create Logs directory for the project if it doesn't exist before creating the project itself.
    # This is because the -logFile argument for -createProject might need it.
    os.makedirs(os.path.join(project_path, "Logs"), exist_ok=True)
    if not run_command(create_project_command, "unity_create_project.log"): # Log file name is relative to Logs dir now
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
        # Attempt to locate it relative to the script's execution directory as a fallback
        alt_cs_script_source_path = os.path.abspath(os.path.join(os.path.dirname(__file__), args.cs_script_source))
        if os.path.exists(alt_cs_script_source_path):
            print(f"Found C# script at alternative path: '{alt_cs_script_source_path}'")
            cs_script_source_path = alt_cs_script_source_path
        else:
            print(f"Still cannot find C# script. Checked default '{cs_script_source_path}' and alternative '{alt_cs_script_source_path}'.")
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
    os.path.join("Logs", "unity_setup_game_log.txt") # Log file path relative to project_path for this command
]
# Ensure Logs directory exists before executing the method that writes to it.
os.makedirs(os.path.join(project_path, "Logs"), exist_ok=True)
if not run_command(setup_game_command, "unity_setup_game_log.txt", cwd=project_path): # Pass project_path as cwd
    print("SetupRubeGoldbergGame failed.")
    exit(1)
print("SetupRubeGoldbergGame completed.")

# Removed the PerformAlphaTestBuild for now, as the primary goal is game setup.
# If builds are needed again, a separate call can be made.

print("All automation steps completed successfully.")
