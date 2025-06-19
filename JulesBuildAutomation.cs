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
using UnityEditor.Presets; // Needed for applying presets

public class JulesBuildAutomation
{
    private const string ProjectName = "RubeGoldbergVR";
    private static string unityEditorPath = "Unity"; // Assumes Unity is in PATH

    // Path to the Editor folder within Assets
    private static string editorFolderPath = "Assets/Editor";
    // Path to this script within the Editor folder
    private static string buildScriptPath = Path.Combine(editorFolderPath, "JulesBuildAutomation.cs");

    // List of XR packages to ensure are installed for VR functionality
    private static List<string> xrPackages = new List<string>
    {
        "com.unity.xr.interaction.toolkit@2.3.1", // Specify version or leave blank for latest compatible
        "com.unity.xr.openxr@1.9.0" // Specify version or leave blank for latest compatible
    };

    // --- Entry points for Jules (via -executeMethod) ---

    // This method will be called by Jules to initialize the project for VR development.
    // It will install necessary XR packages and configure XR settings.
    [MenuItem("Jules/SetupVRProject")]
    public static void SetupVRProject()
    {
        Debug.Log("Jules: Starting VR Project Setup...");
        EnsureEditorFolderExists();
        InstallXRPackages();
    }

    // This method will be called by Jules to perform a dummy build for command-line testing.
    // It will be a minimal build to confirm the pipeline works.
    [MenuItem("Jules/PerformAlphaTestBuild")]
    public static void PerformAlphaTestBuild()
    {
        Debug.Log("Jules: Starting Alpha Test Build...");

        // Ensure a scene exists to build
        string sampleScenePath = "Assets/Scenes/SampleScene.unity";
        if (!File.Exists(sampleScenePath))
        {
            Debug.LogError($"Jules: Scene '{sampleScenePath}' not found for build. Please ensure it exists.");
            EditorApplication.Exit(1);
            return;
        }

        BuildPlayerOptions buildOptions = new BuildPlayerOptions();
        buildOptions.scenes = new[] { sampleScenePath };

        // Define build paths for Windows and Android
        string windowsBuildPath = $"Builds/AlphaTest/Windows/{ProjectName}.exe";
        string androidBuildPath = $"Builds/AlphaTest/Android/{ProjectName}.apk";

        // Create directories if they don't exist
        Directory.CreateDirectory(Path.GetDirectoryName(windowsBuildPath));
        Directory.CreateDirectory(Path.GetDirectoryName(androidBuildPath));

        // --- Build for Windows Standalone ---
        Debug.Log("Jules: Building for Windows Standalone (Alpha Test)...");
        buildOptions.locationPathName = windowsBuildPath;
        buildOptions.target = BuildTarget.StandaloneWindows64;
        buildOptions.options = BuildOptions.None; // Add BuildOptions.Development for debug builds

        BuildReport reportWindows = BuildPipeline.BuildPlayer(buildOptions);
        BuildSummary summaryWindows = reportWindows.summary;

        if (summaryWindows.result == BuildResult.Succeeded)
        {
            Debug.Log($"Jules: Windows Alpha Test Build succeeded: {summaryWindows.totalSize} bytes at {windowsBuildPath}");
        }
        else if (summaryWindows.result == BuildResult.Failed)
        {
            Debug.LogError($"Jules: Windows Alpha Test Build failed: {summaryWindows.totalErrors} errors");
            EditorApplication.Exit(1); // Exit with error if Windows build fails
            return;
        }

        // --- Build for Android (for Quest/VR) ---
        Debug.Log("Jules: Building for Android (Alpha Test for Quest/VR)...");
        buildOptions.locationPathName = androidBuildPath;
        buildOptions.target = BuildTarget.Android;
        buildOptions.options = BuildOptions.None; // Add BuildOptions.Development for debug builds

        // Ensure Android build target is set up with necessary modules in Unity Hub
        if (!EditorUserBuildSettings.activeBuildTarget.Equals(BuildTarget.Android))
        {
            Debug.Log("Jules: Switching active build target to Android for build...");
            EditorUserBuildSettings.SwitchActiveBuildTarget(BuildTargetGroup.Android, BuildTarget.Android);
        }

        BuildReport reportAndroid = BuildPipeline.BuildPlayer(buildOptions);
        BuildSummary summaryAndroid = reportAndroid.summary;

        if (summaryAndroid.result == BuildResult.Succeeded)
        {
            Debug.Log($"Jules: Android Alpha Test Build succeeded: {summaryAndroid.totalSize} bytes at {androidBuildPath}");
        }
        else if (summaryAndroid.result == BuildResult.Failed)
        {
            Debug.LogError($"Jules: Android Alpha Test Build failed: {summaryAndroid.totalErrors} errors");
            EditorApplication.Exit(1); // Exit with error if Android build fails
            return;
        }

        Debug.Log("Jules: All Alpha Test Builds completed successfully.");
        EditorApplication.Exit(0); // Overall success
    }

    // --- Internal Helper Methods ---

    private static void EnsureEditorFolderExists()
    {
        if (!AssetDatabase.IsValidFolder(editorFolderPath))
        {
            AssetDatabase.CreateFolder("Assets", "Editor");
            Debug.Log($"Jules: Created folder: {editorFolderPath}");
        }
    }

    private static void InstallXRPackages()
    {
        packageIndex = 0;
        EditorApplication.update += ProcessPackageInstallationQueue;
    }

    private static AddRequest currentAddRequest;
    private static int packageIndex = 0;

    private static void ProcessPackageInstallationQueue()
    {
        if (currentAddRequest != null && !currentAddRequest.IsCompleted)
        {
            return; // Wait for current request to complete
        }

        if (packageIndex < xrPackages.Count)
        {
            string packageId = xrPackages[packageIndex];
            Debug.Log($"Jules: Attempting to install package: {packageId}");
            currentAddRequest = Client.Add(packageId);
            packageIndex++;
        }
        else
        {
            EditorApplication.update -= ProcessPackageInstallationQueue;
            Debug.Log("Jules: All XR packages installation requests sent. Now configuring XR Plug-in Management and OpenXR. Please wait for assembly compilation.");
            EditorApplication.delayCall += ConfigureXRSettings; // Delay to allow packages to process internally
        }
    }

    private static void ConfigureXRSettings()
    {
        Debug.Log("Jules: Starting XR configuration...");

        // Get the XR General Settings for Standalone (PC) and Android (Quest)
        ConfigureBuildTargetXRSettings(BuildTargetGroup.Standalone, BuildTarget.StandaloneWindows64, "Windows, Mac & Linux");
        ConfigureBuildTargetXRSettings(BuildTargetGroup.Android, BuildTarget.Android, "Android");

        AssetDatabase.SaveAssets();
        AssetDatabase.Refresh();

        Debug.Log("Jules: XR configuration complete. Project ready for VR development.");

        CreateBasicVRSceneElements();
        // Do not exit here, let PerformAlphaTestBuild handle the exit
    }

    private static void ConfigureBuildTargetXRSettings(BuildTargetGroup buildTargetGroup, BuildTarget buildTarget, string tabName)
    {
        Debug.Log($"Jules: Configuring XR for {tabName}...");

        XRGeneralSettingsForEditor generalSettings = null;
        // Corrected: Use TryGetConfigObject to get existing settings or allow creation if null
        EditorBuildSettings.TryGetConfigObject(XRGeneralSettingsForEditor.k_SettingsKey, out generalSettings);
        if (generalSettings == null)
        {
            // This creates a general settings asset if one doesn't exist.
            // And then assigns it to the build target group.
            generalSettings = ScriptableObject.CreateInstance<XRGeneralSettingsForEditor>();
            // The SetBuildTargetSettings is key to actually saving/assigning this new settings object
            XRGeneralSettingsForEditor.SetBuildTargetSettings(buildTargetGroup, generalSettings);
            Debug.Log($"Jules: Created new XRGeneralSettingsForEditor for {tabName} and assigned it.");
        } else {
            Debug.Log($"Jules: Found existing XRGeneralSettingsForEditor for {tabName}.");
        }

        // Ensure XR Plug-in Management is configured for this build target group
        Debug.Log($"Jules: Ensuring XR Plug-in Management is configured for {tabName}.");

        // Temporarily switch active build target group to ensure settings are applied correctly for that group
        var previousBuildTargetGroup = EditorUserBuildSettings.selectedBuildTargetGroup;
        var previousBuildTarget = EditorUserBuildSettings.activeBuildTarget;

        if (EditorUserBuildSettings.selectedBuildTargetGroup != buildTargetGroup) {
            EditorUserBuildSettings.SwitchActiveBuildTarget(buildTargetGroup, buildTarget);
            Debug.Log($"Jules: Switched active build target group to {buildTargetGroup} for configuration.");
        }

        // Get the manager settings for the specific build target group
        var managerSettings = generalSettings.Manager; // This should give the XRManagerSettings for the current group context
        if(managerSettings == null && generalSettings != null) {
            // This case should ideally not happen if generalSettings is valid and correctly linked.
            // If generalSettings.Manager is null, it might imply an issue with the XRGeneralSettingsForEditor asset itself
            // or how it's being initialized or retrieved.
            // For robustness, one might try to re-fetch or ensure the sub-asset (Manager) is there.
            // However, standard Unity practice expects generalSettings.Manager to be valid if generalSettings itself is.
            Debug.LogWarning($"Jules: XRManagerSettings (generalSettings.Manager) is null for {tabName}, attempting to re-verify settings structure.");
            // Potentially re-assign or create the manager part if necessary, though this is deep Unity internal behavior.
            // For now, we proceed assuming managerSettings will be available if generalSettings is.
        }


        // Add OpenXR Loader if not already present
        // Ensure we have a valid list to work with, even if it's empty
        var activeLoadersList = managerSettings.activeLoaders != null ? managerSettings.activeLoaders.ToList() : new List<XRLoader>();

        if (!activeLoadersList.Any(loader => loader is OpenXRLoader))
        {
            var openXRLoader = ScriptableObject.CreateInstance<OpenXRLoader>();
            activeLoadersList.Add(openXRLoader);
            managerSettings.activeLoaders = activeLoadersList; // Update the list of active loaders
            Debug.Log($"Jules: Added OpenXR Loader to {tabName} XR General Settings.");
            EditorUtility.SetDirty(generalSettings); // Mark the main settings object as dirty
            EditorUtility.SetDirty(managerSettings); // Also mark manager settings as dirty
        } else {
            Debug.Log($"Jules: OpenXR Loader already present for {tabName}.");
        }

        // Configure OpenXR settings (e.g., add interaction profiles)
        OpenXRSettings openXRSettings = OpenXRSettings.GetForBuildTargetGroup(buildTargetGroup);
        if (openXRSettings != null)
        {
            Debug.Log($"Jules: Configuring {tabName} OpenXR settings...");
            AddOpenXRInteractionProfile(openXRSettings, "Unity.XR.OpenXR.Features.OculusQuestSupport.OculusQuestFeature");
            AddOpenXRInteractionProfile(openXRSettings, "Unity.XR.OpenXR.Features.HPReverbG2ControllerProfile");
            EditorUtility.SetDirty(openXRSettings);
        }
        else
        {
            Debug.LogWarning($"Jules: OpenXRSettings not found for {tabName}. This might indicate the OpenXR package isn't fully installed/configured or the settings object is missing.");
            // Attempt to create OpenXRSettings if missing
            var featureSet = OpenXRFeatureSetManager.GetFeatureSetWithId(buildTargetGroup, "com.unity.xr.openxr.featureset.oculus"); // Example feature set
            if (featureSet != null) {
                featureSet.isEnabled = true;
                OpenXRFeatureSetManager.SetFeaturesEnabled(buildTargetGroup, featureSet.featureSetId, true);
                Debug.Log($"Jules: Attempted to enable OpenXR feature set for {tabName}. Please re-check OpenXR settings.");
                // Re-try getting settings after enabling a feature set
                openXRSettings = OpenXRSettings.GetForBuildTargetGroup(buildTargetGroup);
                if(openXRSettings != null) {
                    Debug.Log($"Jules: OpenXRSettings found after enabling feature set for {tabName}.");
                    EditorUtility.SetDirty(openXRSettings);
                } else {
                     Debug.LogWarning($"Jules: Still could not find OpenXRSettings for {tabName} after attempting to enable a feature set.");
                }
            }
        }

        // Restore previous build target if changed
        if (EditorUserBuildSettings.selectedBuildTargetGroup != previousBuildTargetGroup) {
            EditorUserBuildSettings.SwitchActiveBuildTarget(previousBuildTargetGroup, previousBuildTarget);
            Debug.Log($"Jules: Restored active build target group to {previousBuildTargetGroup}.");
        }
        AssetDatabase.SaveAssets(); // Save changes to assets
    }

    private static void AddOpenXRInteractionProfile(OpenXRSettings settings, string profileTypeIdName)
    {
        if (settings == null) {
            Debug.LogWarning($"Jules: OpenXRSettings are null, cannot add interaction profile: {profileTypeIdName}");
            return;
        }

        var availableFeatures = OpenXRSettings.GetAllFeatures(settings.buildTargetGroup);
        var featureToEnable = availableFeatures.FirstOrDefault(f => f.GetType().FullName == profileTypeIdName);

        if (featureToEnable != null)
        {
            if (!featureToEnable.enabled)
            {
                featureToEnable.enabled = true;
                Debug.Log($"Jules: Enabled OpenXR feature: {featureToEnable.name} ({profileTypeIdName}) for {settings.buildTargetGroup}.");
                EditorUtility.SetDirty(settings); // Mark settings dirty as a feature has changed
            }
            else
            {
                Debug.Log($"Jules: OpenXR feature '{profileTypeIdName}' already enabled for {settings.buildTargetGroup}.");
            }
        }
        else
        {
            Debug.LogWarning($"Jules: OpenXR feature type '{profileTypeIdName}' not found for {settings.buildTargetGroup}. It might not be installed or the type name is incorrect.");
        }
    }

    private static void CreateBasicVRSceneElements()
    {
        Debug.Log("Jules: Creating basic VR scene elements...");

        string sampleScenePath = "Assets/Scenes/SampleScene.unity";
        if (!Directory.Exists("Assets/Scenes"))
        {
            AssetDatabase.CreateFolder("Assets", "Scenes");
        }

        Scene activeScene;
        if (!File.Exists(sampleScenePath))
        {
            activeScene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            EditorSceneManager.SaveScene(activeScene, sampleScenePath);
            Debug.Log($"Jules: Created new scene at: {sampleScenePath}");
        }
        else
        {
            activeScene = EditorSceneManager.OpenScene(sampleScenePath);
            Debug.Log($"Jules: Opened existing scene at: {sampleScenePath}");
        }

        // Remove existing Main Camera if present
        GameObject mainCamera = GameObject.FindWithTag("MainCamera");
        if (mainCamera != null && mainCamera.GetComponent<Camera>() != null && mainCamera.GetComponent<Camera>().CompareTag("MainCamera"))
        {
            Debug.Log("Jules: Found and removing default Main Camera.");
            Object.DestroyImmediate(mainCamera);
        }

        // Add XR Origin (VR)
        GameObject xrOriginGO = new GameObject("XR Origin");
        var xrOrigin = xrOriginGO.AddComponent<XROrigin>();

        GameObject vrCameraGO = new GameObject("Main Camera");
        vrCameraGO.transform.SetParent(xrOrigin.transform);
        Camera vrCamera = vrCameraGO.AddComponent<Camera>();
        vrCamera.tag = "MainCamera";
        // For XROrigin from XR Interaction Toolkit 2.0.0+, assign Camera property
        xrOrigin.Camera = vrCamera;
        // xrOrigin.CameraFloorOffsetObject = xrOriginGO; // If you want floor offset to be the origin itself

        Debug.Log("Jules: Added XR Origin with Main Camera.");

        if (Object.FindObjectOfType<UnityEngine.XR.Interaction.Toolkit.XRInteractionManager>() == null)
        {
            GameObject interactionManager = new GameObject("XR Interaction Manager");
            interactionManager.AddComponent<UnityEngine.XR.Interaction.Toolkit.XRInteractionManager>();
            Debug.Log("Jules: Added XR Interaction Manager.");
        }

        AddXRController(xrOrigin.transform, "Left Hand Controller", true);
        AddXRController(xrOrigin.transform, "Right Hand Controller", false);

        GameObject floor = GameObject.CreatePrimitive(PrimitiveType.Plane);
        floor.name = "Ground Plane";
        floor.transform.position = new Vector3(0, 0, 0); // Origin, XR Origin will handle height
        floor.transform.localScale = new Vector3(10, 1, 10);

        Renderer floorRenderer = floor.GetComponent<Renderer>();
        if (floorRenderer != null)
        {
            floorRenderer.sharedMaterial = new Material(Shader.Find("Standard"));
            floorRenderer.sharedMaterial.color = Color.gray;
        }
        Debug.Log("Jules: Added Ground Plane.");

        EditorSceneManager.SaveScene(activeScene);
        AssetDatabase.SaveAssets();
        AssetDatabase.Refresh();
        Debug.Log("Jules: Basic VR scene elements created and scene saved.");
    }

    private static void AddXRController(Transform parent, string name, bool isLeftHand)
    {
        GameObject controllerGO = new GameObject(name);
        controllerGO.transform.SetParent(parent);

        var controller = controllerGO.AddComponent<UnityEngine.XR.Interaction.Toolkit.XRController>();
        controller.controllerNode = isLeftHand ? UnityEngine.XR.XRNode.LeftHand : UnityEngine.XR.XRNode.RightHand;

        if (isLeftHand)
        {
            controllerGO.AddComponent<UnityEngine.XR.Interaction.Toolkit.XRRayInteractor>();
            // Optionally add Line Renderer for the ray
            // var lineRenderer = controllerGO.AddComponent<LineRenderer>();
            // Configure lineRenderer (material, width, colors, etc.)
            // controllerGO.AddComponent<UnityEngine.XR.Interaction.Toolkit.XRInteractorLineVisual>();
            Debug.Log($"Jules: Added {name} with XRRayInteractor.");
        }
        else
        {
            controllerGO.AddComponent<UnityEngine.XR.Interaction.Toolkit.XRDirectInteractor>();
            Debug.Log($"Jules: Added {name} with XRDirectInteractor.");
        }

        GameObject visualizer = GameObject.CreatePrimitive(PrimitiveType.Sphere);
        visualizer.name = "Controller Visual";
        visualizer.transform.SetParent(controllerGO.transform);
        visualizer.transform.localScale = new Vector3(0.1f, 0.1f, 0.1f);
        visualizer.transform.localPosition = Vector3.zero;
        Object.DestroyImmediate(visualizer.GetComponent<Collider>());
        Renderer visualizerRenderer = visualizer.GetComponent<Renderer>();
        if (visualizerRenderer != null)
        {
            visualizerRenderer.sharedMaterial = new Material(Shader.Find("Standard"));
            visualizerRenderer.sharedMaterial.color = isLeftHand ? Color.blue : Color.red;
        }
    }

    // Helper to get XR General Settings for a specific build target group - This seems unused in the latest script logic
    // private static XRGeneralSettingsForEditor GetBuildTargetSettings(BuildTargetGroup buildTargetGroup)
    // {
    //     XRGeneralSettingsForEditor generalSettings = null;
    //     EditorBuildSettings.TryGetConfigObject(XRGeneralSettingsForEditor.k_SettingsKey, out generalSettings);
    //     return generalSettings;
    // }
}
