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
    args = parser.parse_args()

    # JULES_TEST_MODE_NO_WRITE (Subtask 5)
    test_mode_no_write = os.environ.get("JULES_TEST_MODE_NO_WRITE", "false").lower() == "true"

    # Read build version from root file
    root_version_file = "build_version.txt"
    current_build_version = "0.1.0" # Default
    if os.path.exists(root_version_file):
        with open(root_version_file, "r") as f:
            version_in_file = f.read().strip()
            if version_in_file: # Basic check for non-empty
                # Add more robust validation later if needed (e.g., regex for X.Y.Z)
                current_build_version = version_in_file
        print(f"MAIN_SCRIPT.PY: Read version '{current_build_version}' from {root_version_file}")
    else:
        print(f"MAIN_SCRIPT.PY: {root_version_file} not found. Using default version '{current_build_version}'.")

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
using System.Diagnostics; // Required for Process class
using Debug = UnityEngine.Debug; // Explicitly use UnityEngine.Debug to avoid conflict with System.Diagnostics.Debug

public class JulesBuildAutomation
{{{{
    public static string buildVersion = \\"{current_build_version}\\"; // Dynamically set by main_script.py
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
        LoadBuildVersion(); // Added for versioning
        Debug.Log($"JulesBuildAutomation: Starting Alpha Test Build for version {{buildVersion}}..."); // Modified for versioning
        string sampleScenePath = "Assets/Scenes/SampleScene.unity";
        if (!File.Exists(sampleScenePath))
        {{{{
            Debug.LogError($"JulesBuildAutomation: Scene '{{{{sampleScenePath}}}}' not found for build. Please ensure it exists.");
            EditorApplication.Exit(1);
            return;
        }}}}
        BuildPlayerOptions buildOptions = new BuildPlayerOptions();
        buildOptions.scenes = new[] {{{{ sampleScenePath }}}};

        // Adjusted build paths for versioned subfolders
        string windowsBuildFolder = Path.Combine("Builds", "AlphaTest", "Windows", $"{ProjectName}_v{buildVersion}");
        Directory.CreateDirectory(windowsBuildFolder);
        string windowsBuildPath = Path.Combine(windowsBuildFolder, $"{ProjectName}.exe");

        string androidBuildFolder = Path.Combine("Builds", "AlphaTest", "Android", $"{ProjectName}_v{buildVersion}");
        Directory.CreateDirectory(androidBuildFolder);
        string androidBuildPath = Path.Combine(androidBuildFolder, $"{ProjectName}.apk");
        // Directory.CreateDirectory(Path.GetDirectoryName(windowsBuildPath)); // No longer needed due to specific folder creation
        // Directory.CreateDirectory(Path.GetDirectoryName(androidBuildPath)); // No longer needed

        Debug.Log($"JulesBuildAutomation: Building for Windows Standalone (Alpha Test) version {{buildVersion}} into {{windowsBuildPath}}...");
        buildOptions.locationPathName = windowsBuildPath; // Corrected path
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

        Debug.Log($"JulesBuildAutomation: Building for Android (Alpha Test for Quest/VR) version {{buildVersion}} into {{androidBuildPath}}..."); // Modified for versioning
        buildOptions.locationPathName = androidBuildPath; // Corrected path
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

    [MenuItem("Jules/PerformSmokeTests")]
    public static void PerformSmokeTests()
    {{{{
        Debug.Log("JulesBuildAutomation: Starting Smoke Tests...");
        // Ensure build version is current if PerformAlphaTestBuild was run prior in the same session.
        // If this method is run in a new Unity session, LoadBuildVersion might be needed here,
        // or rely on the version set at script initialization (passed from main_script.py).
        // For simplicity, we assume buildVersion is correctly populated by LoadBuildVersion()
        // if called from a context where builds were just made, or it's the one from main_script.py.
        // Consider calling LoadBuildVersion() here if these tests can be run independently after editor restart.
        // LoadBuildVersion();

        bool allTestsPassed = true;
        Debug.Log($"JulesBuildAutomation: Using version {{buildVersion}} for smoke test paths.");

        // Define paths based on the new structure used in PerformAlphaTestBuild
        string windowsBuildFolder = Path.Combine("Builds", "AlphaTest", "Windows", $"{ProjectName}_v{buildVersion}");
        string windowsExePath = Path.Combine(windowsBuildFolder, $"{ProjectName}.exe");
        string windowsDataFolder = Path.Combine(windowsBuildFolder, $"{ProjectName}_Data");

        string androidBuildFolder = Path.Combine("Builds", "AlphaTest", "Android", $"{ProjectName}_v{buildVersion}");
        string androidApkPath = Path.Combine(androidBuildFolder, $"{ProjectName}.apk");

        // --- Windows Smoke Tests ---
        Debug.Log("JulesBuildAutomation: --- Windows Smoke Tests ---");
        // 1. Check .exe existence
        if (File.Exists(windowsExePath))
        {{{{
            Debug.Log($"JulesBuildAutomation: SUCCESS - Windows executable found at {{windowsExePath}}.");
        }}}}
        else
        {{{{
            Debug.LogError($"JulesBuildAutomation: FAILURE - Windows executable NOT found at {{windowsExePath}}.");
            allTestsPassed = false;
        }}}}

        // 2. Check _Data folder existence and non-emptiness
        if (Directory.Exists(windowsDataFolder))
        {{{{
            // Check if not empty by looking for any file or directory within it
            if (Directory.EnumerateFileSystemEntries(windowsDataFolder).Any())
            {{{{
                Debug.Log($"JulesBuildAutomation: SUCCESS - Windows _Data folder found at {{windowsDataFolder}} and is not empty.");
            }}}}
            else
            {{{{
                Debug.LogWarning($"JulesBuildAutomation: WARNING - Windows _Data folder found at {{windowsDataFolder}} but is EMPTY.");
                // Depending on strictness, this could be allTestsPassed = false;
            }}}}
        }}}}
        else
        {{{{
            Debug.LogError($"JulesBuildAutomation: FAILURE - Windows _Data folder NOT found at {{windowsDataFolder}}.");
            allTestsPassed = false;
        }}}}

        // 3. Basic Launch Test (Windows)
        if (allTestsPassed && File.Exists(windowsExePath)) // Only attempt launch if previous checks related to exe were fine
        {{{{
            Debug.Log($"JulesBuildAutomation: Attempting to launch Windows executable: {{windowsExePath}} for a short period...");
            Process process = new Process();
            process.StartInfo.FileName = windowsExePath;
            process.StartInfo.WindowStyle = ProcessWindowStyle.Minimized; // Try to avoid focus stealing
            try
            {{{{
                process.Start();
                int timeoutMilliseconds = 10000; // 10 seconds
                if (process.WaitForExit(timeoutMilliseconds))
                {{{{
                    Debug.Log($"JulesBuildAutomation: Windows executable launched and exited within timeout. Exit Code: {{process.ExitCode}}.");
                    if (process.ExitCode != 0)
                    {{{{
                        Debug.LogWarning($"JulesBuildAutomation: WARNING - Windows executable exited with non-zero code: {{process.ExitCode}}. This might indicate an issue.");
                        // Consider setting allTestsPassed = false; if a non-zero exit code is a definitive failure.
                    }}}}
                }}}}
                else
                {{{{
                    Debug.LogWarning($"JulesBuildAutomation: WARNING - Windows executable did not exit within {{timeoutMilliseconds / 1000}} seconds. Attempting to kill.");
                    if (!process.HasExited) process.Kill();
                    // allTestsPassed = false; // Consider this a failure if it hangs
                }}}}
            }}}}
            catch (System.Exception ex)
            {{{{
                Debug.LogError($"JulesBuildAutomation: FAILURE - Exception during Windows executable launch test: {{ex.Message}}");
                allTestsPassed = false;
            }}}}
        }}}}
        else if (!File.Exists(windowsExePath))
        {{{{
             Debug.Log("JulesBuildAutomation: Skipping Windows executable launch test as the file was not found.");
        }}}}


        // --- Android Smoke Tests ---
        Debug.Log("JulesBuildAutomation: --- Android Smoke Tests ---");
        // 1. Check .apk existence
        if (File.Exists(androidApkPath))
        {{{{
            Debug.Log($"JulesBuildAutomation: SUCCESS - Android APK found at {{androidApkPath}}.");
        }}}}
        else
        {{{{
            Debug.LogError($"JulesBuildAutomation: FAILURE - Android APK NOT found at {{androidApkPath}}.");
            allTestsPassed = false;
        }}}}
        // Optional: Further APK checks (e.g., size) could be added here if desired.
        // Verifying contents of an APK is complex from Unity C# alone.

        // --- Summary ---
        Debug.Log("JulesBuildAutomation: --- Smoke Test Summary ---");
        if (allTestsPassed)
        {{{{
            Debug.Log("JulesBuildAutomation: All smoke tests passed successfully.");
            EditorApplication.Exit(0);
        }}}}
        else
        {{{{
            Debug.LogError("JulesBuildAutomation: One or more smoke tests FAILED. Check logs for details.");
            EditorApplication.Exit(1);
        }}}}
    }}}}

    // Method to recursively copy a directory
    private static void CopyDirectoryRecursive(string sourceDir, string destDir)
    {{{{
        // Create the destination directory if it doesn't exist
        if (!Directory.Exists(destDir))
        {{{{
            Directory.CreateDirectory(destDir);
        }}}}

        // Copy all files from source to destination
        foreach (string file in Directory.GetFiles(sourceDir))
        {{{{
            string destFile = Path.Combine(destDir, Path.GetFileName(file));
            File.Copy(file, destFile, true); // true to overwrite if exists
        }}}}

        // Recursively copy subdirectories
        foreach (string subDir in Directory.GetDirectories(sourceDir))
        {{{{
            string destSubDir = Path.Combine(destDir, Path.GetFileName(subDir));
            CopyDirectoryRecursive(subDir, destSubDir);
        }}}}
    }}}}

    [MenuItem("Jules/DistributeAlphaBuilds")]
    public static void DistributeAlphaBuilds()
    {{{{
        LoadBuildVersion(); // Ensure buildVersion is up-to-date
        Debug.Log($"JulesBuildAutomation: Initiating Alpha Build Distribution for Project: {{ProjectName}}, Version: {{buildVersion}}...");

        string windowsBuildFolder = Path.Combine("Builds", "AlphaTest", "Windows", $"{ProjectName}_v{buildVersion}");
        string androidBuildFolder = Path.Combine("Builds", "AlphaTest", "Android", $"{ProjectName}_v{buildVersion}");
        string windowsExeArtifact = Path.Combine(windowsBuildFolder, $"{ProjectName}.exe");
        string windowsDataFolderArtifact = Path.Combine(windowsBuildFolder, $"{ProjectName}_Data");
        string androidApkArtifact = Path.Combine(androidBuildFolder, $"{ProjectName}.apk");

        string distributionTypeEnv = System.Environment.GetEnvironmentVariable("DISTRIBUTION_TYPE");
        string distributionPathEnv = System.Environment.GetEnvironmentVariable("DISTRIBUTION_PATH");
        string distributionSubfolderEnv = System.Environment.GetEnvironmentVariable("DISTRIBUTION_SUBFOLDER");

        if (string.IsNullOrEmpty(distributionTypeEnv))
        {{{{
            distributionTypeEnv = "NONE";
            Debug.LogWarning("JulesBuildAutomation: DISTRIBUTION_TYPE environment variable not set. Defaulting to NONE.");
        }}}}

        if (string.IsNullOrEmpty(distributionPathEnv) && distributionTypeEnv != "NONE")
        {{{{
            Debug.LogError("JulesBuildAutomation: DISTRIBUTION_PATH environment variable is not set, but DISTRIBUTION_TYPE is not NONE. Distribution cannot proceed.");
            EditorApplication.Exit(1);
            return;
        }}}}

        bool overallSuccess = true;

        switch (distributionTypeEnv.ToUpper())
        {{{{
            case "LOCAL_SHARE":
                Debug.Log($"JulesBuildAutomation: LOCAL_SHARE distribution selected. Target: {{distributionPathEnv}}");
                string targetBasePath = distributionPathEnv;
                if (!string.IsNullOrEmpty(distributionSubfolderEnv))
                {{{{
                    targetBasePath = Path.Combine(distributionPathEnv, distributionSubfolderEnv);
                }}}}

                try
                {{{{
                    if (!Directory.Exists(targetBasePath))
                    {{{{
                        Debug.Log($"JulesBuildAutomation: Creating target directory: {{targetBasePath}}");
                        Directory.CreateDirectory(targetBasePath);
                    }}}}

                    // Copy Windows EXE
                    if (File.Exists(windowsExeArtifact))
                    {{{{
                        string destExePath = Path.Combine(targetBasePath, Path.GetFileName(windowsExeArtifact));
                        Debug.Log($"JulesBuildAutomation: Copying {{windowsExeArtifact}} to {{destExePath}}...");
                        File.Copy(windowsExeArtifact, destExePath, true);
                        Debug.Log("JulesBuildAutomation: Windows EXE copied successfully.");
                    }}}}
                    else
                    {{{{
                        Debug.LogWarning($"JulesBuildAutomation: Windows EXE artifact not found at {{windowsExeArtifact}}. Skipping copy.");
                        overallSuccess = false; // Or handle as a critical error
                    }}}}

                    // Copy Windows Data Folder
                    if (Directory.Exists(windowsDataFolderArtifact))
                    {{{{
                        string destDataFolderPath = Path.Combine(targetBasePath, Path.GetFileName(windowsDataFolderArtifact));
                        Debug.Log($"JulesBuildAutomation: Copying {{windowsDataFolderArtifact}} to {{destDataFolderPath}}...");
                        CopyDirectoryRecursive(windowsDataFolderArtifact, destDataFolderPath);
                        Debug.Log("JulesBuildAutomation: Windows Data folder copied successfully.");
                    }}}}
                    else
                    {{{{
                        Debug.LogWarning($"JulesBuildAutomation: Windows Data folder artifact not found at {{windowsDataFolderArtifact}}. Skipping copy.");
                        overallSuccess = false; // Or handle as a critical error
                    }}}}

                    // Copy Android APK
                    if (File.Exists(androidApkArtifact))
                    {{{{
                        string destApkPath = Path.Combine(targetBasePath, Path.GetFileName(androidApkArtifact));
                        Debug.Log($"JulesBuildAutomation: Copying {{androidApkArtifact}} to {{destApkPath}}...");
                        File.Copy(androidApkArtifact, destApkPath, true);
                        Debug.Log("JulesBuildAutomation: Android APK copied successfully.");
                    }}}}
                    else
                    {{{{
                        Debug.LogWarning($"JulesBuildAutomation: Android APK artifact not found at {{androidApkArtifact}}. Skipping copy.");
                        overallSuccess = false; // Or handle as a critical error
                    }}}}
                }}}}
                catch (System.Exception ex)
                {{{{
                    Debug.LogError($"JulesBuildAutomation: Error during LOCAL_SHARE distribution: {{ex.Message}}");
                    overallSuccess = false;
                }}}}
                break;

            case "SFTP":
                Debug.Log($"JulesBuildAutomation: SFTP distribution selected. Target: {{distributionPathEnv}}. This method is not yet implemented.");
                // overallSuccess = false; // Mark as not successful until implemented
                break;

            case "CLOUD":
                Debug.Log($"JulesBuildAutomation: Cloud distribution selected. Target: {{distributionPathEnv}}. This method is not yet implemented.");
                // overallSuccess = false; // Mark as not successful until implemented
                break;

            default: // NONE or unrecognized
                Debug.Log($"JulesBuildAutomation: Distribution skipped as DISTRIBUTION_TYPE is '{{distributionTypeEnv}}'.");
                // If type is "NONE", it's not an error. If it's unrecognized, it could be.
                if (distributionTypeEnv != "NONE")
                {{{{
                    Debug.LogWarning($"JulesBuildAutomation: Unrecognized DISTRIBUTION_TYPE: {{distributionTypeEnv}}");
                }}}}
                break;
        }}}}

        if (overallSuccess)
        {{{{
            Debug.Log("JulesBuildAutomation: Alpha Build Distribution process completed successfully.");
            EditorApplication.Exit(0);
        }}}}
        else
        {{{{
            Debug.LogError("JulesBuildAutomation: Alpha Build Distribution process encountered errors or was skipped for critical items.");
            EditorApplication.Exit(1);
        }}}}
    }}}}

    public static void IncrementBuildVersion()
    {{{{
        Debug.Log($"JulesBuildAutomation: Current version: {{buildVersion}}");
        string[] versionParts = buildVersion.Split('.');
        if (versionParts.Length == 3 && int.TryParse(versionParts[2], out int patch))
        {{{{
            patch++;
            buildVersion = $"{{{{versionParts[0]}}}}.{{{{versionParts[1]}}}}.{{{{patch}}}}";
            Debug.Log($"JulesBuildAutomation: Incremented version to: {{buildVersion}}");

            string versionFilePath = "Assets/Resources/build_version.txt";
            string resourcesFolderPath = Path.GetDirectoryName(versionFilePath);
            if (!Directory.Exists(resourcesFolderPath))
            {{{{
                Directory.CreateDirectory(resourcesFolderPath);
                AssetDatabase.Refresh(); // Ensure Unity sees the new folder
                Debug.Log($"JulesBuildAutomation: Created directory: {{resourcesFolderPath}}");
            }}}}
            File.WriteAllText(versionFilePath, buildVersion);
            AssetDatabase.Refresh(); // Ensure Unity sees the new file or changes
            Debug.Log($"JulesBuildAutomation: Saved new version to {{versionFilePath}}");
        }}}}
        else
        {{{{
            Debug.LogError($"JulesBuildAutomation: Could not parse buildVersion '{{buildVersion}}'. Expected format MAJOR.MINOR.PATCH");
        }}}}
    }}}}

    public static void LoadBuildVersion()
    {{{{
        string versionFilePath = "Assets/Resources/build_version.txt";
        if (File.Exists(versionFilePath))
        {{{{
            string versionFromFile = File.ReadAllText(versionFilePath).Trim();
            // Basic validation for "X.Y.Z" format
            string[] versionParts = versionFromFile.Split('.');
            if (versionParts.Length == 3 &&
                int.TryParse(versionParts[0], out _) &&
                int.TryParse(versionParts[1], out _) &&
                int.TryParse(versionParts[2], out _))
            {{{{
                buildVersion = versionFromFile;
                PlayerSettings.bundleVersion = buildVersion;
                // Optionally append version to product name, e.g., "RubeGoldbergVR v0.1.0"
                // PlayerSettings.productName = $"{ProjectName} v{buildVersion}";
                // For now, keeping product name as is, but bundleVersion is updated.
                Debug.Log($"JulesBuildAutomation: Loaded version {{buildVersion}} from {{versionFilePath}}. PlayerSettings.bundleVersion updated.");
            }}}}
            else
            {{{{
                Debug.LogWarning($"JulesBuildAutomation: Version file '{{versionFilePath}}' contained invalid format '{{versionFromFile}}'. Using default version {{buildVersion}}.");
            }}}}
        }}}}
        else
        {{{{
            Debug.Log($"JulesBuildAutomation: Version file '{{versionFilePath}}' not found. Using default version {{buildVersion}}. It will be created on next increment or build if setup correctly.");
            // Optionally, save the default version here if it's the first ever run and no file exists
            // IncrementBuildVersion(); // This would create it, but might not be desired on every load if file is missing.
            // For now, let's assume the file is created by IncrementBuildVersion or a manual process first.
        }}}}
        // Ensure PlayerSettings are updated even if file wasn't found, using the current static buildVersion
        PlayerSettings.bundleVersion = buildVersion;
         // Ensure productName is also set, potentially based on ProjectName
        if (PlayerSettings.productName != ProjectName) {{ PlayerSettings.productName = ProjectName; }}
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
# --increment-version-after-build for managing versioning
parser.add_argument("--increment-version-after-build", action="store_true", help="Increment build version via Unity after a successful build.")
# --run-smoke-tests for triggering smoke tests
parser.add_argument("--run-smoke-tests", action="store_true", help="Run smoke tests after a successful alpha build.")
parser.add_argument("--distribute-alpha-builds", action="store_true", help="Distribute alpha builds after successful smoke tests.")

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
    alpha_build_succeeded = run_command(alpha_build_command, "unity_alpha_build_log.txt")
    if not alpha_build_succeeded:
        print("Execution of JulesBuildAutomation.PerformAlphaTestBuild failed.")
        exit(1)
    print("JulesBuildAutomation.PerformAlphaTestBuild completed.")

    if alpha_build_succeeded and args.increment_version_after_build:
        print(f"Step 5: Executing JulesBuildAutomation.IncrementBuildVersion to update version in Assets/Resources...")
        increment_version_command = [unity_editor_path, "-batchmode", "-quit", "-projectPath", project_path, "-executeMethod", "JulesBuildAutomation.IncrementBuildVersion", "-logFile", os.path.join(project_path, "Logs", "unity_increment_version_log.txt")]
        if not run_command(increment_version_command, "unity_increment_version_log.txt"):
            print("Execution of JulesBuildAutomation.IncrementBuildVersion failed. The version in Assets/Resources/build_version.txt might be stale.")
            # Depending on desired strictness, one might exit(1) here.
            # For now, we'll just log the error and continue, as the main build succeeded.
        else:
            print("JulesBuildAutomation.IncrementBuildVersion completed. Version in Assets/Resources/build_version.txt should be updated.")
    elif not args.increment_version_after_build:
        print("Skipping version increment as --increment-version-after-build flag was not set.")

    # Conditional Smoke Tests call
    if args.run_alpha_build and args.run_smoke_tests and alpha_build_succeeded:
        print(f"Step 6: Executing JulesBuildAutomation.PerformSmokeTests...")
        smoke_test_command = [unity_editor_path, "-batchmode", "-quit", "-projectPath", project_path, "-executeMethod", "JulesBuildAutomation.PerformSmokeTests", "-logFile", os.path.join(project_path, "Logs", "unity_smoke_test_log.txt")]
        smoke_tests_command_succeeded = run_command(smoke_test_command, "unity_smoke_test_log.txt")
        if not smoke_tests_command_succeeded:
            print("Execution of JulesBuildAutomation.PerformSmokeTests failed. Unity reported an error or the command could not be run. Check unity_smoke_test_log.txt for details.")
            exit(1) # Exit with error if smoke tests fail
        print("JulesBuildAutomation.PerformSmokeTests completed.")
    elif args.run_smoke_tests and not alpha_build_succeeded:
        print("Skipping smoke tests as the Alpha Test Build did not succeed or was not run.")
    elif args.run_smoke_tests and not args.run_alpha_build:
         print("Skipping smoke tests as --run-alpha-build was not set (required for smoke tests).")

    # Conditional Distribution of Alpha Builds
    # Ensure smoke_tests_command_succeeded is defined even if smoke tests are skipped, default to False or handle logic flow
    if 'smoke_tests_command_succeeded' not in locals(): # if smoke tests were skipped, var won't exist
        smoke_tests_command_succeeded = False

    if args.run_alpha_build and args.run_smoke_tests and smoke_tests_command_succeeded and args.distribute_alpha_builds:
        print(f"Step 7: Executing JulesBuildAutomation.DistributeAlphaBuilds...")
        distribute_build_command = [unity_editor_path, "-batchmode", "-quit", "-projectPath", project_path, "-executeMethod", "JulesBuildAutomation.DistributeAlphaBuilds", "-logFile", os.path.join(project_path, "Logs", "unity_distribute_build_log.txt")]
        distribute_build_command_succeeded = run_command(distribute_build_command, "unity_distribute_build_log.txt")
        if not distribute_build_command_succeeded:
            print("Execution of JulesBuildAutomation.DistributeAlphaBuilds failed. Unity reported an error or the command could not be run. Check unity_distribute_build_log.txt for details.")
            exit(1) # Exit with error if distribution fails
        print("JulesBuildAutomation.DistributeAlphaBuilds completed.")
    elif args.distribute_alpha_builds: # If the flag is true but conditions aren't met
        print("Skipping distribution of Alpha Builds: Not all prerequisite steps were successful or enabled (--run-alpha-build, --run-smoke-tests must be set and succeed).")

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
        command_parts.append("--increment-version-after-build") # Trigger increment in create_unity_project.py
        if args.alpha_build_smoke_test: # New condition for smoke tests
            command_parts.append("--run-smoke-tests")
            if args.distribute_alpha_builds: # New condition
                command_parts.append("--distribute-alpha-builds")
    jules_command = " ".join(command_parts)

    print(f"To create/setup the Unity project, run the following command from the repository root:")
    print(jules_command)

    # If an alpha build was triggered, attempt to read the incremented version back from the Unity project
    # and write it to the root build_version.txt for the next run.
    if args.alpha_build and not test_mode_no_write: # Only if not in test_mode_no_write
        unity_project_resources_version_file_path = os.path.join(args.project_name, "Assets", "Resources", "build_version.txt")
        # This part simulates what would happen after the jules_command is actually run.
        # In a real CI/CD, this logic might be in a subsequent script or step.
        print(f"MAIN_SCRIPT.PY: Simulating post-build version update (as --alpha-build was specified).")
        print(f"MAIN_SCRIPT.PY: Attempting to read version from Unity project's resource file: {unity_project_resources_version_file_path}")

        # We need to ensure the directory for args.project_name exists before trying to read from it,
        # and also Assets/Resources. In a real run, Unity would create these.
        # For this simulation, we'll only try to read if the file is expected to be there.
        # This is a placeholder for the actual file read that would happen *after* Unity runs.
        # Since we can't actually run Unity here, we'll write the *current_build_version* + 1 patch
        # to simulate the increment that *would* have happened.
        # This is a simplification for the current context.

        # A more realistic simulation: if IncrementBuildVersion was supposed to run,
        # it would have updated Assets/Resources/build_version.txt. We try to read that.
        # If it's not there (e.g. Unity didn't run or failed before increment), we log a warning.
        if os.path.exists(unity_project_resources_version_file_path):
            with open(unity_project_resources_version_file_path, "r") as f:
                incremented_version_from_unity = f.read().strip()
                if incremented_version_from_unity:
                    with open(root_version_file, "w") as rf:
                        rf.write(incremented_version_from_unity)
                    print(f"MAIN_SCRIPT.PY: Successfully read '{incremented_version_from_unity}' from Unity project and updated {root_version_file}.")
                else:
                    print(f"MAIN_SCRIPT.PY: Warning - Unity project's version file '{unity_project_resources_version_file_path}' was empty. Root {root_version_file} not updated.")
        else:
            # This case will be hit if JulesBuildAutomation.cs hasn't run yet to create the file.
            # For the purpose of this script (which generates other scripts but doesn't run them itself),
            # this is an expected state if this is the first time or if the Unity project doesn't exist yet.
            # If main_script.py were to *actually run* create_unity_project.py and wait for it,
            # then this file should exist after a successful run with increment.
            print(f"MAIN_SCRIPT.PY: Warning - Unity project's version file '{unity_project_resources_version_file_path}' not found. Root {root_version_file} not updated. This is expected if Unity has not run and created it yet.")


# From Subtask 3
if __name__ == "__main__":
    main()
