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
using UnityEngine.SceneManagement; // Added for SceneManager

public class JulesBuildAutomation
{
    private const string ProjectName = "RubeGoldbergVR";
    private static List<string> xrPackages = new List<string>
    {
        "com.unity.xr.interaction.toolkit@2.3.1",
        "com.unity.xr.openxr@1.9.0"
    };

    private static AddRequest currentAddRequest;
    private static int packageIndex = 0;

    [MenuItem("Jules/SetupVRProject")]
    public static void SetupVRProject()
    {
        Debug.Log("Jules: Starting VR Project Setup...");
        EnsureEditorFolderExists();
        InstallXRPackages();
    }

    [MenuItem("Jules/PerformAlphaTestBuild")]
    public static void PerformAlphaTestBuild()
    {
        Debug.Log("Jules: Starting Alpha Test Build...");

        string sampleScenePath = "Assets/Scenes/SampleScene.unity";
        if (!File.Exists(sampleScenePath))
        {
            Debug.LogError($"Jules: Scene '{sampleScenePath}' not found for build. Please ensure it exists.");
            EditorApplication.Exit(1);
            return;
        }

        BuildPlayerOptions buildOptions = new BuildPlayerOptions();
        buildOptions.scenes = new[] { sampleScenePath };

        string windowsBuildPath = $"Builds/AlphaTest/Windows/{ProjectName}.exe";
        string androidBuildPath = $"Builds/AlphaTest/Android/{ProjectName}.apk";

        Directory.CreateDirectory(Path.GetDirectoryName(windowsBuildPath));
        Directory.CreateDirectory(Path.GetDirectoryName(androidBuildPath));

        Debug.Log("Jules: Building for Windows Standalone (Alpha Test)...");
        buildOptions.locationPathName = windowsBuildPath;
        buildOptions.target = BuildTarget.StandaloneWindows64;
        buildOptions.options = BuildOptions.None;

        BuildReport reportWindows = BuildPipeline.BuildPlayer(buildOptions);
        BuildSummary summaryWindows = reportWindows.summary;

        if (summaryWindows.result == BuildResult.Succeeded)
        {
            Debug.Log($"Jules: Windows Alpha Test Build succeeded: {summaryWindows.totalSize} bytes at {windowsBuildPath}");
        }
        else if (summaryWindows.result == BuildResult.Failed)
        {
            Debug.LogError($"Jules: Windows Alpha Test Build failed: {summaryWindows.totalErrors} errors");
            EditorApplication.Exit(1);
            return;
        }

        Debug.Log("Jules: Building for Android (Alpha Test for Quest/VR)...");
        buildOptions.locationPathName = androidBuildPath;
        buildOptions.target = BuildTarget.Android;
        buildOptions.options = BuildOptions.None;

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
            EditorApplication.Exit(1);
            return;
        }

        Debug.Log("Jules: All Alpha Test Builds completed successfully.");
        EditorApplication.Exit(0);
    }

    [MenuItem("Jules/SetupRubeGoldbergGame")]
    public static void SetupRubeGoldbergGame()
    {
        Debug.Log("Jules: Starting Rube Goldberg Game Setup...");
        CreateBasicVRSceneElements();
        AddInteractablePhysicsObjects();
        CreateRubeGoldbergPrefabs();
        EditorApplication.Exit(0);
    }


    private static void EnsureEditorFolderExists()
    {
        if (!AssetDatabase.IsValidFolder("Assets/Editor"))
        {
            AssetDatabase.CreateFolder("Assets", "Editor");
            Debug.Log("Jules: Created folder: Assets/Editor");
        }
    }

    private static void InstallXRPackages()
    {
        packageIndex = 0;
        EditorApplication.update += ProcessPackageInstallationQueue;
    }

    private static void ProcessPackageInstallationQueue()
    {
        if (currentAddRequest != null && !currentAddRequest.IsCompleted)
        {
            return;
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
            EditorApplication.delayCall += ConfigureXRSettings;
        }
    }

    private static void ConfigureXRSettings()
    {
        Debug.Log("Jules: Starting XR configuration...");

        ConfigureBuildTargetXRSettings(BuildTargetGroup.Standalone, BuildTarget.StandaloneWindows64, "Windows, Mac & Linux");
        ConfigureBuildTargetXRSettings(BuildTargetGroup.Android, BuildTarget.Android, "Android");

        AssetDatabase.SaveAssets();
        AssetDatabase.Refresh();

        Debug.Log("Jules: XR configuration complete. Project ready for VR development.");

        EditorApplication.delayCall += SetupRubeGoldbergGame;
    }

    private static void ConfigureBuildTargetXRSettings(BuildTargetGroup buildTargetGroup, BuildTarget buildTarget, string tabName)
    {
        Debug.Log($"Jules: Configuring XR for {tabName}...");

        XRGeneralSettingsForEditor generalSettings;
        string settingsKey = XRGeneralSettingsForEditor.k_SettingsKey;

        // Try to get existing settings or create new ones.
        if (!EditorBuildSettings.TryGetConfigObject(settingsKey, out generalSettings))
        {
            generalSettings = ScriptableObject.CreateInstance<XRGeneralSettingsForEditor>();
            EditorBuildSettings.AddConfigObject(settingsKey, generalSettings, true); // true to make it visible in Project Settings
            Debug.Log($"Jules: Created new XRGeneralSettingsForEditor for {tabName}.");
        }

        // Assign the settings to the target build group.
        XRGeneralSettingsForEditor.SetBuildTargetSettings(buildTargetGroup, generalSettings);

        // Switch active build target before changing XRManagerSettings to avoid issues.
        if (EditorUserBuildSettings.activeBuildTargetGroup != buildTargetGroup || EditorUserBuildSettings.activeBuildTarget != buildTarget)
        {
            EditorUserBuildSettings.SwitchActiveBuildTarget(buildTargetGroup, buildTarget);
        }

        // Ensure XRManagerSettings exists.
        if (generalSettings.Manager == null)
        {
            generalSettings.Manager = ScriptableObject.CreateInstance<XRManagerSettings>();
            EditorUtility.SetDirty(generalSettings); // Mark generalSettings as dirty to save this change.
            AssetDatabase.SaveAssets(); // Save the change to generalSettings.
            Debug.Log($"Jules: Created new XRManagerSettings for {tabName}.");
        }

        var currentLoaders = generalSettings.Manager.loaders; // This should now be a new list if Manager was just created.
        bool openXRLoaderFound = false;
        OpenXRLoader openXRLoaderInstance = null;

        // Check if OpenXR Loader is already in the list.
        foreach (var loader in currentLoaders)
        {
            if (loader is OpenXRLoader oxrLoader)
            {
                openXRLoaderFound = true;
                openXRLoaderInstance = oxrLoader;
                break;
            }
        }

        if (!openXRLoaderFound)
        {
            openXRLoaderInstance = ScriptableObject.CreateInstance<OpenXRLoader>();
            // Add the loader to the list of loaders in XRManagerSettings.
            // The list of loaders might be empty if XRManagerSettings was just created.
            // We need to ensure we are adding to the list associated with generalSettings.Manager.
            generalSettings.Manager.loaders.Add(openXRLoaderInstance);
            EditorUtility.SetDirty(generalSettings.Manager); // Mark Manager as dirty
            Debug.Log($"Jules: Added OpenXR Loader to {tabName} XR General Settings.");
        }

        // Ensure the loader is active.
        if (openXRLoaderInstance != null && !generalSettings.Manager.activeLoaders.Contains(openXRLoaderInstance))
        {
            generalSettings.Manager.activeLoaders.Add(openXRLoaderInstance);
            EditorUtility.SetDirty(generalSettings.Manager);
            Debug.Log($"Jules: Activated OpenXR Loader for {tabName}.");
        }


        // Configure OpenXR specific settings (like interaction profiles).
        OpenXRSettings openXRSettings = OpenXRSettings.GetForBuildTargetGroup(buildTargetGroup);
        if (openXRSettings != null)
        {
            Debug.Log($"Jules: Configuring {tabName} OpenXR settings...");

            // Example: Add Oculus Touch Controller Profile and Meta Quest Support Feature
            AddOpenXRInteractionProfile(openXRSettings, "com.unity.openxr.features.oculustouchcontroller");
            AddOpenXRInteractionProfile(openXRSettings, "com.unity.openxr.features.metarequestsupport");
            AddOpenXRInteractionProfile(openXRSettings, "com.unity.openxr.features.hp_reverb_g2_controller");

            EditorUtility.SetDirty(openXRSettings); // Mark OpenXRSettings as dirty
        }
        else
        {
            Debug.LogWarning($"Jules: OpenXRSettings not found for {tabName}. This might indicate a problem with package installation or XR management setup. Attempting to create one.");
            // This case should ideally not happen if OpenXR package is correctly installed and loaded.
            // If it does, creating one might be complex or might not integrate correctly without proper initialization.
            // For now, we'll just log the warning. A more robust solution might involve re-checking package installation.
        }

        EditorUtility.SetDirty(generalSettings); // Mark general settings as dirty to ensure all changes are saved.
        AssetDatabase.SaveAssets(); // Save all changes to disk.
        AssetDatabase.Refresh();    // Refresh asset database to reflect changes.
    }

    private static void AddOpenXRInteractionProfile(OpenXRSettings settings, string featureId)
    {
        // Iterate through all available features for the build target group.
        foreach (var feature in OpenXRSettings.GetAllFeatures(settings.buildTargetGroup))
        {
            if (feature.featureId == featureId)
            {
                if (!feature.enabled)
                {
                    feature.enabled = true;
                    Debug.Log($"Jules: Enabled OpenXR feature: {feature.name} (ID: {feature.featureId}) for {settings.buildTargetGroup}.");
                } else {
                    Debug.Log($"Jules: OpenXR feature: {feature.name} (ID: {feature.featureId}) already enabled for {settings.buildTargetGroup}.");
                }
                return; // Feature found and processed.
            }
        }
        // If the loop completes, the feature was not found.
        Debug.LogWarning($"Jules: OpenXR feature with ID '{featureId}' not found for {settings.buildTargetGroup}. Ensure the relevant package/feature set is installed.");
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
        // Check if the scene file exists. If not, create a new one.
        if (!File.Exists(sampleScenePath))
        {
            activeScene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            EditorSceneManager.SaveScene(activeScene, sampleScenePath); // Save the new scene
            Debug.Log($"Jules: Created new scene at: {sampleScenePath}");
        }
        else
        {
            activeScene = EditorSceneManager.OpenScene(sampleScenePath); // Open existing scene
            Debug.Log($"Jules: Opened existing scene at: {sampleScenePath}");
        }

        // Remove default main camera if it exists
        GameObject mainCamera = GameObject.FindWithTag("MainCamera");
        if (mainCamera != null && mainCamera.GetComponent<Camera>() != null && mainCamera.GetComponent<Camera>().CompareTag("MainCamera"))
        {
            Debug.Log("Jules: Found and removing default Main Camera.");
            Object.DestroyImmediate(mainCamera);
        }

        // Create XR Origin (Rig)
        GameObject xrOriginGO = new GameObject("XR Origin");
        var xrOrigin = xrOriginGO.AddComponent<XROrigin>(); // Use XROrigin from CoreUtils

        // Create Camera for XR Origin
        GameObject vrCameraGO = new GameObject("Main Camera"); // This will be the VR camera
        vrCameraGO.transform.SetParent(xrOrigin.transform); // Parent to XR Origin
        Camera vrCamera = vrCameraGO.AddComponent<Camera>();
        vrCamera.tag = "MainCamera"; // Ensure it's tagged as MainCamera
        xrOrigin.Camera = vrCamera; // Assign VR Camera to XROrigin's Camera property

        // Set Camera GameObject for XROrigin's CameraFloorOffsetObject
        // This ensures the camera's height is correctly offset from the floor.
        // In recent XR Interaction Toolkit versions, this is automatically handled or configured differently.
        // For XROrigin, we need to ensure CameraYOffset is applied correctly.
        // xrOrigin.CameraYOffset = 1.8f; // Example height, adjust as needed or use device-reported height.
        // For XROrigin, it's more about setting the TrackingOriginMode.
        xrOrigin.RequestedTrackingOriginMode = XROrigin.TrackingOriginMode.Floor;


        // Ensure XR Interaction Manager exists
        if (Object.FindObjectOfType<UnityEngine.XR.Interaction.Toolkit.XRInteractionManager>() == null)
        {
            GameObject interactionManager = new GameObject("XR Interaction Manager");
            interactionManager.AddComponent<UnityEngine.XR.Interaction.Toolkit.XRInteractionManager>();
            Debug.Log("Jules: Added XR Interaction Manager.");
        }

        // Add Left and Right Hand Controllers
        AddXRController(xrOrigin.transform, "Left Hand Controller", true);
        AddXRController(xrOrigin.transform, "Right Hand Controller", false);

        // Create a simple floor
        GameObject floor = GameObject.CreatePrimitive(PrimitiveType.Plane);
        floor.name = "Ground Plane";
        floor.transform.position = new Vector3(0, -0.05f, 0); // Slightly below origin to avoid Z-fighting with objects at y=0
        floor.transform.localScale = new Vector3(10, 1, 10); // Make it reasonably large

        // Add a material to the floor for better visibility
        Renderer floorRenderer = floor.GetComponent<Renderer>();
        if (floorRenderer != null)
        {
            // Create a new default material (Standard Shader)
            Material defaultMaterial = new Material(Shader.Find("Standard"));
            defaultMaterial.color = Color.gray; // Set color to gray
            floorRenderer.sharedMaterial = defaultMaterial;
        }

        // Save changes to the scene
        EditorSceneManager.SaveScene(activeScene);
        AssetDatabase.SaveAssets(); // Save all asset changes
        AssetDatabase.Refresh();    // Refresh Asset Database
        Debug.Log("Jules: Basic VR scene elements created and scene saved.");
    }

    private static void AddXRController(Transform parent, string name, bool isLeftHand)
    {
        GameObject controllerGO = new GameObject(name);
        controllerGO.transform.SetParent(parent); // Parent to XR Origin

        // Add XRController component
        var controller = controllerGO.AddComponent<UnityEngine.XR.Interaction.Toolkit.XRController>();
        controller.controllerNode = isLeftHand ? UnityEngine.XR.XRNode.LeftHand : UnityEngine.XR.XRNode.RightHand;

        // Add Interactor based on hand
        if (isLeftHand)
        {
            // Left hand typically uses Ray Interactor for UI and distant interactions
            controllerGO.AddComponent<UnityEngine.XR.Interaction.Toolkit.XRRayInteractor>();
            // Optionally, add a line visual for the ray
            // controllerGO.AddComponent<UnityEngine.XR.Interaction.Toolkit.XRInteractorLineVisual>();
            Debug.Log($"Jules: Added {name} with XRRayInteractor.");
        }
        else
        {
            // Right hand often uses Direct Interactor for grabbing nearby objects
            controllerGO.AddComponent<UnityEngine.XR.Interaction.Toolkit.XRDirectInteractor>();
            Debug.Log($"Jules: Added {name} with XRDirectInteractor.");
        }

        // Add a simple visual representation for the controller (optional)
        GameObject visualizer = GameObject.CreatePrimitive(PrimitiveType.Sphere);
        visualizer.name = "Controller Visual";
        visualizer.transform.SetParent(controllerGO.transform);
        visualizer.transform.localScale = new Vector3(0.1f, 0.1f, 0.1f); // Small sphere
        visualizer.transform.localPosition = Vector3.zero; // At controller's origin
        Object.DestroyImmediate(visualizer.GetComponent<Collider>()); // Remove collider from visual
        // Add material to visualizer
        Renderer visualizerRenderer = visualizer.GetComponent<Renderer>();
        if (visualizerRenderer != null)
        {
            Material controllerMaterial = new Material(Shader.Find("Standard"));
            controllerMaterial.color = isLeftHand ? Color.blue : Color.red;
            visualizerRenderer.sharedMaterial = controllerMaterial;
        }
    }

    // Helper method to add Rigidbody and XRGrabInteractable to an object
    private static void AddPhysicsAndInteraction(GameObject obj)
    {
        // Add Rigidbody if not present
        if (obj.GetComponent<Rigidbody>() == null)
        {
            Rigidbody rb = obj.AddComponent<Rigidbody>();
            rb.mass = 1.0f; // Default mass
            // rb.collisionDetectionMode = CollisionDetectionMode.ContinuousSpeculative; // Good for performance & reliability
            Debug.Log($"Jules: Added Rigidbody to {obj.name}.");
        }

        // Add XRGrabInteractable if not present
        if (obj.GetComponent<XRGrabInteractable>() == null)
        {
            obj.AddComponent<XRGrabInteractable>();
            Debug.Log($"Jules: Added XRGrabInteractable to {obj.name}.");
        }

        // Ensure collider is not a trigger if it's meant to be physically grabbed
        Collider collider = obj.GetComponent<Collider>();
        if (collider != null)
        {
            collider.isTrigger = false; // Make sure it's a solid collider
        }
    }

    private static void AddInteractablePhysicsObjects()
    {
        Debug.Log("Jules: Adding interactable physics objects...");

        Scene activeScene = EditorSceneManager.GetActiveScene();
        if (!activeScene.IsValid()) {
            Debug.LogError("Jules: No active scene found. Please ensure a scene is open.");
            return;
        }

        // Create a Cube
        GameObject cube = GameObject.CreatePrimitive(PrimitiveType.Cube);
        cube.name = "Interactable_Cube";
        cube.transform.position = new Vector3(0.5f, 1f, 1f); // Position it in the scene
        AddPhysicsAndInteraction(cube); // Make it grabbable and physical
        // Add material
        Renderer cubeRenderer = cube.GetComponent<Renderer>();
        if (cubeRenderer != null) {
            Material mat = new Material(Shader.Find("Standard"));
            mat.color = Color.cyan;
            cubeRenderer.sharedMaterial = mat;
        }
        Debug.Log("Jules: Added Interactable_Cube.");


        // Create a Sphere
        GameObject sphere = GameObject.CreatePrimitive(PrimitiveType.Sphere);
        sphere.name = "Interactable_Sphere";
        sphere.transform.position = new Vector3(-0.5f, 1f, 1f);
        AddPhysicsAndInteraction(sphere);
        // Add material
        Renderer sphereRenderer = sphere.GetComponent<Renderer>();
        if (sphereRenderer != null) {
            Material mat = new Material(Shader.Find("Standard"));
            mat.color = Color.magenta;
            sphereRenderer.sharedMaterial = mat;
        }
        Debug.Log("Jules: Added Interactable_Sphere.");

        // Create a Cylinder
        GameObject cylinder = GameObject.CreatePrimitive(PrimitiveType.Cylinder);
        cylinder.name = "Interactable_Cylinder";
        cylinder.transform.position = new Vector3(0f, 1f, 0.5f);
        AddPhysicsAndInteraction(cylinder);
        // Add material
        Renderer cylinderRenderer = cylinder.GetComponent<Renderer>();
        if (cylinderRenderer != null) {
            Material mat = new Material(Shader.Find("Standard"));
            mat.color = Color.yellow;
            cylinderRenderer.sharedMaterial = mat;
        }
        Debug.Log("Jules: Added Interactable_Cylinder.");

        EditorSceneManager.SaveScene(activeScene); // Save the scene
        AssetDatabase.SaveAssets();
        AssetDatabase.Refresh();
        Debug.Log("Jules: Interactable physics objects added to the scene.");
    }

    private static void CreateRubeGoldbergPrefabs()
    {
        Debug.Log("Jules: Creating Rube Goldberg prefabs...");

        string prefabsPath = "Assets/RubeGoldbergPrefabs";
        if (!AssetDatabase.IsValidFolder(prefabsPath))
        {
            AssetDatabase.CreateFolder("Assets", "RubeGoldbergPrefabs");
            Debug.Log($"Jules: Created folder: {prefabsPath}");
        }

        // --- Ramp Prefab ---
        GameObject rampBase = GameObject.CreatePrimitive(PrimitiveType.Cube);
        rampBase.name = "Ramp_Prefab_Base"; // Temporary name for prefab creation
        rampBase.transform.localScale = new Vector3(1.0f, 0.1f, 2.0f); // Thin, long ramp surface
        rampBase.transform.rotation = Quaternion.Euler(-15f, 0, 0); // Tilt it by 15 degrees
        rampBase.transform.position = new Vector3(0, 0.5f, 0); // Position it slightly above ground

        // Ramps are usually static, but can be interactable if desired.
        // For a simple Rube Goldberg machine, a static ramp is fine.
        // If it needs to be moved by the player, then AddPhysicsAndInteraction(rampBase);
        // For now, let's assume it's static and doesn't need XRGrabInteractable.
        // A Rigidbody is still useful if other dynamic objects will interact with it.
        // If it's purely static geometry, even Rigidbody might be omitted, but ensure it has a collider.
        if (rampBase.GetComponent<Rigidbody>() == null)
        {
            Rigidbody rb = rampBase.AddComponent<Rigidbody>();
            rb.isKinematic = true; // Make it static so it doesn't fall, but can interact
            Debug.Log($"Jules: Added Kinematic Rigidbody to {rampBase.name}.");
        }


        string rampPrefabPath = $"{prefabsPath}/Ramp.prefab";
        PrefabUtility.SaveAsPrefabAsset(rampBase, rampPrefabPath);
        Object.DestroyImmediate(rampBase); // Clean up the temporary GameObject
        Debug.Log($"Jules: Created Ramp prefab at {rampPrefabPath}.");


        // --- Lever Prefab (Simple representation) ---
        // A lever typically has a base (pivot) and an arm that rotates.
        GameObject leverBase = new GameObject("Lever_Prefab_Base"); // Parent GameObject for the lever parts

        // Pivot (fulcrum) - could be a small cylinder or cube
        GameObject pivot = GameObject.CreatePrimitive(PrimitiveType.Cylinder);
        pivot.name = "Pivot";
        pivot.transform.SetParent(leverBase.transform);
        pivot.transform.localScale = new Vector3(0.1f, 0.5f, 0.1f); // Small, tall cylinder
        pivot.transform.localPosition = new Vector3(0, 0.25f, 0); // Position pivot at base center

        // Add a kinematic Rigidbody to the pivot. This allows the HingeJoint to connect to it
        // and treats the pivot as a fixed point in space for the joint.
        Rigidbody pivotRb = pivot.AddComponent<Rigidbody>();
        pivotRb.isKinematic = true;
        Debug.Log($"Jules: Added kinematic Rigidbody to {pivot.name}.");

        // Arm of the lever
        GameObject arm = GameObject.CreatePrimitive(PrimitiveType.Cube);
        arm.name = "Arm";
        arm.transform.SetParent(leverBase.transform); // Parent to the leverBase
        arm.transform.localScale = new Vector3(0.1f, 0.1f, 1.0f); // Long, thin arm
        arm.transform.localPosition = new Vector3(0, 0.5f, 0.5f); // Position arm relative to pivot (offset along Z)

        // Add Rigidbody to the arm so it can be affected by physics and the joint
        Rigidbody armRb = arm.AddComponent<Rigidbody>();
        armRb.mass = 0.5f; // Give it some mass

        // Add HingeJoint to the arm, connecting it to the pivot
        HingeJoint hj = arm.AddComponent<HingeJoint>();
        hj.connectedBody = pivotRb; // Connect to the pivot's Rigidbody
        hj.anchor = new Vector3(0, 0, -0.5f); // Anchor point of the joint on the arm (local space)
        hj.axis = new Vector3(1, 0, 0); // Axis of rotation (e.g., around X-axis)
        hj.useLimits = true;
        JointLimits limits = hj.limits;
        limits.min = -45f; // Min rotation angle
        limits.max = 45f; // Max rotation angle
        hj.limits = limits;
        Debug.Log($"Jules: Configured HingeJoint on {arm.name}, connected to {pivot.name}.");

        // Make the arm grabbable
        XRGrabInteractable armGrab = arm.AddComponent<XRGrabInteractable>();
        // For a lever, we usually want to rotate it around the hinge, not move it freely.
        // So, we might disable position tracking or use a specific grab configuration.
        armGrab.trackPosition = false; // HingeJoint controls position, grab controls rotation input.

        string leverPrefabPath = $"{prefabsPath}/Lever.prefab";
        PrefabUtility.SaveAsPrefabAsset(leverBase, leverPrefabPath);
        Object.DestroyImmediate(leverBase);
        Debug.Log($"Jules: Created Lever prefab at {leverPrefabPath}.");


        // --- Domino Prefab ---
        GameObject domino = GameObject.CreatePrimitive(PrimitiveType.Cube);
        domino.name = "Domino_Prefab";
        domino.transform.localScale = new Vector3(0.1f, 0.5f, 0.25f); // Standard domino-like proportions
        AddPhysicsAndInteraction(domino); // Make it grabbable and physical

        string dominoPrefabPath = $"{prefabsPath}/Domino.prefab";
        PrefabUtility.SaveAsPrefabAsset(domino, dominoPrefabPath);
        Object.DestroyImmediate(domino);
        Debug.Log($"Jules: Created Domino prefab at {dominoPrefabPath}.");

        AssetDatabase.SaveAssets();
        AssetDatabase.Refresh();
        Debug.Log("Jules: All Rube Goldberg prefabs created.");
    }
}
