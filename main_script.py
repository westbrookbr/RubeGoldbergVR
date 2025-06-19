import os
import shutil # Ensure shutil is imported for the python script content, though not directly used by main_script.py itself

# Define the project name
project_name = "RubeGoldbergVR"

# Content of the updated JulesBuildAutomation.cs script
jules_build_automation_cs_content = f"""
using UnityEditor;
using UnityEngine;
using UnityEditor.Build.Reporting;
using UnityEditor.PackageManager;
using UnityEditor.PackageManager.Requests;
using System.IO;
using System.Collections.Generic;
using UnityEditor.XR.Management;
using UnityEditor.XR.OpenXR;
using System.Linq;
using Unity.XR.OpenXR;
using UnityEditor.SceneManagement;
using Unity.XR.CoreUtils;
using Object = UnityEngine.Object; // Explicitly specify UnityEngine.Object to avoid ambiguity

public class JulesBuildAutomation
{{
    private const string ProjectName = "RubeGoldbergVR";
    // List of XR packages to ensure are installed for VR functionality
    private static List<string> xrPackages = new List<string>
    {{
        "com.unity.xr.interaction.toolkit@2.3.1", // Specify version for consistency
        "com.unity.xr.openxr@1.9.0" // Specify version for consistency
    }};

    private static AddRequest currentAddRequest;
    private static int packageIndex = 0;

    // --- Entry points for Jules (via -executeMethod) ---

    [MenuItem("Jules/SetupVRProject")]
    public static void SetupVRProject()
    {{
        Debug.Log("Jules: Starting VR Project Setup...");
        EnsureEditorFolderExists();
        InstallXRPackages();
    }}

    [MenuItem("Jules/PerformAlphaTestBuild")]
    public static void PerformAlphaTestBuild()
    {{
        Debug.Log("Jules: Starting Alpha Test Build...");

        string sampleScenePath = "Assets/Scenes/SampleScene.unity";
        if (!File.Exists(sampleScenePath))
        {{
            Debug.LogError($"Jules: Scene '{{sampleScenePath}}' not found for build. Please ensure it exists.");
            EditorApplication.Exit(1);
            return;
        }}

        BuildPlayerOptions buildOptions = new BuildPlayerOptions();
        buildOptions.scenes = new[] {{ sampleScenePath }};

        string windowsBuildPath = $"Builds/AlphaTest/Windows/{{ProjectName}}.exe";
        string androidBuildPath = $"Builds/AlphaTest/Android/{{ProjectName}}.apk";

        Directory.CreateDirectory(Path.GetDirectoryName(windowsBuildPath));
        Directory.CreateDirectory(Path.GetDirectoryName(androidBuildPath));

        // --- Build for Windows Standalone ---
        Debug.Log("Jules: Building for Windows Standalone (Alpha Test)...");
        buildOptions.locationPathName = windowsBuildPath;
        buildOptions.target = BuildTarget.StandaloneWindows64;
        buildOptions.options = BuildOptions.None;

        BuildReport reportWindows = BuildPipeline.BuildPlayer(buildOptions);
        BuildSummary summaryWindows = reportWindows.summary;

        if (summaryWindows.result == BuildResult.Succeeded)
        {{
            Debug.Log($"Jules: Windows Alpha Test Build succeeded: {{summaryWindows.totalSize}} bytes at {{windowsBuildPath}}");
        }}
        else if (summaryWindows.result == BuildResult.Failed)
        {{
            Debug.LogError($"Jules: Windows Alpha Test Build failed: {{summaryWindows.totalErrors}} errors");
            EditorApplication.Exit(1);
            return;
        }}

        // --- Build for Android (for Quest/VR) ---
        Debug.Log("Jules: Building for Android (Alpha Test for Quest/VR)...");
        buildOptions.locationPathName = androidBuildPath;
        buildOptions.target = BuildTarget.Android;
        buildOptions.options = BuildOptions.None;

        if (!EditorUserBuildSettings.activeBuildTarget.Equals(BuildTarget.Android))
        {{
            Debug.Log("Jules: Switching active build target to Android for build...");
            EditorUserBuildSettings.SwitchActiveBuildTarget(BuildTargetGroup.Android, BuildTarget.Android);
        }}

        BuildReport reportAndroid = BuildPipeline.BuildPlayer(buildOptions);
        BuildSummary summaryAndroid = reportAndroid.summary;

        if (summaryAndroid.result == BuildResult.Succeeded)
        {{
            Debug.Log($"Jules: Android Alpha Test Build succeeded: {{summaryAndroid.totalSize}} bytes at {{androidBuildPath}}");
        }}
        else if (summaryAndroid.result == BuildResult.Failed)
        {{
            Debug.LogError($"Jules: Android Alpha Test Build failed: {{summaryAndroid.totalErrors}} errors");
            EditorApplication.Exit(1);
            return;
        }}

        Debug.Log("Jules: All Alpha Test Builds completed successfully.");
        EditorApplication.Exit(0);
    }}

    // --- Internal Helper Methods ---

    private static void EnsureEditorFolderExists()
    {{
        if (!AssetDatabase.IsValidFolder("Assets/Editor"))
        {{
            AssetDatabase.CreateFolder("Assets", "Editor");
            Debug.Log("Jules: Created folder: Assets/Editor");
        }}
    }}

    private static void InstallXRPackages()
    {{
        packageIndex = 0;
        EditorApplication.update += ProcessPackageInstallationQueue;
    }}

    private static void ProcessPackageInstallationQueue()
    {{
        if (currentAddRequest != null && !currentAddRequest.IsCompleted)
        {{
            return; // Wait for current request to complete
        }}

        if (packageIndex < xrPackages.Count)
        {{
            string packageId = xrPackages[packageIndex];
            Debug.Log($"Jules: Attempting to install package: {{packageId}}");
            currentAddRequest = Client.Add(packageId);
            packageIndex++;
        }}
        else
        {{
            EditorApplication.update -= ProcessPackageInstallationQueue;
            Debug.Log("Jules: All XR packages installation requests sent. Now configuring XR Plug-in Management and OpenXR. Please wait for assembly compilation.");
            EditorApplication.delayCall += ConfigureXRSettings;
        }}
    }}

    private static void ConfigureXRSettings()
    {{
        Debug.Log("Jules: Starting XR configuration...");

        ConfigureBuildTargetXRSettings(BuildTargetGroup.Standalone, BuildTarget.StandaloneWindows64, "Windows, Mac & Linux");
        ConfigureBuildTargetXRSettings(BuildTargetGroup.Android, BuildTarget.Android, "Android");

        AssetDatabase.SaveAssets();
        AssetDatabase.Refresh();

        Debug.Log("Jules: XR configuration complete. Project ready for VR development.");

        CreateBasicVRSceneElements();
    }}

    private static void ConfigureBuildTargetXRSettings(BuildTargetGroup buildTargetGroup, BuildTarget buildTarget, string tabName)
    {{
        Debug.Log($"Jules: Configuring XR for {{tabName}}...");

        XRGeneralSettingsForEditor generalSettings;
        string settingsKey = XRGeneralSettingsForEditor.k_SettingsKey;

        // Try to get existing settings
        if (!EditorBuildSettings.TryGetConfigObject(settingsKey, out generalSettings))
        {{
            // If not found, create new settings
            generalSettings = ScriptableObject.CreateInstance<XRGeneralSettingsForEditor>();
            EditorBuildSettings.AddConfigObject(settingsKey, generalSettings, true); // Add it to EditorBuildSettings
            Debug.Log($"Jules: Created new XRGeneralSettingsForEditor for {{tabName}}.");
        }}

        // Ensure the XRGeneralSettingsForEditor instance for this build target group is correctly set
        XRGeneralSettingsForEditor.SetBuildTargetSettings(buildTargetGroup, generalSettings);

        // Temporarily switch build target for accurate settings application
        EditorUserBuildSettings.activeBuildTargetGroup = buildTargetGroup;
        EditorUserBuildSettings.SwitchActiveBuildTarget(buildTargetGroup, buildTarget);

        // Get the XRManagerSettings for the current generalSettings
        if (generalSettings.Manager == null)
        {{
            generalSettings.Manager = ScriptableObject.CreateInstance<XRManagerSettings>();
            EditorUtility.SetDirty(generalSettings);
            Debug.Log($"Jules: Created new XRManagerSettings for {{tabName}}.");
        }}

        // Add OpenXR Loader if not already present in the list of configured loaders
        var currentLoaders = generalSettings.Manager.loaders;
        bool openXRLoaderFound = false;
        OpenXRLoader openXRLoader = null;

        foreach (var loader in currentLoaders)
        {{
            if (loader is OpenXRLoader oxrLoader)
            {{
                openXRLoaderFound = true;
                openXRLoader = oxrLoader;
                break;
            }}
        }}

        if (!openXRLoaderFound)
        {{
            openXRLoader = ScriptableObject.CreateInstance<OpenXRLoader>();
            currentLoaders.Add(openXRLoader);
            if (!generalSettings.Manager.activeLoaders.Contains(openXRLoader))
            {{
                generalSettings.Manager.activeLoaders.Add(openXRLoader);
            }}
            EditorUtility.SetDirty(generalSettings.Manager);
            Debug.Log($"Jules: Added OpenXR Loader to {{tabName}} XR General Settings.");
        }}

        // Configure OpenXR settings (e.g., add interaction profiles)
        OpenXRSettings openXRSettings = OpenXRSettings.GetForBuildTargetGroup(buildTargetGroup);
        if (openXRSettings != null)
        {{
            Debug.Log($"Jules: Configuring {{tabName}} OpenXR settings...");

            AddOpenXRInteractionProfile(openXRSettings, "com.unity.openxr.features.oculustouchcontroller");
            AddOpenXRInteractionProfile(openXRSettings, "com.unity.openxr.features.metarequestsupport");
            AddOpenXRInteractionProfile(openXRSettings, "com.unity.openxr.features.hp_reverb_g2_controller");

            EditorUtility.SetDirty(openXRSettings);
        }}
        else
        {{
            Debug.LogWarning($"Jules: OpenXRSettings not found for {{tabName}}. This might indicate a problem with package installation or XR management setup.");
        }}

        EditorUtility.SetDirty(generalSettings);
    }}

    private static void AddOpenXRInteractionProfile(OpenXRSettings settings, string featureId)
    {{
        foreach (var feature in OpenXRSettings.GetAllFeatures(settings.buildTargetGroup))
        {{
            if (feature.featureId == featureId)
            {{
                if (!feature.enabled)
                {{
                    feature.enabled = true;
                    Debug.Log($"Jules: Enabled OpenXR feature: {{feature.name}} (ID: {{feature.featureId}}) for {{settings.buildTargetGroup}}.");
                }} else {{
                    Debug.Log($"Jules: OpenXR feature: {{feature.name}} (ID: {{feature.featureId}}) already enabled for {{settings.buildTargetGroup}}.");
                }}
                return;
            }}
        }}
        Debug.LogWarning($"Jules: OpenXR feature with ID '{{featureId}}' not found for {{settings.buildTargetGroup}}. Ensure the relevant package/feature set is installed.");
    }}

    private static void CreateBasicVRSceneElements()
    {{
        Debug.Log("Jules: Creating basic VR scene elements...");

        string sampleScenePath = "Assets/Scenes/SampleScene.unity";
        if (!Directory.Exists("Assets/Scenes"))
        {{
            AssetDatabase.CreateFolder("Assets", "Scenes");
        }}

        Scene activeScene;
        if (!File.Exists(sampleScenePath))
        {{
            activeScene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            EditorSceneManager.SaveScene(activeScene, sampleScenePath);
            Debug.Log($"Jules: Created new scene at: {{sampleScenePath}}");
        }}
        else
        {{
            activeScene = EditorSceneManager.OpenScene(sampleScenePath);
            Debug.Log($"Jules: Opened existing scene at: {{sampleScenePath}}");
        }}

        GameObject mainCamera = GameObject.FindWithTag("MainCamera");
        if (mainCamera != null && mainCamera.GetComponent<Camera>() != null && mainCamera.GetComponent<Camera>().CompareTag("MainCamera"))
        {{
            Debug.Log("Jules: Found and removing default Main Camera.");
            Object.DestroyImmediate(mainCamera);
        }}

        GameObject xrOriginGO = new GameObject("XR Origin");
        var xrOrigin = xrOriginGO.AddComponent<XROrigin>();

        GameObject vrCameraGO = new GameObject("Main Camera");
        vrCameraGO.transform.SetParent(xrOrigin.transform);
        Camera vrCamera = vrCameraGO.AddComponent<Camera>();
        vrCamera.tag = "MainCamera";
        xrOrigin.Camera = vrCamera;

        xrOrigin.rigCamera = vrCamera.transform;
        xrOrigin.rigPlayspace = xrOriginGO.transform;

        if (Object.FindObjectOfType<UnityEngine.XR.Interaction.Toolkit.XRInteractionManager>() == null)
        {{
            GameObject interactionManager = new GameObject("XR Interaction Manager");
            interactionManager.AddComponent<UnityEngine.XR.Interaction.Toolkit.XRInteractionManager>();
            Debug.Log("Jules: Added XR Interaction Manager.");
        }}

        AddXRController(xrOrigin.transform, "Left Hand Controller", true);
        AddXRController(xrOrigin.transform, "Right Hand Controller", false);

        GameObject floor = GameObject.CreatePrimitive(PrimitiveType.Plane);
        floor.name = "Ground Plane";
        floor.transform.position = new Vector3(0, -0.5f, 0);
        floor.transform.localScale = new Vector3(10, 1, 10);

        Renderer floorRenderer = floor.GetComponent<Renderer>();
        if (floorRenderer != null)
        {{
            floorRenderer.sharedMaterial = new Material(Shader.Find("Standard"));
            floorRenderer.sharedMaterial.color = Color.gray;
        }}

        EditorSceneManager.SaveScene(activeScene);
        AssetDatabase.SaveAssets();
        AssetDatabase.Refresh();
        Debug.Log("Jules: Basic VR scene elements created and scene saved.");
    }}

    private static void AddXRController(Transform parent, string name, bool isLeftHand)
    {{
        GameObject controllerGO = new GameObject(name);
        controllerGO.transform.SetParent(parent);

        var controller = controllerGO.AddComponent<UnityEngine.XR.Interaction.Toolkit.XRController>();
        controller.controllerNode = isLeftHand ? UnityEngine.XR.XRNode.LeftHand : UnityEngine.XR.XRNode.RightHand;

        if (isLeftHand)
        {{
            controllerGO.AddComponent<UnityEngine.XR.Interaction.Toolkit.XRRayInteractor>();
            Debug.Log($"Jules: Added {{name}} with XRRayInteractor.");
        }}
        else
        {{
            controllerGO.AddComponent<UnityEngine.XR.Interaction.Toolkit.XRDirectInteractor>();
            Debug.Log($"Jules: Added {{name}} with XRDirectInteractor.");
        }}

        GameObject visualizer = GameObject.CreatePrimitive(PrimitiveType.Sphere);
        visualizer.name = "Controller Visual";
        visualizer.transform.SetParent(controllerGO.transform);
        visualizer.transform.localScale = new Vector3(0.1f, 0.1f, 0.1f);
        visualizer.transform.localPosition = Vector3.zero;
        Object.DestroyImmediate(visualizer.GetComponent<Collider>());
        Renderer visualizerRenderer = visualizer.GetComponent<Renderer>();
        if (visualizerRenderer != null)
        {{
            visualizerRenderer.sharedMaterial = new Material(Shader.Find("Standard"));
            visualizerRenderer.sharedMaterial.color = isLeftHand ? Color.blue : Color.red;
        }}
    }}
}}
"""

# Write the updated Editor script to a temporary file in the workspace root.
with open("JulesBuildAutomation.cs", "w") as f:
    f.write(jules_build_automation_cs_content)

# Define the Python script for Unity project creation and execution
create_unity_project_py_content = f"""
import subprocess
import os
import argparse
import time
import shutil

parser = argparse.ArgumentParser(description="Create and setup a Unity project for VR development.")
parser.add_argument("--unity-editor-path", type=str, default="Unity",
                    help="Path to the Unity Editor executable (e.g., 'C:/Program Files/Unity/Editor/Unity.exe' or 'Unity' if in PATH)")
parser.add_argument("--project-name", type=str, default="RubeGoldbergVR",
                    help="Name of the Unity project to create.")
parser.add_argument("--unity-version", type=str, default="2023.2.14f1",
                    help="Unity LTS version to use (e.g., 2023.2.14f1)")
parser.add_argument("--cs-script-source", type=str, default=os.path.join(os.path.pardir, "JulesBuildAutomation.cs"),
                    help="Source path of the C# Editor script to be deployed (relative to script location).")

args = parser.parse_args()

project_path = os.path.abspath(args.project_name)
unity_editor_path = args.unity_editor_path
cs_script_source_path = os.path.abspath(args.cs_script_source) # Get absolute path
cs_script_dest_path = os.path.join(project_path, "Assets", "Editor", "JulesBuildAutomation.cs")

def run_command(command_list, log_file_name=None, cwd=None):
    print(f"Executing command: {{' '.join(command_list)}}")
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
    os.path.join(project_path, "Logs", "unity_create_project.log"),
    "-version",
    args.unity_version
]
if not run_command(create_project_command, "unity_create_project.log"):
    exit(1)
print(f"Unity project '{{args.project_name}}' created successfully.")

# Step 2: Deploy the C# Editor script
print("Step 2: Deploying JulesBuildAutomation.cs...")
os.makedirs(os.path.dirname(cs_script_dest_path), exist_ok=True)
try:
    if not os.path.exists(cs_script_source_path):
        print(f"Error: Source C# script not found at '{{cs_script_source_path}}'.")
        exit(1)

    shutil.copy(cs_script_source_path, cs_script_dest_path)
    print(f"JulesBuildAutomation.cs deployed to {{cs_script_dest_path}}.")
except Exception as e:
    print(f"Error deploying C# script: {{e}}")
    exit(1)

time.sleep(2) # Give a moment for file system to sync

# Step 3: Open the Unity project in batchmode and execute SetupVRProject
print("Step 3: Executing SetupVRProject...")
setup_vr_command = [
    unity_editor_path,
    "-batchmode",
    "-quit",
    "-projectPath",
    project_path,
    "-executeMethod",
    "JulesBuildAutomation.SetupVRProject",
    "-logFile",
    os.path.join(project_path, "Logs", "unity_setup_vr_log.txt")
]
if not run_command(setup_vr_command, "unity_setup_vr_log.txt"):
    print("SetupVRProject failed.")
    exit(1)
print("SetupVRProject completed.")

time.sleep(5) # Give Unity time to process changes and recompile assemblies

# Step 4: Perform Alpha Test Builds
print("Step 4: Performing Alpha Test Builds...")
perform_build_command = [
    unity_editor_path,
    "-batchmode",
    "-quit",
    "-projectPath",
    project_path,
    "-executeMethod",
    "JulesBuildAutomation.PerformAlphaTestBuild",
    "-logFile",
    os.path.join(project_path, "Logs", "unity_alpha_build_log.txt")
]
if not run_command(perform_build_command, "unity_alpha_build_log.txt"):
    print("Alpha Test Build failed.")
    exit(1)
print("Alpha Test Builds completed successfully.")

print("All automation steps completed successfully.")
"""

# MODIFIED PART: Write the Python script to the scripts directory
if not os.path.exists("scripts"):
    os.makedirs("scripts")
with open("scripts/create_unity_project.py", "w") as f:
    f.write(create_unity_project_py_content)

# MODIFIED PART: Define the single Jules command to execute the script from the scripts directory
jules_command = f"python scripts/create_unity_project.py --project-name {project_name} --unity-editor-path Unity"

print(jules_command)
