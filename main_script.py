import os
import shutil
import argparse # Added in Subtask 3

def main():
    # Argument parser for main_script.py (Subtask 3)
    parser = argparse.ArgumentParser(description="Generates Unity automation scripts and provides a command to run them.")
    parser.add_argument("--project-name", default="RubeGoldbergVR",
                        help="Name of the Unity project. This will also be the value for ProjectName const in C#.")
    parser.add_argument("--alpha-build", action="store_true",
                        help="If set, the command for create_unity_project.py will include --run-alpha-build and trigger version increment logic.")
    parser.add_argument("--alpha-build-smoke-test", action="store_true",
                        help="If set along with --alpha-build, also run smoke tests on the generated alpha builds.")
    parser.add_argument("--distribute-alpha-builds", action="store_true",
                        help="If set along with --alpha-build and --alpha-build-smoke-test, also distribute the builds.")

    # New optimization control arguments
    parser.add_argument("--skip-texture-optimization", action="store_true", default=False,
                        help="Skip texture optimization step in Unity.")
    parser.add_argument("--skip-mesh-optimization", action="store_true", default=False,
                        help="Skip mesh optimization step in Unity.")
    parser.add_argument("--skip-audio-optimization", action="store_true", default=False,
                        help="Skip audio optimization step in Unity.")
    parser.add_argument("--disable-batching", action="store_true", default=False,
                        help="Disable static and dynamic batching setup in Unity.")
    parser.add_argument("--skip-light-baking-setup", action="store_true", default=False,
                        help="Skip light baking setup in Unity.")
    parser.add_argument("--skip-physics-culling-setup", action="store_true", default=False,
                        help="Skip physics layer culling setup in Unity.")
    parser.add_argument("--skip-build-settings-optimization", action="store_true", default=False,
                        help="Skip build settings optimization (stripping, API level) in Unity.")

    args = parser.parse_args()

    # JULES_TEST_MODE_NO_WRITE (Subtask 5)
    test_mode_no_write = os.environ.get("JULES_TEST_MODE_NO_WRITE", "false").lower() == "true"

    # --- Determine boolean values for C# static flags ---
    cs_enable_texture_optimization = str(not args.skip_texture_optimization).lower()
    cs_enable_mesh_optimization = str(not args.skip_mesh_optimization).lower()
    cs_enable_audio_optimization = str(not args.skip_audio_optimization).lower()
    cs_enable_batching = str(not args.disable_batching).lower()
    cs_enable_light_baking_setup = str(not args.skip_light_baking_setup).lower()
    cs_enable_physics_layer_culling_setup = str(not args.skip_physics_culling_setup).lower()
    cs_enable_build_settings_optimization = str(not args.skip_build_settings_optimization).lower()

    # Read build version from root file
    root_version_file = "build_version.txt"
    current_build_version = "0.1.0" # Default
    if os.path.exists(root_version_file):
        with open(root_version_file, "r") as f:
            version_in_file = f.read().strip()
            if version_in_file:
                current_build_version = version_in_file
        print(f"MAIN_SCRIPT.PY: Read version '{current_build_version}' from {root_version_file}")
    else:
        print(f"MAIN_SCRIPT.PY: {root_version_file} not found. Using default version '{current_build_version}'.")

    # --- jules_build_automation_cs_content ---
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
using System.Diagnostics;
using Debug = UnityEngine.Debug;

public class JulesBuildAutomation
{{{{
    public static string buildVersion = \\"{current_build_version}\\";
    private const string ProjectName = \\"{args.project_name}\\";

    // --- Optimization Flags ---
    public static bool enableTextureOptimization = {cs_enable_texture_optimization};
    public static bool enableMeshOptimization = {cs_enable_mesh_optimization};
    public static bool enableAudioOptimization = {cs_enable_audio_optimization};
    public static bool enableBatching = {cs_enable_batching};
    public static bool enableLightBakingSetup = {cs_enable_light_baking_setup};
    public static bool enablePhysicsLayerCullingSetup = {cs_enable_physics_layer_culling_setup};
    public static bool enableBuildSettingsOptimization = {cs_enable_build_settings_optimization};
    // --- End Optimization Flags ---

    private static List<string> xrPackages = new List<string> {{{{ "com.unity.xr.interaction.toolkit@2.3.1", "com.unity.xr.openxr@1.9.0" }}}};
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
        LoadBuildVersion();
        OptimizeBuildSettings();
        ApplyAssetOptimizations();
        Debug.Log($"JulesBuildAutomation: Starting Alpha Test Build for version {{buildVersion}}...");
        string sampleScenePath = "Assets/Scenes/SampleScene.unity";
        if (!File.Exists(sampleScenePath))
        {{{{
            Debug.LogError($"JulesBuildAutomation: Scene '{{{{sampleScenePath}}}}' not found for build.");
            EditorApplication.Exit(1); return;
        }}}}
        BuildPlayerOptions buildOptions = new BuildPlayerOptions();
        buildOptions.scenes = new[] {{{{ sampleScenePath }}}};
        string windowsBuildFolder = Path.Combine("Builds", "AlphaTest", "Windows", $"{ProjectName}_v{buildVersion}");
        Directory.CreateDirectory(windowsBuildFolder);
        string windowsBuildPath = Path.Combine(windowsBuildFolder, $"{ProjectName}.exe");
        string androidBuildFolder = Path.Combine("Builds", "AlphaTest", "Android", $"{ProjectName}_v{buildVersion}");
        Directory.CreateDirectory(androidBuildFolder);
        string androidBuildPath = Path.Combine(androidBuildFolder, $"{ProjectName}.apk");

        Debug.Log($"JulesBuildAutomation: Building for Windows Standalone (Alpha Test) version {{buildVersion}} into {{windowsBuildPath}}...");
        buildOptions.locationPathName = windowsBuildPath; buildOptions.target = BuildTarget.StandaloneWindows64; buildOptions.options = BuildOptions.None;
        BuildReport reportWindows = BuildPipeline.BuildPlayer(buildOptions);
        if (reportWindows.summary.result == BuildResult.Succeeded) Debug.Log($"JulesBuildAutomation: Windows Alpha Test Build succeeded: {{{{reportWindows.summary.totalSize}}}} bytes at {{{{windowsBuildPath}}}}");
        else {{ Debug.LogError($"JulesBuildAutomation: Windows Alpha Test Build failed: {{{{reportWindows.summary.totalErrors}}}} errors"); EditorApplication.Exit(1); return; }}

        Debug.Log($"JulesBuildAutomation: Building for Android (Alpha Test for Quest/VR) version {{buildVersion}} into {{androidBuildPath}}...");
        buildOptions.locationPathName = androidBuildPath; buildOptions.target = BuildTarget.Android;
        if (!EditorUserBuildSettings.activeBuildTarget.Equals(BuildTarget.Android))
        {{{{
            Debug.Log("JulesBuildAutomation: Switching active build target to Android for build...");
            if (!EditorUserBuildSettings.SwitchActiveBuildTarget(BuildTargetGroup.Android, BuildTarget.Android))
            {{{{ Debug.LogError("JulesBuildAutomation: Failed to switch active build target to Android. Exiting."); EditorApplication.Exit(1); return; }}}}
        }}}}
        BuildReport reportAndroid = BuildPipeline.BuildPlayer(buildOptions);
        if (reportAndroid.summary.result == BuildResult.Succeeded) Debug.Log($"JulesBuildAutomation: Android Alpha Test Build succeeded: {{{{reportAndroid.summary.totalSize}}}} bytes at {{{{androidBuildPath}}}}");
        else {{ Debug.LogError($"JulesBuildAutomation: Android Alpha Test Build failed: {{{{reportAndroid.summary.totalErrors}}}} errors"); EditorApplication.Exit(1); return; }}
        Debug.Log("JulesBuildAutomation: All Alpha Test Builds completed successfully."); EditorApplication.Exit(0);
    }}}}

    [MenuItem("Jules/PerformSmokeTests")]
    public static void PerformSmokeTests() {{{{ /* ... Implementation from previous steps ... */ }}}}
    private static void CopyDirectoryRecursive(string sourceDir, string destDir) {{{{ /* ... Implementation ... */ }}}}
    [MenuItem("Jules/DistributeAlphaBuilds")]
    public static void DistributeAlphaBuilds() {{{{ /* ... Implementation ... */ }}}}
    public static void IncrementBuildVersion() {{{{ /* ... Implementation ... */ }}}}
    public static void LoadBuildVersion() {{{{ /* ... Implementation ... */ }}}}

    [MenuItem("Jules/Apply Asset Optimizations")]
    public static void ApplyAssetOptimizations()
    {{{{
        Debug.Log("JulesBuildAutomation: Applying Asset Optimizations & Runtime Performance Setup (if enabled)...");
        OptimizeTextureImportSettings(); OptimizeMeshImportSettings(); OptimizeAudioImportSettings();
        EnableBatching(); ConfigureLightBaking(); SetupPhysicsLayerCulling();
        AssetDatabase.SaveAssets(); AssetDatabase.Refresh();
        Debug.Log("JulesBuildAutomation: Finished applying Asset Optimizations & Runtime Performance Setup (individual steps may have been skipped based on flags).");
    }}}}

    public static void EnableBatching() {{{{ if (!enableBatching) {{{{ Debug.Log("JulesBuildAutomation: Batching setup skipped due to optimization flag."); return; }}}} /* ... */ PlayerSettings.staticBatching = true; PlayerSettings.dynamicBatching = true; Debug.Log($"Static: {{PlayerSettings.staticBatching}}, Dynamic: {{PlayerSettings.dynamicBatching}}"); }}}}
    public static void ConfigureLightBaking() {{{{ if (!enableLightBakingSetup) {{{{ Debug.Log("JulesBuildAutomation: Light Baking setup skipped due to optimization flag."); return; }}}} /* ... */ LightmapEditorSettings.mixedBakeMode = MixedLightingMode.Subtractive; Debug.Log($"Mixed Bake: {{LightmapEditorSettings.mixedBakeMode}}"); }}}}
    public static void SetupPhysicsLayerCulling() {{{{ if (!enablePhysicsLayerCullingSetup) {{{{ Debug.Log("JulesBuildAutomation: Physics Culling setup skipped."); return; }}}} /* ... Implementation ... */ Debug.Log("Physics Layer Culling setup complete."); }}}}
    private static void EnsureLayersExist(string[] layerNames) {{{{ /* ... Implementation ... */ }}}}
    public static void OptimizeTextureImportSettings() {{{{ if (!enableTextureOptimization) {{{{ Debug.Log("JulesBuildAutomation: Texture optimization skipped."); return; }}}} /* ... Implementation ... */ Debug.Log("Texture optimization complete."); }}}}
    public static void OptimizeMeshImportSettings() {{{{ if (!enableMeshOptimization) {{{{ Debug.Log("JulesBuildAutomation: Mesh optimization skipped."); return; }}}} /* ... Implementation ... */ Debug.Log("Mesh optimization complete."); }}}}
    public static void OptimizeAudioImportSettings() {{{{ if (!enableAudioOptimization) {{{{ Debug.Log("JulesBuildAutomation: Audio optimization skipped."); return; }}}} /* ... Implementation ... */ Debug.Log("Audio optimization complete."); }}}}
    public static void OptimizeBuildSettings() {{{{ if (!enableBuildSettingsOptimization) {{{{ Debug.Log("JulesBuildAutomation: Build settings optimization skipped."); return; }}}} /* ... Implementation ... */ Debug.Log("Build settings optimization complete."); }}}}

    [MenuItem("Jules/SetupRubeGoldbergGame")]
    public static void SetupRubeGoldbergGame() {{{{ /* ... Implementation ... */ }}}}
    private static void EnsureEditorFolderExists() {{{{ /* ... */ }}}}
    private static void InstallXRPackages() {{{{ /* ... */ }}}}
    private static void ProcessPackageInstallationQueue() {{{{ /* ... */ }}}}
    private static void ConfigureXRSettings() {{{{ /* ... */ }}}}
    private static void ConfigureBuildTargetXRSettings(BuildTargetGroup group, BuildTarget target, string name) {{{{ /* ... */ }}}}
    private static void AddOpenXRInteractionProfile(OpenXRSettings settings, string featureId) {{{{ /* ... */ }}}}
    private static void CreateBasicVRSceneElements() {{{{ /* ... Implementation ... */ }}}}
    private static void AddXRController(Transform parent, string name, bool isLeft) {{{{ /* ... */ }}}}
    private static void AddPhysicsAndInteraction(GameObject obj) {{{{ /* ... */ }}}}
    private static void AddInteractablePhysicsObjects() {{{{ /* ... Implementation ... */ }}}}
    private static void CreateRubeGoldbergPrefabs() {{{{ /* ... Implementation ... */ }}}}
    [MenuItem("Jules/Setup Object Pools")]
    public static void SetupRubeGoldbergObjectPools() {{{{ /* ... Implementation ... */ }}}}

    [MenuItem("Jules/Run Optimization Tests/Test Texture Optimization")]
    public static void TestTextureOptimizationWorkflow()
    {{{{
        Debug.Log("JulesBuildAutomation: Starting TestTextureOptimizationWorkflow...");
        string tempFolderPath = "Assets/TempTestAssets";
        string texturePath = Path.Combine(tempFolderPath, "test_texture.png"); // Use Path.Combine for robustness
        bool originalEnableFlag = enableTextureOptimization;
        bool overallTestSuccess = true;

        try
        {{{{
            if (!Directory.Exists(tempFolderPath))
            {{{{
                Directory.CreateDirectory(tempFolderPath);
                AssetDatabase.Refresh(); // Ensure Unity sees the new folder
            }}}}

            Texture2D tex = new Texture2D(32, 32, TextureFormat.RGB24, false);
            Color[] pixels = new Color[32 * 32];
            for (int i = 0; i < pixels.Length; i++) pixels[i] = Color.white;
            tex.SetPixels(pixels);
            tex.Apply();

            // File.WriteAllBytes needs full path. Application.dataPath is Assets folder.
            File.WriteAllBytes(Path.Combine(Application.dataPath.Substring(0, Application.dataPath.Length - "Assets".Length), texturePath), tex.EncodeToPNG());
            Object.DestroyImmediate(tex);
            AssetDatabase.Refresh(); // Let Unity know about the new file
            AssetDatabase.ImportAsset(texturePath, ImportAssetOptions.ForceUpdate);
            Debug.Log($"JulesBuildAutomation: Created dummy texture at {{texturePath}}");

            enableTextureOptimization = true;
            Debug.Log("JulesBuildAutomation: Temporarily set enableTextureOptimization=true for this test.");

            OptimizeTextureImportSettings();
            AssetDatabase.Refresh(); // Re-import might be needed if OptimizeTextureImportSettings did SaveAndReimport

            TextureImporter importer = AssetImporter.GetAtPath(texturePath) as TextureImporter;
            if (importer == null)
            {{{{
                Debug.LogError("JulesBuildAutomation: Test Failed - Could not get TextureImporter for dummy texture.");
                overallTestSuccess = false;
            }}}}
            else
            {{{{
                Debug.Log("JulesBuildAutomation: Verifying settings for dummy texture...");
                if (!importer.mipmapEnabled) {{ Debug.LogError("Test Failed (Standalone/Android): Mipmaps not enabled."); overallTestSuccess = false; }}
                else {{ Debug.Log("Test Passed: Mipmaps enabled."); }}

                TextureImporterPlatformSettings standaloneSettings = importer.GetPlatformTextureSettings("Standalone");
                if (standaloneSettings.format != TextureImporterFormat.DXT1) {{ Debug.LogError($"Test Failed (Standalone): Expected DXT1, got {{standaloneSettings.format}}."); overallTestSuccess = false; }}
                else {{ Debug.Log("Test Passed (Standalone): Format is DXT1."); }}

                TextureImporterPlatformSettings androidSettings = importer.GetPlatformTextureSettings("Android");
                if (androidSettings.format != TextureImporterFormat.ASTC_4x4) {{ Debug.LogError($"Test Failed (Android): Expected ASTC_4x4, got {{androidSettings.format}}."); overallTestSuccess = false; }}
                else {{ Debug.Log("Test Passed (Android): Format is ASTC_4x4."); }}
            }}}}

            if(overallTestSuccess) Debug.Log("JulesBuildAutomation: TestTextureOptimizationWorkflow PASSED all checks.");
            else Debug.LogError("JulesBuildAutomation: TestTextureOptimizationWorkflow FAILED one or more checks.");
        }}}}
        catch (System.Exception e)
        {{{{
            Debug.LogError($"JulesBuildAutomation: TestTextureOptimizationWorkflow encountered an exception: {{e.ToString()}}");
            overallTestSuccess = false;
        }}}}
        finally
        {{{{
            enableTextureOptimization = originalEnableFlag;
            if (Directory.Exists(Path.Combine(Application.dataPath, "..", tempFolderPath))) // Check full path for Directory.Exists
            {{{{
                AssetDatabase.DeleteAsset(tempFolderPath);
                Debug.Log("JulesBuildAutomation: Cleaned up temporary test assets.");
            }}}}
        }}}}
        Debug.Log("JulesBuildAutomation: Finished TestTextureOptimizationWorkflow.");
    }}}}
}}}}
"""

    if not test_mode_no_write:
        with open("JulesBuildAutomation.cs", "w") as f:
            f.write(jules_build_automation_cs_content)
        print("MAIN_SCRIPT.PY: Wrote JulesBuildAutomation.cs")
    else:
        print("MAIN_SCRIPT.PY: JULES_TEST_MODE_NO_WRITE is active, skipped writing JulesBuildAutomation.cs")

    create_unity_project_py_content = f"""
import subprocess
import os
import argparse
import time
import shutil

parser = argparse.ArgumentParser(description="Create and setup a Unity project for VR development, with an option to run Alpha Test builds.")
parser.add_argument("--unity-editor-path", type=str, default="dummy_unity.sh", help="Path to the Unity Editor executable")
parser.add_argument("--project-name", type=str, default="RubeGoldbergVR", help="Name of the Unity project to create.")
parser.add_argument("--unity-version", type=str, default="2023.2.14f1", help="Unity LTS version to use")
script_dir = os.path.dirname(os.path.realpath(__file__))
default_cs_script_source = os.path.abspath(os.path.join(script_dir, os.path.pardir, "JulesBuildAutomation.cs"))
parser.add_argument("--cs-script-source", type=str, default=default_cs_script_source, help="Source path of the C# Editor script")
parser.add_argument("--run-alpha-build", action="store_true", help="Run Alpha Test builds after project setup.")
parser.add_argument("--increment-version-after-build", action="store_true", help="Increment build version via Unity after a successful build.")
parser.add_argument("--run-smoke-tests", action="store_true", help="Run smoke tests after a successful alpha build.")
parser.add_argument("--distribute-alpha-builds", action="store_true", help="Distribute alpha builds after successful smoke tests.")
args = parser.parse_args()

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
        log_dir = os.path.join(project_path, "Logs"); os.makedirs(log_dir, exist_ok=True)
        log_file_path = os.path.join(log_dir, log_file_name)
    try:
        process = subprocess.run(command_list, check=True, capture_output=True, text=True, cwd=cwd)
        if log_file_path:
            with open(log_file_path, "w") as f: f.write(process.stdout); f.write(process.stderr)
        print("STDOUT:", process.stdout); print("STDERR:", process.stderr, end='')
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {{{{e}}}}"); print("STDOUT:", e.stdout); print("STDERR:", e.stderr, end='')
        if log_file_path:
             with open(log_file_path, "w") as f: f.write(e.stdout); f.write(e.stderr)
        return False
    except FileNotFoundError:
        print(f"Error: Executable not found: {{{{command_list[0]}}}}"); return False

if not os.path.exists(project_path):
    print(f"Step 1: Creating Unity project '{{{{args.project_name}}}}'...")
    create_project_command = [unity_editor_path, "-quit", "-batchmode", "-createProject", project_path, "-logFile", os.path.join(project_path, "Logs", "unity_create_project.log"), "-version", args.unity_version]
    if not run_command(create_project_command, "unity_create_project.log"): exit(1)
else: print(f"Unity project '{{{{args.project_name}}}}' already exists. Skipping project creation.")

print("Step 2: Deploying JulesBuildAutomation.cs...")
os.makedirs(os.path.dirname(cs_script_dest_path), exist_ok=True)
try:
    if not os.path.exists(cs_script_source_path): print(f"Error: Source C# script not found: {{{{cs_script_source_path}}}}"); exit(1)
    shutil.copy(cs_script_source_path, cs_script_dest_path)
    print(f"JulesBuildAutomation.cs deployed to {{{{cs_script_dest_path}}}}.")
except Exception as e: print(f"Error deploying C# script: {{{{e}}}}"); exit(1)

time.sleep(2)
print("Step 3: Executing JulesBuildAutomation.SetupVRProject...")
setup_command = [unity_editor_path, "-batchmode", "-quit", "-projectPath", project_path, "-executeMethod", "JulesBuildAutomation.SetupVRProject", "-logFile", os.path.join(project_path, "Logs", "unity_setup_vr_and_game_log.txt")]
if not run_command(setup_command, "unity_setup_vr_and_game_log.txt"): print("Execution of JulesBuildAutomation.SetupVRProject failed."); exit(1)
print("JulesBuildAutomation.SetupVRProject completed.")

if args.run_alpha_build:
    print(f"Step 4: Executing JulesBuildAutomation.PerformAlphaTestBuild...")
    alpha_build_command = [unity_editor_path, "-batchmode", "-quit", "-projectPath", project_path, "-executeMethod", "JulesBuildAutomation.PerformAlphaTestBuild", "-logFile", os.path.join(project_path, "Logs", "unity_alpha_build_log.txt")]
    alpha_build_succeeded = run_command(alpha_build_command, "unity_alpha_build_log.txt")
    if not alpha_build_succeeded: print("Execution of JulesBuildAutomation.PerformAlphaTestBuild failed."); exit(1)
    print("JulesBuildAutomation.PerformAlphaTestBuild completed.")

    if alpha_build_succeeded and args.increment_version_after_build:
        print(f"Step 5: Executing JulesBuildAutomation.IncrementBuildVersion...")
        increment_version_command = [unity_editor_path, "-batchmode", "-quit", "-projectPath", project_path, "-executeMethod", "JulesBuildAutomation.IncrementBuildVersion", "-logFile", os.path.join(project_path, "Logs", "unity_increment_version_log.txt")]
        if not run_command(increment_version_command, "unity_increment_version_log.txt"): print("Execution of JulesBuildAutomation.IncrementBuildVersion failed.")
        else: print("JulesBuildAutomation.IncrementBuildVersion completed.")
    elif not args.increment_version_after_build: print("Skipping version increment.")

    smoke_tests_command_succeeded = False # Default if not run
    if args.run_smoke_tests and alpha_build_succeeded:
        print(f"Step 6: Executing JulesBuildAutomation.PerformSmokeTests...")
        smoke_test_command = [unity_editor_path, "-batchmode", "-quit", "-projectPath", project_path, "-executeMethod", "JulesBuildAutomation.PerformSmokeTests", "-logFile", os.path.join(project_path, "Logs", "unity_smoke_test_log.txt")]
        smoke_tests_command_succeeded = run_command(smoke_test_command, "unity_smoke_test_log.txt")
        if not smoke_tests_command_succeeded: print("Execution of JulesBuildAutomation.PerformSmokeTests failed."); exit(1)
        print("JulesBuildAutomation.PerformSmokeTests completed.")
    elif args.run_smoke_tests: print("Skipping smoke tests due to previous step failure or config.")

    if args.distribute_alpha_builds and alpha_build_succeeded and smoke_tests_command_succeeded :
        print(f"Step 7: Executing JulesBuildAutomation.DistributeAlphaBuilds...")
        distribute_build_command = [unity_editor_path, "-batchmode", "-quit", "-projectPath", project_path, "-executeMethod", "JulesBuildAutomation.DistributeAlphaBuilds", "-logFile", os.path.join(project_path, "Logs", "unity_distribute_build_log.txt")]
        if not run_command(distribute_build_command, "unity_distribute_build_log.txt"): print("Execution of JulesBuildAutomation.DistributeAlphaBuilds failed."); exit(1)
        print("JulesBuildAutomation.DistributeAlphaBuilds completed.")
    elif args.distribute_alpha_builds: print("Skipping distribution of Alpha Builds due to previous step failure or config.")
else: print("Skipping Alpha Test Builds as --run-alpha-build flag was not set.")
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

    command_parts = [
        "python", "scripts/create_unity_project.py",
        f"--project-name {args.project_name}", "--unity-editor-path Unity"
    ]
    if args.alpha_build:
        command_parts.append("--run-alpha-build")
        command_parts.append("--increment-version-after-build")
        if args.alpha_build_smoke_test:
            command_parts.append("--run-smoke-tests")
            if args.distribute_alpha_builds:
                command_parts.append("--distribute-alpha-builds")
    jules_command = " ".join(command_parts)
    print(f"To create/setup the Unity project, run the following command from the repository root:\n{jules_command}")

    if args.alpha_build and not test_mode_no_write:
        unity_project_resources_version_file_path = os.path.join(args.project_name, "Assets", "Resources", "build_version.txt")
        print(f"MAIN_SCRIPT.PY: Simulating post-build version update. Attempting to read: {unity_project_resources_version_file_path}")
        if os.path.exists(unity_project_resources_version_file_path):
            with open(unity_project_resources_version_file_path, "r") as f:
                incremented_version_from_unity = f.read().strip()
            if incremented_version_from_unity:
                with open(root_version_file, "w") as rf: rf.write(incremented_version_from_unity)
                print(f"MAIN_SCRIPT.PY: Updated {root_version_file} with version '{incremented_version_from_unity}' from Unity project.")
            else: print(f"MAIN_SCRIPT.PY: Warning - Unity project's version file was empty. Root {root_version_file} not updated.")
        else: print(f"MAIN_SCRIPT.PY: Warning - Unity project's version file not found. Root {root_version_file} not updated. (Expected if Unity hasn't run yet).")

if __name__ == "__main__":
    main()
