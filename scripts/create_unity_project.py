import subprocess
import os
import argparse
import time
import shutil

# This script automates the creation of a new Unity project (if it doesn't already exist)
# and then sets up the project for VR development by executing the JulesBuildAutomation.SetupVRProject method.
# The SetupVRProject method, defined in JulesBuildAutomation.cs, handles:
# 1. Installation of XR packages (OpenXR, XR Interaction Toolkit).
# 2. Configuration of XR settings for Standalone (Windows) and Android.
# 3. Automatic execution of JulesBuildAutomation.SetupRubeGoldbergGame, which includes:
#    - Basic VR scene setup (XR Origin, controllers, ground plane).
#    - Addition of interactable physics objects.
#    - Creation of Rube Goldberg machine prefabs (Ramp, Lever, Domino).

parser = argparse.ArgumentParser(description="Create and setup a Unity project for VR development, including Rube Goldberg game elements.")
parser.add_argument("--unity-editor-path", type=str, default="dummy_unity.sh",
                    help="Path to the Unity Editor executable (e.g., 'C:/Program Files/Unity/Editor/Unity.exe' or 'dummy_unity.sh')")
parser.add_argument("--project-name", type=str, default="RubeGoldbergVR",
                    help="Name of the Unity project to create.")
parser.add_argument("--unity-version", type=str, default="2023.2.14f1",
                    help="Unity LTS version to use (e.g., 2023.2.14f1)")

script_dir = os.path.dirname(os.path.realpath(__file__))
# Assumes JulesBuildAutomation.cs is in the parent directory of this script's directory (i.e., the repository root)
default_cs_script_source = os.path.abspath(os.path.join(script_dir, os.path.pardir, "JulesBuildAutomation.cs"))
parser.add_argument("--cs-script-source", type=str, default=default_cs_script_source,
                    help="Source path of the C# Editor script (JulesBuildAutomation.cs) to be deployed.")

args = parser.parse_args()

project_path = os.path.abspath(args.project_name)
unity_editor_path = args.unity_editor_path
cs_script_source_path = args.cs_script_source
cs_script_dest_path = os.path.join(project_path, "Assets", "Editor", "JulesBuildAutomation.cs")

def run_command(command_list, log_file_name=None, cwd=None):
    print(f"Executing command: {{ ' '.join(command_list) }}")
    log_file_path = None
    if log_file_name:
        log_dir = os.path.join(project_path, "Logs")
        os.makedirs(log_dir, exist_ok=True)
        log_file_path = os.path.join(log_dir, log_file_name)
        print(f"Command output will be logged to: {{log_file_path}}")

    try:
        process = subprocess.run(command_list, check=True, capture_output=True, text=True, cwd=cwd)
        if log_file_path:
            with open(log_file_path, "w") as f:
                f.write("STDOUT:\n")
                f.write(process.stdout)
                f.write("\nSTDERR:\n")
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
                f.write("STDOUT (Error):\n")
                f.write(e.stdout)
                f.write("\nSTDERR (Error):\n")
                f.write(e.stderr)
        return False
    except FileNotFoundError:
        print(f"Error: Executable '{{command_list[0]}}' not found. Ensure it's in your PATH or provide the full path via --unity-editor-path.")
        return False

# Step 1: Create the Unity project (if it doesn't exist)
if not os.path.exists(project_path):
    print(f"Step 1: Creating Unity project '{{args.project_name}}' at '{{project_path}}' using Unity version '{{args.unity_version}}'.")
    # Define the log path for Unity's own creation log
    unity_create_log_path = os.path.join(project_path, "Logs", "unity_editor_create_project.log") # Specific log for Unity process
    os.makedirs(os.path.dirname(unity_create_log_path), exist_ok=True)

    create_project_command = [
        unity_editor_path,
        "-quit",
        "-batchmode",
        "-createProject",
        project_path,
        "-logFile",
        unity_create_log_path, # Use the specific Unity log path here
        "-version",
        args.unity_version
    ]
    # The run_command function will create a separate log for the stdout/stderr of the create_project_command itself.
    if not run_command(create_project_command, "cmd_unity_create_project.log"): # Log for the subprocess call
        print(f"Unity project creation failed. Check logs in '{{os.path.join(project_path, 'Logs')}}'.")
        exit(1)
    print(f"Unity project '{{args.project_name}}' created successfully.")
else:
    print(f"Unity project '{{args.project_name}}' already exists at '{{project_path}}'. Skipping project creation.")

# Step 2: Deploy the C# Editor script (JulesBuildAutomation.cs)
print(f"Step 2: Deploying C# automation script '{{os.path.basename(cs_script_source_path)}}' to '{{cs_script_dest_path}}'...")
os.makedirs(os.path.dirname(cs_script_dest_path), exist_ok=True)
try:
    if not os.path.exists(cs_script_source_path):
        print(f"Error: Source C# script not found at '{{cs_script_source_path}}'.")
        print(f"Please ensure 'JulesBuildAutomation.cs' is in the repository root or specify its path via --cs-script-source.")
        exit(1)

    shutil.copy(cs_script_source_path, cs_script_dest_path)
    print(f"C# automation script deployed successfully.")
except Exception as e:
    print(f"Error deploying C# script: {{e}}")
    exit(1)

print("Waiting a moment for Unity to detect script changes before execution...")
time.sleep(5) # Increased sleep time slightly to give Unity more time to compile.

# Step 3: Execute JulesBuildAutomation.SetupVRProject within Unity.
# This single method call triggers the entire sequence:
# XR Package Installation -> XR Settings Configuration -> Rube Goldberg Game Setup.
print(f"Step 3: Initiating Unity automation sequence by executing 'JulesBuildAutomation.SetupVRProject' in project '{{args.project_name}}'.")
print("This will configure VR, set up the scene, and create Rube Goldberg elements.")

# Define the log path for Unity's own execution log for this step
unity_exec_log_path = os.path.join(project_path, "Logs", "unity_editor_setup_vr_project.log")
os.makedirs(os.path.dirname(unity_exec_log_path), exist_ok=True)

setup_command = [
    unity_editor_path,
    "-batchmode",
    "-quit", # Unity will exit automatically via EditorApplication.Exit(0) in JulesBuildAutomation.cs
    "-projectPath",
    project_path,
    "-executeMethod",
    "JulesBuildAutomation.SetupVRProject",
    "-logFile",
    unity_exec_log_path # Use the specific Unity log path here
]
# The run_command function will create its own log for the stdout/stderr of the setup_command.
if not run_command(setup_command, "cmd_unity_setup_vr_project.log"): # Log for the subprocess call
    print("Execution of 'JulesBuildAutomation.SetupVRProject' failed. Check logs for details.")
    exit(1)
print("'JulesBuildAutomation.SetupVRProject' execution successfully initiated. Check Unity logs for detailed progress.")
print(f"Primary Unity execution log for this step: {{unity_exec_log_path}}")
print(f"Command execution log: {{os.path.join(project_path, 'Logs', 'cmd_unity_setup_vr_project.log')}}")


print(f"Python script '{{os.path.basename(__file__)}}' completed its tasks.")
print(f"The Unity project '{{args.project_name}}' should now be created and fully configured for VR with Rube Goldberg elements.")
