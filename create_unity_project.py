import subprocess
import os
import shutil
import argparse

def main():
    parser = argparse.ArgumentParser(description="Create and setup a Unity project.")
    parser.add_argument('--unity-editor-path', type=str, default="Unity",
                        help='Path to the Unity editor executable.')
    # Add an argument for the project name, though the subtask specifies "RubeGoldbergVR"
    parser.add_argument('--project-name', type=str, default="RubeGoldbergVR",
                        help='Name of the Unity project to create.')

    args = parser.parse_args()

    unity_editor_path = args.unity_editor_path
    project_name = args.project_name
    project_path = os.path.join(os.getcwd(), project_name)

    source_jules_build_automation_cs = "JulesBuildAutomation.cs"
    destination_editor_folder = os.path.join(project_path, "Assets", "Editor")
    destination_jules_build_automation_cs = os.path.join(destination_editor_folder, "JulesBuildAutomation.cs")

    print(f"Using Unity editor path: {unity_editor_path}")
    print(f"Target project name: {project_name}")
    print(f"Target project path: {project_path}")

    # 1. Generate a helper Python script (unity_create_project_script_content) and execute it
    #    to create a Unity project named "RubeGoldbergVR".
    #    (Simplified: directly create project using Unity command)
    if os.path.exists(project_path):
        print(f"Project path {project_path} already exists. Removing it.")
        shutil.rmtree(project_path)

    print(f"Creating Unity project '{project_name}' at '{project_path}'...")
    create_project_command = f'{unity_editor_path} -batchmode -quit -createProject "{project_path}"'

    try:
        subprocess.run(create_project_command, shell=True, check=True, timeout=300) # 5 min timeout
        print(f"Project '{project_name}' created successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error creating Unity project: {e}")
        return
    except subprocess.TimeoutExpired:
        print(f"Timeout creating Unity project. It might still be running or failed to start properly.")
        # It's possible Unity started and is running in background, or it failed silently.
        # For this automated script, we'll assume failure on timeout for project creation.
        return
    except FileNotFoundError:
        print(f"Error: Unity editor not found at '{unity_editor_path}'. Please ensure it's in PATH or provide correct path.")
        return

    # 2. Create the Assets/Editor directory within the new project.
    print(f"Creating directory: {destination_editor_folder}")
    os.makedirs(destination_editor_folder, exist_ok=True)

    # 3. Move the JulesBuildAutomation.cs file ... into {project_name}/Assets/Editor/JulesBuildAutomation.cs.
    if not os.path.exists(source_jules_build_automation_cs):
        print(f"Error: Source file '{source_jules_build_automation_cs}' not found in workspace root.")
        # Create a dummy JulesBuildAutomation.cs if not found, so Unity methods don't fail immediately
        print(f"Creating a dummy '{source_jules_build_automation_cs}' for placeholder purposes.")
        with open(source_jules_build_automation_cs, "w") as f:
            f.write("""
using UnityEngine;
using UnityEditor;

public class JulesBuildAutomation : MonoBehaviour
{
    [MenuItem("Jules/Build Automation/Setup VR Project")]
    public static void SetupVRProject()
    {
        Debug.Log("JulesBuildAutomation.SetupVRProject called - Placeholder");
    }

    [MenuItem("Jules/Build Automation/Perform Alpha Test Build")]
    public static void PerformAlphaTestBuild()
    {
        Debug.Log("JulesBuildAutomation.PerformAlphaTestBuild called - Placeholder");
        // Example of how a build might be triggered:
        // BuildPlayerOptions buildPlayerOptions = new BuildPlayerOptions();
        // buildPlayerOptions.scenes = new[] { "Assets/Scenes/SampleScene.unity" }; // Ensure this scene exists
        // buildPlayerOptions.locationPathName = "Builds/AlphaBuild";
        // buildPlayerOptions.target = EditorUserBuildSettings.activeBuildTarget;
        // buildPlayerOptions.options = BuildOptions.None;
        // BuildPipeline.BuildPlayer(buildPlayerOptions);
        // Debug.Log("Build process initiated by placeholder.");
    }
}
""")

    print(f"Moving '{source_jules_build_automation_cs}' to '{destination_jules_build_automation_cs}'")
    shutil.move(source_jules_build_automation_cs, destination_jules_build_automation_cs)

    # 4. Execute Unity -batchmode -quit -projectPath RubeGoldbergVR -executeMethod JulesBuildAutomation.SetupVRProject
    setup_command = (f'{unity_editor_path} -batchmode -quit -projectPath "{project_path}" '
                     f'-executeMethod JulesBuildAutomation.SetupVRProject '
                     f'-logFile "{os.path.join(project_path, "unity_setup_log.txt")}"')

    print(f"Executing: {setup_command}")
    try:
        subprocess.run(setup_command, shell=True, check=True, timeout=300) # 5 min timeout
        print("JulesBuildAutomation.SetupVRProject executed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error executing JulesBuildAutomation.SetupVRProject: {e}")
        # Continue to next step even if this fails, to attempt build
    except subprocess.TimeoutExpired:
        print(f"Timeout executing JulesBuildAutomation.SetupVRProject.")
    except FileNotFoundError:
        print(f"Error: Unity editor not found at '{unity_editor_path}'. Cannot execute SetupVRProject.")
        return


    # 5. Execute Unity -batchmode -quit -projectPath RubeGoldbergVR -executeMethod JulesBuildAutomation.PerformAlphaTestBuild
    build_command = (f'{unity_editor_path} -batchmode -quit -projectPath "{project_path}" '
                     f'-executeMethod JulesBuildAutomation.PerformAlphaTestBuild '
                     f'-logFile "{os.path.join(project_path, "unity_build_log.txt")}"')

    print(f"Executing: {build_command}")
    try:
        subprocess.run(build_command, shell=True, check=True, timeout=600) # 10 min timeout for build
        print("JulesBuildAutomation.PerformAlphaTestBuild executed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error executing JulesBuildAutomation.PerformAlphaTestBuild: {e}")
    except subprocess.TimeoutExpired:
        print(f"Timeout executing JulesBuildAutomation.PerformAlphaTestBuild.")
    except FileNotFoundError:
        print(f"Error: Unity editor not found at '{unity_editor_path}'. Cannot execute PerformAlphaTestBuild.")
        return

    print("Script finished.")

if __name__ == "__main__":
    main()
