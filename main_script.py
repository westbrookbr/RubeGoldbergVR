import os
import shutil
import argparse # Added in Subtask 3

def main():
    # Argument parser for main_script.py (Subtask 3)
    parser = argparse.ArgumentParser(description="Generates Unity automation scripts and provides a command to run them.")
    parser.add_argument("--project-name", default="RubeGoldbergVR",
                        help="Name of the Unity project. This will also be the value for ProjectName const in C#.")
    parser.add_argument("--alpha-build", action="store_true",
                        help="If set, the command for create_unity_project.py will include --run-alpha-build.")
    args = parser.parse_args()

    # JULES_TEST_MODE_NO_WRITE (Subtask 5)
    test_mode_no_write = os.environ.get("JULES_TEST_MODE_NO_WRITE", "false").lower() == "true"

    # --- jules_build_automation_cs_content ---
    # ProjectName is now dynamic via args.project_name (Subtask 3)
    # SwitchActiveBuildTarget check added in PerformAlphaTestBuild (Subtask 1)
    jules_build_automation_cs_content = f"""
// JulesBuildAutomation.cs content starts here
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
using Object = UnityEngine.Object;
using UnityEngine.XR.Interaction.Toolkit;
using UnityEngine.SceneManagement;

public class JulesBuildAutomation
{{{{
    private const string ProjectName = \\"{args.project_name}\\"; // From Subtask 3
    private static List<string> xrPackages = new List<string>
    {{{{
        "com.unity.xr.interaction.toolkit@2.3.1",
        "com.unity.xr.openxr@1.9.0"
    }}}};

    private static AddRequest currentAddRequest;
    private static int packageIndex = 0;

    [MenuItem("Jules/SetupVRProject")]
    public static void SetupVRProject()
    {{{{
        Debug.Log("JulesBuildAutomation: Initiating VR Project Setup Sequence (XR Packages, XR Settings)...");
        EnsureEditorFolderExists();
        InstallXRPackages();
    }}}}

    [MenuItem("Jules/PerformAlphaTestBuild")]
    public static void PerformAlphaTestBuild()
    {{{{
        Debug.Log("JulesBuildAutomation: Starting Alpha Test Build...");
        string sampleScenePath = "Assets/Scenes/SampleScene.unity";
        if (!File.Exists(sampleScenePath))
        {{{{
            Debug.LogError($"JulesBuildAutomation: Scene '{{{{sampleScenePath}}}}' not found for build. Please ensure it exists.");
            EditorApplication.Exit(1);
            return;
        }}}}
        BuildPlayerOptions buildOptions = new BuildPlayerOptions();
        buildOptions.scenes = new[] {{{{ sampleScenePath }}}};
        string windowsBuildPath = $"Builds/AlphaTest/Windows/{{{{ProjectName}}}}.exe";
        string androidBuildPath = $"Builds/AlphaTest/Android/{{{{ProjectName}}}}.apk";
        Directory.CreateDirectory(Path.GetDirectoryName(windowsBuildPath));
        Directory.CreateDirectory(Path.GetDirectoryName(androidBuildPath));

        Debug.Log("JulesBuildAutomation: Building for Windows Standalone (Alpha Test)...");
        buildOptions.locationPathName = windowsBuildPath;
        buildOptions.target = BuildTarget.StandaloneWindows64;
        buildOptions.options = BuildOptions.None;
        BuildReport reportWindows = BuildPipeline.BuildPlayer(buildOptions);
        BuildSummary summaryWindows = reportWindows.summary;
        if (summaryWindows.result == BuildResult.Succeeded)
        {{{{
            Debug.Log($"JulesBuildAutomation: Windows Alpha Test Build succeeded: {{{{summaryWindows.totalSize}}}} bytes at {{{{windowsBuildPath}}}}");
        }}}}
        else if (summaryWindows.result == BuildResult.Failed)
        {{{{
            Debug.LogError($"JulesBuildAutomation: Windows Alpha Test Build failed: {{{{summaryWindows.totalErrors}}}} errors");
            EditorApplication.Exit(1);
            return;
        }}}}

        Debug.Log("JulesBuildAutomation: Building for Android (Alpha Test for Quest/VR)...");
        buildOptions.locationPathName = androidBuildPath;
        buildOptions.target = BuildTarget.Android;
        buildOptions.options = BuildOptions.None;
        // Modification from Subtask 1 - Check SwitchActiveBuildTarget success
        if (!EditorUserBuildSettings.activeBuildTarget.Equals(BuildTarget.Android))
        {{{{
            Debug.Log("JulesBuildAutomation: Switching active build target to Android for build...");
            if (!EditorUserBuildSettings.SwitchActiveBuildTarget(BuildTargetGroup.Android, BuildTarget.Android))
            {{{{
                 Debug.LogError("JulesBuildAutomation: Failed to switch active build target to Android. Exiting.");
                 EditorApplication.Exit(1);
                 return;
            }}}}
        }}}}
        BuildReport reportAndroid = BuildPipeline.BuildPlayer(buildOptions);
        BuildSummary summaryAndroid = reportAndroid.summary;
        if (summaryAndroid.result == BuildResult.Succeeded)
        {{{{
            Debug.Log($"JulesBuildAutomation: Android Alpha Test Build succeeded: {{{{summaryAndroid.totalSize}}}} bytes at {{{{androidBuildPath}}}}");
        }}}}
        else if (summaryAndroid.result == BuildResult.Failed)
        {{{{
            Debug.LogError($"JulesBuildAutomation: Android Alpha Test Build failed: {{{{summaryAndroid.totalErrors}}}} errors");
            EditorApplication.Exit(1);
            return;
        }}}}
        Debug.Log("JulesBuildAutomation: All Alpha Test Builds completed successfully.");
        EditorApplication.Exit(0);
    }}}}

    [MenuItem("Jules/SetupRubeGoldbergGame")]
    public static void SetupRubeGoldbergGame()
    {{{{
        Debug.Log("JulesBuildAutomation: Starting Rube Goldberg Game Setup (Scene, Interactables, Prefabs)...");
        CreateBasicVRSceneElements();
        AddInteractablePhysicsObjects();
        CreateRubeGoldbergPrefabs();
        EditorApplication.Exit(0);
    }}}}

    private static void EnsureEditorFolderExists() {{{{ if (!AssetDatabase.IsValidFolder("Assets/Editor")) {{{{ AssetDatabase.CreateFolder("Assets", "Editor"); Debug.Log("JulesBuildAutomation: Created folder: Assets/Editor"); }}}}}}
    private static void InstallXRPackages() {{{{ Debug.Log("JulesBuildAutomation: Queuing XR packages for installation..."); packageIndex = 0; EditorApplication.update += ProcessPackageInstallationQueue; }}}}
    private static void ProcessPackageInstallationQueue()
    {{{{
        if (currentAddRequest != null && !currentAddRequest.IsCompleted) return;
        if (packageIndex < xrPackages.Count)
        {{{{
            string packageId = xrPackages[packageIndex];
            Debug.Log($"JulesBuildAutomation: Attempting to install package: {{{{packageId}}}}");
            currentAddRequest = Client.Add(packageId);
            packageIndex++;
        }}}}
        else
        {{{{
            EditorApplication.update -= ProcessPackageInstallationQueue;
            Debug.Log("JulesBuildAutomation: All XR package installation requests sent. Proceeding to XR Plug-in Management and OpenXR configuration after recompilation (if any)...");
            EditorApplication.delayCall += ConfigureXRSettings;
        }}}}
    }}}}
    private static void ConfigureXRSettings()
    {{{{
        Debug.Log("JulesBuildAutomation: Starting XR Plug-in Management and OpenXR configuration for all target platforms...");
        ConfigureBuildTargetXRSettings(BuildTargetGroup.Standalone, BuildTarget.StandaloneWindows64, "Windows, Mac & Linux");
        ConfigureBuildTargetXRSettings(BuildTargetGroup.Android, BuildTarget.Android, "Android");
        AssetDatabase.SaveAssets(); AssetDatabase.Refresh();
        Debug.Log("JulesBuildAutomation: XR Plug-in Management and OpenXR configuration complete.");
        Debug.Log("JulesBuildAutomation: Scheduling Rube Goldberg Game Setup to run next...");
        EditorApplication.delayCall += SetupRubeGoldbergGame;
    }}}}
    private static void ConfigureBuildTargetXRSettings(BuildTargetGroup buildTargetGroup, BuildTarget buildTarget, string tabName)
    {{{{
        Debug.Log($"JulesBuildAutomation: Configuring XR for {{{{tabName}}}}...");
        XRGeneralSettingsForEditor generalSettings;
        string settingsKey = XRGeneralSettingsForEditor.k_SettingsKey;
        if (!EditorBuildSettings.TryGetConfigObject(settingsKey, out generalSettings))
        {{{{ generalSettings = ScriptableObject.CreateInstance<XRGeneralSettingsForEditor>(); EditorBuildSettings.AddConfigObject(settingsKey, generalSettings, true); Debug.Log($"JulesBuildAutomation: Created new XRGeneralSettingsForEditor for {{{{tabName}}}}."); }}}}
        XRGeneralSettingsForEditor.SetBuildTargetSettings(buildTargetGroup, generalSettings);
        EditorUserBuildSettings.activeBuildTargetGroup = buildTargetGroup;
        EditorUserBuildSettings.SwitchActiveBuildTarget(buildTargetGroup, buildTarget);
        if (generalSettings.Manager == null) {{{{ generalSettings.Manager = ScriptableObject.CreateInstance<XRManagerSettings>(); EditorUtility.SetDirty(generalSettings); Debug.Log($"JulesBuildAutomation: Created new XRManagerSettings for {{{{tabName}}}}."); }}}}
        var currentLoaders = generalSettings.Manager.loaders;
        bool openXRLoaderFound = false; OpenXRLoader openXRLoader = null;
        foreach (var loader in currentLoaders) {{{{ if (loader is OpenXRLoader oxrLoader) {{{{ openXRLoaderFound = true; openXRLoader = oxrLoader; break; }}}}}} }}}}
        if (!openXRLoaderFound) {{{{ openXRLoader = ScriptableObject.CreateInstance<OpenXRLoader>(); currentLoaders.Add(openXRLoader); if (!generalSettings.Manager.activeLoaders.Contains(openXRLoader)) generalSettings.Manager.activeLoaders.Add(openXRLoader); EditorUtility.SetDirty(generalSettings.Manager); Debug.Log($"JulesBuildAutomation: Added OpenXR Loader to {{{{tabName}}}} XR General Settings."); }}}}
        OpenXRSettings openXRSettings = OpenXRSettings.GetForBuildTargetGroup(buildTargetGroup);
        if (openXRSettings != null)
        {{{{
            Debug.Log($"JulesBuildAutomation: Configuring {{{{tabName}}}} OpenXR settings...");
            AddOpenXRInteractionProfile(openXRSettings, "com.unity.openxr.features.oculustouchcontroller");
            AddOpenXRInteractionProfile(openXRSettings, "com.unity.openxr.features.metarequestsupport");
            AddOpenXRInteractionProfile(openXRSettings, "com.unity.openxr.features.hp_reverb_g2_controller");
            EditorUtility.SetDirty(openXRSettings);
        }}}} else {{{{ Debug.LogWarning($"JulesBuildAutomation: OpenXRSettings not found for {{{{tabName}}}}. This might indicate a problem with package installation or XR management setup."); }}}}
        EditorUtility.SetDirty(generalSettings);
    }}}}
    private static void AddOpenXRInteractionProfile(OpenXRSettings settings, string featureId)
    {{{{
        foreach (var feature in OpenXRSettings.GetAllFeatures(settings.buildTargetGroup))
        {{{{ if (feature.featureId == featureId) {{{{ if (!feature.enabled) {{{{ feature.enabled = true; Debug.Log($"JulesBuildAutomation: Enabled OpenXR feature: {{{{feature.name}}}} (ID: {{{{feature.featureId}}}}) for {{{{settings.buildTargetGroup}}}}."); }}}} else {{{{ Debug.Log($"JulesBuildAutomation: OpenXR feature: {{{{feature.name}}}} (ID: {{{{feature.featureId}}}}) already enabled for {{{{settings.buildTargetGroup}}}}."); }}}} return; }}}}}}
        Debug.LogWarning($"JulesBuildAutomation: OpenXR feature with ID '{{{{featureId}}}}' not found for {{{{settings.buildTargetGroup}}}}. Ensure the relevant package/feature set is installed.");
    }}}}
    private static void CreateBasicVRSceneElements()
    {{{{
        Debug.Log("JulesBuildAutomation: Creating basic VR scene elements...");
        string sampleScenePath = "Assets/Scenes/SampleScene.unity";
        if (!Directory.Exists("Assets/Scenes")) AssetDatabase.CreateFolder("Assets", "Scenes");
        Scene activeScene;
        if (!File.Exists(sampleScenePath)) {{{{ activeScene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single); EditorSceneManager.SaveScene(activeScene, sampleScenePath); Debug.Log($"JulesBuildAutomation: Created new scene at: {{{{sampleScenePath}}}}"); }}}}
        else {{{{ activeScene = EditorSceneManager.OpenScene(sampleScenePath); Debug.Log($"JulesBuildAutomation: Opened existing scene at: {{{{sampleScenePath}}}}"); }}}}
        GameObject mainCamera = GameObject.FindWithTag("MainCamera");
        if (mainCamera != null && mainCamera.GetComponent<Camera>() != null && mainCamera.GetComponent<Camera>().CompareTag("MainCamera")) {{{{ Debug.Log("JulesBuildAutomation: Found and removing default Main Camera."); Object.DestroyImmediate(mainCamera); }}}}
        GameObject xrOriginGO = new GameObject("XR Origin"); var xrOrigin = xrOriginGO.AddComponent<XROrigin>();
        GameObject vrCameraGO = new GameObject("Main Camera"); vrCameraGO.transform.SetParent(xrOrigin.transform); Camera vrCamera = vrCameraGO.AddComponent<Camera>(); vrCamera.tag = "MainCamera"; xrOrigin.Camera = vrCamera;
        xrOrigin.rigCamera = vrCamera.transform; xrOrigin.rigPlayspace = xrOriginGO.transform;
        if (Object.FindObjectOfType<UnityEngine.XR.Interaction.Toolkit.XRInteractionManager>() == null) {{{{ GameObject interactionManager = new GameObject("XR Interaction Manager"); interactionManager.AddComponent<UnityEngine.XR.Interaction.Toolkit.XRInteractionManager>(); Debug.Log("JulesBuildAutomation: Added XR Interaction Manager."); }}}}
        AddXRController(xrOrigin.transform, "Left Hand Controller", true); AddXRController(xrOrigin.transform, "Right Hand Controller", false);
        GameObject floor = GameObject.CreatePrimitive(PrimitiveType.Plane); floor.name = "Ground Plane"; floor.transform.position = new Vector3(0, -0.5f, 0); floor.transform.localScale = new Vector3(10, 1, 10);
        Renderer floorRenderer = floor.GetComponent<Renderer>(); if (floorRenderer != null) {{{{ floorRenderer.sharedMaterial = new Material(Shader.Find("Standard")); floorRenderer.sharedMaterial.color = Color.gray; }}}}
        EditorSceneManager.SaveScene(activeScene); AssetDatabase.SaveAssets(); AssetDatabase.Refresh(); Debug.Log("JulesBuildAutomation: Basic VR scene elements created and scene saved.");
    }}}}
    private static void AddXRController(Transform parent, string name, bool isLeftHand)
    {{{{
        GameObject controllerGO = new GameObject(name); controllerGO.transform.SetParent(parent);
        var controller = controllerGO.AddComponent<UnityEngine.XR.Interaction.Toolkit.XRController>(); controller.controllerNode = isLeftHand ? UnityEngine.XR.XRNode.LeftHand : UnityEngine.XR.XRNode.RightHand;
        if (isLeftHand) {{{{ controllerGO.AddComponent<UnityEngine.XR.Interaction.Toolkit.XRRayInteractor>(); Debug.Log($"JulesBuildAutomation: Added {{{{name}}}} with XRRayInteractor."); }}}}
        else {{{{ controllerGO.AddComponent<UnityEngine.XR.Interaction.Toolkit.XRDirectInteractor>(); Debug.Log($"JulesBuildAutomation: Added {{{{name}}}} with XRDirectInteractor."); }}}}
        GameObject visualizer = GameObject.CreatePrimitive(PrimitiveType.Sphere); visualizer.name = "Controller Visual"; visualizer.transform.SetParent(controllerGO.transform); visualizer.transform.localScale = new Vector3(0.1f, 0.1f, 0.1f); visualizer.transform.localPosition = Vector3.zero; Object.DestroyImmediate(visualizer.GetComponent<Collider>());
        Renderer visualizerRenderer = visualizer.GetComponent<Renderer>(); if (visualizerRenderer != null) {{{{ visualizerRenderer.sharedMaterial = new Material(Shader.Find("Standard")); visualizerRenderer.sharedMaterial.color = isLeftHand ? Color.blue : Color.red; }}}}
    }}}}
    private static void AddPhysicsAndInteraction(GameObject obj) {{{{ if (obj.GetComponent<Rigidbody>() == null) {{{{ Rigidbody rb = obj.AddComponent<Rigidbody>(); rb.mass = 1.0f; Debug.Log($"JulesBuildAutomation: Added Rigidbody to {{{{obj.name}}}}."); }}}} if (obj.GetComponent<XRGrabInteractable>() == null) {{{{ obj.AddComponent<XRGrabInteractable>(); Debug.Log($"JulesBuildAutomation: Added XRGrabInteractable to {{{{obj.name}}}}."); }}}} Collider collider = obj.GetComponent<Collider>(); if (collider != null) collider.isTrigger = false; }}}}
    private static void AddInteractablePhysicsObjects()
    {{{{
        Debug.Log("JulesBuildAutomation: Adding interactable physics objects...");
        Scene activeScene = EditorSceneManager.GetActiveScene(); if (!activeScene.IsValid()) {{{{ Debug.LogError("JulesBuildAutomation: No active scene found. Please ensure a scene is open."); return; }}}}
        GameObject cube = GameObject.CreatePrimitive(PrimitiveType.Cube); cube.name = "Interactable_Cube"; cube.transform.position = new Vector3(0.5f, 1f, 1f); AddPhysicsAndInteraction(cube); Renderer cubeRenderer = cube.GetComponent<Renderer>(); if (cubeRenderer != null) {{{{ cubeRenderer.sharedMaterial = new Material(Shader.Find("Standard")); cubeRenderer.sharedMaterial.color = Color.cyan; }}}} Debug.Log("JulesBuildAutomation: Added Interactable_Cube.");
        GameObject sphere = GameObject.CreatePrimitive(PrimitiveType.Sphere); sphere.name = "Interactable_Sphere"; sphere.transform.position = new Vector3(-0.5f, 1f, 1f); AddPhysicsAndInteraction(sphere); Renderer sphereRenderer = sphere.GetComponent<Renderer>(); if (sphereRenderer != null) {{{{ sphereRenderer.sharedMaterial = new Material(Shader.Find("Standard")); sphereRenderer.sharedMaterial.color = Color.magenta; }}}} Debug.Log("JulesBuildAutomation: Added Interactable_Sphere.");
        GameObject cylinder = GameObject.CreatePrimitive(PrimitiveType.Cylinder); cylinder.name = "Interactable_Cylinder"; cylinder.transform.position = new Vector3(0f, 1f, 0.5f); AddPhysicsAndInteraction(cylinder); Renderer cylinderRenderer = cylinder.GetComponent<Renderer>(); if (cylinderRenderer != null) {{{{ cylinderRenderer.sharedMaterial = new Material(Shader.Find("Standard")); cylinderRenderer.sharedMaterial.color = Color.yellow; }}}} Debug.Log("JulesBuildAutomation: Added Interactable_Cylinder.");
        EditorSceneManager.SaveScene(activeScene); AssetDatabase.SaveAssets(); AssetDatabase.Refresh(); Debug.Log("JulesBuildAutomation: Interactable physics objects added to the scene.");
    }}}}
    private static void CreateRubeGoldbergPrefabs()
    {{{{
        Debug.Log("JulesBuildAutomation: Creating Rube Goldberg prefabs...");
        string prefabsPath = "Assets/RubeGoldbergPrefabs"; if (!AssetDatabase.IsValidFolder(prefabsPath)) {{{{ AssetDatabase.CreateFolder("Assets", "RubeGoldbergPrefabs"); Debug.Log($"JulesBuildAutomation: Created folder: {{{{prefabsPath}}}}"); }}}}
        GameObject rampBase = GameObject.CreatePrimitive(PrimitiveType.Cube); rampBase.name = "Ramp_Prefab_Base"; rampBase.transform.localScale = new Vector3(1.0f, 0.1f, 2.0f); rampBase.transform.rotation = Quaternion.Euler(-15f, 0, 0); rampBase.transform.position = new Vector3(0, 0.5f, 0); AddPhysicsAndInteraction(rampBase); string rampPrefabPath = $"{{{{prefabsPath}}}}/Ramp.prefab"; PrefabUtility.SaveAsPrefabAsset(rampBase, rampPrefabPath); Object.DestroyImmediate(rampBase); Debug.Log($"JulesBuildAutomation: Created Ramp prefab at {{{{rampPrefabPath}}}}.");
        GameObject leverBase = new GameObject("Lever_Prefab_Base"); GameObject pivot = GameObject.CreatePrimitive(PrimitiveType.Cylinder); pivot.name = "Pivot"; pivot.transform.SetParent(leverBase.transform); pivot.transform.localScale = new Vector3(0.1f, 0.5f, 0.1f); pivot.transform.localPosition = new Vector3(0, 0.25f, 0); Rigidbody pivotRb = pivot.AddComponent<Rigidbody>(); pivotRb.isKinematic = true; Debug.Log($"JulesBuildAutomation: Added kinematic Rigidbody to {{{{pivot.name}}}}."); GameObject arm = GameObject.CreatePrimitive(PrimitiveType.Cube); arm.name = "Arm"; arm.transform.SetParent(leverBase.transform); arm.transform.localScale = new Vector3(0.1f, 0.1f, 1.0f); arm.transform.localPosition = new Vector3(0, 0.5f, 0.5f); Rigidbody armRb = arm.AddComponent<Rigidbody>(); armRb.mass = 0.5f; HingeJoint hj = arm.AddComponent<HingeJoint>(); hj.connectedBody = pivotRb; hj.anchor = new Vector3(0, 0, -0.5f); hj.axis = new Vector3(1, 0, 0); hj.useLimits = true; JointLimits limits = hj.limits; limits.min = -45f; limits.max = 45f; hj.limits = limits; Debug.Log($"JulesBuildAutomation: Configured HingeJoint on {{{{arm.name}}}}, connected to {{{{pivot.name}}}}."); XRGrabInteractable armGrab = arm.AddComponent<XRGrabInteractable>(); armGrab.trackPosition = false; string leverPrefabPath = $"{{{{prefabsPath}}}}/Lever.prefab"; PrefabUtility.SaveAsPrefabAsset(leverBase, leverPrefabPath); Object.DestroyImmediate(leverBase); Debug.Log($"JulesBuildAutomation: Created Lever prefab at {{{{leverPrefabPath}}}}.");
        GameObject domino = GameObject.CreatePrimitive(PrimitiveType.Cube); domino.name = "Domino_Prefab"; domino.transform.localScale = new Vector3(0.1f, 0.5f, 0.25f); AddPhysicsAndInteraction(domino); string dominoPrefabPath = $"{{{{prefabsPath}}}}/Domino.prefab"; PrefabUtility.SaveAsPrefabAsset(domino, dominoPrefabPath); Object.DestroyImmediate(domino); Debug.Log($"JulesBuildAutomation: Created Domino prefab at {{{{dominoPrefabPath}}}}.");
        AssetDatabase.SaveAssets(); AssetDatabase.Refresh(); Debug.Log("JulesBuildAutomation: All Rube Goldberg prefabs created. Automation sequence complete.");
    }}}}
}}}}
"""

    if not test_mode_no_write:
        with open("JulesBuildAutomation.cs", "w") as f:
            f.write(jules_build_automation_cs_content)
        print("MAIN_SCRIPT.PY: Wrote JulesBuildAutomation.cs")
    else:
        print("MAIN_SCRIPT.PY: JULES_TEST_MODE_NO_WRITE is active, skipped writing JulesBuildAutomation.cs")

    # --- create_unity_project_py_content ---
    # ArgumentParser description, --run-alpha-build arg, and conditional PerformAlphaTestBuild call (Subtask 2)
    # Print statements for received args (internal Subtask 5 fix attempt)
    create_unity_project_py_content = f"""
import subprocess
import os
import argparse
import time
import shutil

# Description updated in Subtask 2
parser = argparse.ArgumentParser(description="Create and setup a Unity project for VR development, with an option to run Alpha Test builds.")
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
# --run-alpha-build added in Subtask 2
parser.add_argument("--run-alpha-build", action="store_true", help="Run Alpha Test builds after project setup.")

args = parser.parse_args()

# Print received arguments for E2E testing (internal Subtask 5 fix attempt)
print(f"CREATE_UNITY_PROJECT.PY: Received project_name: {{{{args.project_name}}}}")
print(f"CREATE_UNITY_PROJECT.PY: Received run_alpha_build: {{{{args.run_alpha_build}}}}")

project_path = os.path.abspath(args.project_name)
unity_editor_path = args.unity_editor_path
cs_script_source_path = args.cs_script_source
cs_script_dest_path = os.path.join(project_path, "Assets", "Editor", "JulesBuildAutomation.cs")

def run_command(command_list, log_file_name=None, cwd=None):
    print(f"Executing command: {{{{ ' '.join(command_list) }}}}")
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
        if process.stderr: print("STDERR:", process.stderr)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {{{{e}}}}")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        if log_file_path:
            with open(log_file_path, "w") as f:
                f.write(e.stdout)
                f.write(e.stderr)
        return False
    except FileNotFoundError:
        print(f"Error: Executable not found. Please ensure '{{{{command_list[0]}}}}' is in your system's PATH or provide the full path.")
        return False

if not os.path.exists(project_path):
    print(f"Step 1: Creating Unity project '{{{{args.project_name}}}}'...")
    create_project_command = [unity_editor_path, "-quit", "-batchmode", "-createProject", project_path, "-logFile", os.path.join(project_path, "Logs", "unity_create_project.log"), "-version", args.unity_version]
    if not run_command(create_project_command, "unity_create_project.log"): exit(1)
    print(f"Unity project '{{{{args.project_name}}}}' created successfully.")
else:
    print(f"Unity project '{{{{args.project_name}}}}' already exists. Skipping project creation.")

print("Step 2: Deploying JulesBuildAutomation.cs...")
os.makedirs(os.path.dirname(cs_script_dest_path), exist_ok=True)
try:
    if not os.path.exists(cs_script_source_path):
        print(f"Error: Source C# script not found at '{{{{cs_script_source_path}}}}'.")
        exit(1)
    shutil.copy(cs_script_source_path, cs_script_dest_path)
    print(f"JulesBuildAutomation.cs deployed to {{{{cs_script_dest_path}}}}.")
except Exception as e:
    print(f"Error deploying C# script: {{{{e}}}}")
    exit(1)

time.sleep(2)

print("Step 3: Executing JulesBuildAutomation.SetupVRProject to initiate full VR project and game setup...")
setup_command = [unity_editor_path, "-batchmode", "-quit", "-projectPath", project_path, "-executeMethod", "JulesBuildAutomation.SetupVRProject", "-logFile", os.path.join(project_path, "Logs", "unity_setup_vr_and_game_log.txt")]
if not run_command(setup_command, "unity_setup_vr_and_game_log.txt"):
    print("Execution of JulesBuildAutomation.SetupVRProject failed.")
    exit(1)
print("JulesBuildAutomation.SetupVRProject completed, which handles VR setup and subsequent game scene configuration.")

# Conditional PerformAlphaTestBuild call (Subtask 2)
if args.run_alpha_build:
    print(f"Step 4: Executing JulesBuildAutomation.PerformAlphaTestBuild...")
    alpha_build_command = [unity_editor_path, "-batchmode", "-quit", "-projectPath", project_path, "-executeMethod", "JulesBuildAutomation.PerformAlphaTestBuild", "-logFile", os.path.join(project_path, "Logs", "unity_alpha_build_log.txt")]
    if not run_command(alpha_build_command, "unity_alpha_build_log.txt"):
        print("Execution of JulesBuildAutomation.PerformAlphaTestBuild failed.")
        exit(1)
    print("JulesBuildAutomation.PerformAlphaTestBuild completed.")
else:
    print("Skipping Alpha Test Builds as --run-alpha-build flag was not set.")

print("All automation steps initiated by create_unity_project.py completed successfully.")
"""

    if not test_mode_no_write:
        if not os.path.exists("scripts"):
            os.makedirs("scripts")
        with open("scripts/create_unity_project.py", "w") as f:
            f.write(create_unity_project_py_content)
        print("MAIN_SCRIPT.PY: Wrote scripts/create_unity_project.py")
    else:
        print("MAIN_SCRIPT.PY: JULES_TEST_MODE_NO_WRITE is active, skipped writing scripts/create_unity_project.py")

    # Construct the command for scripts/create_unity_project.py (Subtask 3)
    command_parts = [
        "python",
        "scripts/create_unity_project.py",
        f"--project-name {args.project_name}",
        "--unity-editor-path Unity"
    ]
    if args.alpha_build: # From Subtask 3
        command_parts.append("--run-alpha-build")
    jules_command = " ".join(command_parts)

    print(f"To create/setup the Unity project, run the following command from the repository root:")
    print(jules_command)

# From Subtask 3
if __name__ == "__main__":
    main()
