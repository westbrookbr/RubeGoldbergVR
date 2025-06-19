import subprocess
import os
import argparse
import time
import shutil # Ensure shutil is imported

parser = argparse.ArgumentParser(description="Create and setup a Unity project for VR development.")
parser.add_argument("--unity-editor-path", type=str, default="Unity",
                    help="Path to the Unity Editor executable (e.g., 'C:/Program Files/Unity/Editor/Unity.exe' or 'Unity' if in PATH)")
parser.add_argument("--project-name", type=str, default="RubeGoldbergVR",
                    help="Name of the Unity project to create.")
parser.add_argument("--unity-version", type=str, default="2023.2.14f1",
                    help="Unity LTS version to use (e.g., 2023.2.14f1)")
# Update the default source path for the C# script
# It's expected to be in the parent directory of this script
parser.add_argument("--cs-script-source", type=str, default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "JulesBuildAutomation.cs"),
                    help="Source path of the C# Editor script to be deployed.")

args = parser.parse_args()

project_path = os.path.abspath(args.project_name)
unity_editor_path = args.unity_editor_path
# cs_script_source_path will now be correctly resolved based on the default or user input
cs_script_source_path = os.path.abspath(args.cs_script_source)
cs_script_dest_path = os.path.join(project_path, "Assets", "Editor", "JulesBuildAutomation.cs")

def run_command(command_list, log_file_path=None, cwd=None):
    print(f"Executing command: {{' '.join(command_list)}}")
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
        print(f"Error executing command: {{e}}")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        if log_file_path:
            with open(log_file_path, "w") as f:
                f.write(e.stdout)
                f.write(e.stderr)
        return False
    except FileNotFoundError:
        print(f"Error: Executable not found. Please ensure '{{command_list[0]}}' is in your system's PATH or provide the full path.")
        return False

# Step 1: Create the Unity project
print(f"Step 1: Creating Unity project '{{args.project_name}}'...")
create_project_command = [
    unity_editor_path,
    "-quit",
    "-batchmode",
    "-createProject",
    project_path,
    "-logFile",
    os.path.join(project_path, "unity_create_project.log"), # Log within project for organization
    "-version",
    args.unity_version
]
# Create project directory if it doesn't exist, so logs can be placed there.
os.makedirs(project_path, exist_ok=True)
if not run_command(create_project_command):
    exit(1)
print(f"Unity project '{{args.project_name}}' created successfully.")

# Step 2: Deploy the C# Editor script
print("Step 2: Deploying JulesBuildAutomation.cs...")
# Ensure the target directory Assets/Editor exists
os.makedirs(os.path.dirname(cs_script_dest_path), exist_ok=True)
try:
    if not os.path.exists(cs_script_source_path):
        print(f"Error: Source C# script not found at '{{cs_script_source_path}}'. Looked for JulesBuildAutomation.cs in the root of the repo.")
        exit(1)

    shutil.copy(cs_script_source_path, cs_script_dest_path)
    print(f"JulesBuildAutomation.cs deployed from {{cs_script_source_path}} to {{cs_script_dest_path}}.")
except Exception as e:
    print(f"Error deploying C# script: {{e}}")
    exit(1)

time.sleep(2)

# Step 3: Open the Unity project in batchmode and execute SetupVRProject
print("Step 3: Executing SetupVRProject...")
setup_vr_command = [
    unity_editor_path,
    "-batchmode",
    "-quit", # Ensure Unity quits after execution
    "-projectPath",
    project_path,
    "-executeMethod",
    "JulesBuildAutomation.SetupVRProject",
    "-logFile",
    os.path.join(project_path, "unity_setup_vr_log.txt") # Log within project
]
if not run_command(setup_vr_command):
    print("SetupVRProject failed.")
    exit(1)
print("SetupVRProject completed.")

time.sleep(5) # Adding a slightly longer delay to ensure all Unity processes have finished

# Step 4: Perform Alpha Test Builds
print("Step 4: Performing Alpha Test Builds...")
perform_build_command = [
    unity_editor_path,
    "-batchmode",
    "-quit", # Ensure Unity quits after execution
    "-projectPath",
    project_path,
    "-executeMethod",
    "JulesBuildAutomation.PerformAlphaTestBuild",
    "-logFile",
    os.path.join(project_path, "unity_alpha_build_log.txt") # Log within project
]
if not run_command(perform_build_command):
    print("Alpha Test Build failed.")
    exit(1)
print("Alpha Test Builds completed successfully.")

print("All automation steps completed successfully.")
