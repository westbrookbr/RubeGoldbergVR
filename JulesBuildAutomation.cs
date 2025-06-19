
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

// JulesBuildAutomation is responsible for automating the setup of a Unity project for VR development,
// including XR package installation, XR settings configuration, and basic scene setup with interactables
// and Rube Goldberg machine prefabs. It's designed to be triggered by external scripts (e.g., Python)
// for a fully automated project initialization pipeline.
public class JulesBuildAutomation
{{
    private const string ProjectName = "RubeGoldbergVR";
    private static List<string> xrPackages = new List<string>
    {{
        "com.unity.xr.interaction.toolkit@2.3.1",
        "com.unity.xr.openxr@1.9.0"
    }};

    private static AddRequest currentAddRequest;
    private static int packageIndex = 0;

    // This is the main entry point called by the Python script.
    // It triggers the entire setup sequence for the VR project.
    [MenuItem("Jules/SetupVRProject")]
    public static void SetupVRProject()
    {{
        Debug.Log("JulesBuildAutomation: Initiating VR Project Setup Sequence (XR Packages, XR Settings)...");
        EnsureEditorFolderExists();
        InstallXRPackages();
    }}

    [MenuItem("Jules/PerformAlphaTestBuild")]
    public static void PerformAlphaTestBuild()
    {{
        Debug.Log("JulesBuildAutomation: Starting Alpha Test Build...");

        string sampleScenePath = "Assets/Scenes/SampleScene.unity";
        if (!File.Exists(sampleScenePath))
        {{
            Debug.LogError($"JulesBuildAutomation: Scene '{{sampleScenePath}}' not found for build. Please ensure it exists.");
            EditorApplication.Exit(1);
            return;
        }}

        BuildPlayerOptions buildOptions = new BuildPlayerOptions();
        buildOptions.scenes = new[] {{ sampleScenePath }};

        string windowsBuildPath = $"Builds/AlphaTest/Windows/{{ProjectName}}.exe";
        string androidBuildPath = $"Builds/AlphaTest/Android/{{ProjectName}}.apk";

        Directory.CreateDirectory(Path.GetDirectoryName(windowsBuildPath));
        Directory.CreateDirectory(Path.GetDirectoryName(androidBuildPath));

        Debug.Log("JulesBuildAutomation: Building for Windows Standalone (Alpha Test)...");
        buildOptions.locationPathName = windowsBuildPath;
        buildOptions.target = BuildTarget.StandaloneWindows64;
        buildOptions.options = BuildOptions.None;

        BuildReport reportWindows = BuildPipeline.BuildPlayer(buildOptions);
        BuildSummary summaryWindows = reportWindows.summary;

        if (summaryWindows.result == BuildResult.Succeeded)
        {{
            Debug.Log($"JulesBuildAutomation: Windows Alpha Test Build succeeded: {{summaryWindows.totalSize}} bytes at {{windowsBuildPath}}");
        }}
        else if (summaryWindows.result == BuildResult.Failed)
        {{
            Debug.LogError($"JulesBuildAutomation: Windows Alpha Test Build failed: {{summaryWindows.totalErrors}} errors");
            EditorApplication.Exit(1);
            return;
        }}

        Debug.Log("JulesBuildAutomation: Building for Android (Alpha Test for Quest/VR)...");
        buildOptions.locationPathName = androidBuildPath;
        buildOptions.target = BuildTarget.Android;
        buildOptions.options = BuildOptions.None;

        if (!EditorUserBuildSettings.activeBuildTarget.Equals(BuildTarget.Android))
        {{
            Debug.Log("JulesBuildAutomation: Switching active build target to Android for build...");
            EditorUserBuildSettings.SwitchActiveBuildTarget(BuildTargetGroup.Android, BuildTarget.Android);
        }}

        BuildReport reportAndroid = BuildPipeline.BuildPlayer(buildOptions);
        BuildSummary summaryAndroid = reportAndroid.summary;

        if (summaryAndroid.result == BuildResult.Succeeded)
        {{
            Debug.Log($"JulesBuildAutomation: Android Alpha Test Build succeeded: {{summaryAndroid.totalSize}} bytes at {{androidBuildPath}}");
        }}
        else if (summaryAndroid.result == BuildResult.Failed)
        {{
            Debug.LogError($"JulesBuildAutomation: Android Alpha Test Build failed: {{summaryAndroid.totalErrors}} errors");
            EditorApplication.Exit(1);
            return;
        }}

        Debug.Log("JulesBuildAutomation: All Alpha Test Builds completed successfully.");
        EditorApplication.Exit(0);
    }}

    // This method is automatically called after successful XR configuration (via EditorApplication.delayCall).
    // It is responsible for the initial scene setup, including basic VR elements,
    // interactable objects, and the creation of Rube Goldberg machine prefabs.
    [MenuItem("Jules/SetupRubeGoldbergGame")]
    public static void SetupRubeGoldbergGame()
    {{
        Debug.Log("JulesBuildAutomation: Starting Rube Goldberg Game Setup (Scene, Interactables, Prefabs)...");
        CreateBasicVRSceneElements();
        AddInteractablePhysicsObjects();
        CreateRubeGoldbergPrefabs();
        EditorApplication.Exit(0); // Ensure this is present to signal completion in batch mode
    }}

    // Ensures that the "Assets/Editor" folder exists, creating it if necessary.
    // This folder is often required for editor scripts.
    private static void EnsureEditorFolderExists()
    {{
        if (!AssetDatabase.IsValidFolder("Assets/Editor"))
        {{
            AssetDatabase.CreateFolder("Assets", "Editor");
            Debug.Log("JulesBuildAutomation: Created folder: Assets/Editor");
        }}
    }}

    // Initiates the asynchronous installation of necessary XR packages.
    // It sets up a callback to process the package installation queue.
    private static void InstallXRPackages()
    {{
        Debug.Log("JulesBuildAutomation: Queuing XR packages for installation...");
        packageIndex = 0;
        EditorApplication.update += ProcessPackageInstallationQueue;
    }}

    // Handles the sequential installation of XR packages from the xrPackages list.
    // It processes one package at a time and waits for its completion before starting the next.
    // Once all packages are requested, it schedules XR settings configuration.
    private static void ProcessPackageInstallationQueue()
    {{
        if (currentAddRequest != null && !currentAddRequest.IsCompleted)
        {{
            return;
        }}

        if (packageIndex < xrPackages.Count)
        {{
            string packageId = xrPackages[packageIndex];
            Debug.Log($"JulesBuildAutomation: Attempting to install package: {{packageId}}");
            currentAddRequest = Client.Add(packageId);
            packageIndex++;
        }}
        else
        {{
            EditorApplication.update -= ProcessPackageInstallationQueue;
            Debug.Log("JulesBuildAutomation: All XR package installation requests sent. Proceeding to XR Plug-in Management and OpenXR configuration after recompilation (if any)...");
            EditorApplication.delayCall += ConfigureXRSettings;
        }}
    }}

    // This method configures XR for both Standalone (Windows, Mac, Linux) and Android build targets.
    // Crucially, it schedules SetupRubeGoldbergGame to run after its completion using EditorApplication.delayCall,
    // ensuring that scene setup happens only after XR is fully configured.
    private static void ConfigureXRSettings()
    {{
        Debug.Log("JulesBuildAutomation: Starting XR Plug-in Management and OpenXR configuration for all target platforms...");

        ConfigureBuildTargetXRSettings(BuildTargetGroup.Standalone, BuildTarget.StandaloneWindows64, "Windows, Mac & Linux");
        ConfigureBuildTargetXRSettings(BuildTargetGroup.Android, BuildTarget.Android, "Android");

        AssetDatabase.SaveAssets();
        AssetDatabase.Refresh();

        Debug.Log("JulesBuildAutomation: XR Plug-in Management and OpenXR configuration complete.");
        Debug.Log("JulesBuildAutomation: Scheduling Rube Goldberg Game Setup to run next...");
        EditorApplication.delayCall += SetupRubeGoldbergGame; // Ensures this runs after XR setup and potential recompilations
    }}

    // Helper method for setting up XR for a specific build target (e.g., Standalone, Android).
    // It configures XR General Settings, XR Manager, and OpenXR specific settings including interaction profiles.
    private static void ConfigureBuildTargetXRSettings(BuildTargetGroup buildTargetGroup, BuildTarget buildTarget, string tabName)
    {{
        Debug.Log($"JulesBuildAutomation: Configuring XR for {{tabName}}...");

        XRGeneralSettingsForEditor generalSettings;
        string settingsKey = XRGeneralSettingsForEditor.k_SettingsKey;

        if (!EditorBuildSettings.TryGetConfigObject(settingsKey, out generalSettings))
        {{
            generalSettings = ScriptableObject.CreateInstance<XRGeneralSettingsForEditor>();
            EditorBuildSettings.AddConfigObject(settingsKey, generalSettings, true);
            Debug.Log($"JulesBuildAutomation: Created new XRGeneralSettingsForEditor for {{tabName}}.");
        }}

        XRGeneralSettingsForEditor.SetBuildTargetSettings(buildTargetGroup, generalSettings);

        EditorUserBuildSettings.activeBuildTargetGroup = buildTargetGroup;
        EditorUserBuildSettings.SwitchActiveBuildTarget(buildTargetGroup, buildTarget);

        if (generalSettings.Manager == null)
        {{
            generalSettings.Manager = ScriptableObject.CreateInstance<XRManagerSettings>();
            EditorUtility.SetDirty(generalSettings);
            Debug.Log($"JulesBuildAutomation: Created new XRManagerSettings for {{tabName}}.");
        }}

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
            Debug.Log($"JulesBuildAutomation: Added OpenXR Loader to {{tabName}} XR General Settings.");
        }}

        OpenXRSettings openXRSettings = OpenXRSettings.GetForBuildTargetGroup(buildTargetGroup);
        if (openXRSettings != null)
        {{
            Debug.Log($"JulesBuildAutomation: Configuring {{tabName}} OpenXR settings...");

            AddOpenXRInteractionProfile(openXRSettings, "com.unity.openxr.features.oculustouchcontroller");
            AddOpenXRInteractionProfile(openXRSettings, "com.unity.openxr.features.metarequestsupport");
            AddOpenXRInteractionProfile(openXRSettings, "com.unity.openxr.features.hp_reverb_g2_controller");

            EditorUtility.SetDirty(openXRSettings);
        }}
        else
        {{
            Debug.LogWarning($"JulesBuildAutomation: OpenXRSettings not found for {{tabName}}. This might indicate a problem with package installation or XR management setup.");
        }}

        EditorUtility.SetDirty(generalSettings);
    }}

    // Adds a specified OpenXR interaction profile feature if it's not already enabled.
    private static void AddOpenXRInteractionProfile(OpenXRSettings settings, string featureId)
    {{
        foreach (var feature in OpenXRSettings.GetAllFeatures(settings.buildTargetGroup))
        {{
            if (feature.featureId == featureId)
            {{
                if (!feature.enabled)
                {{
                    feature.enabled = true;
                    Debug.Log($"JulesBuildAutomation: Enabled OpenXR feature: {{feature.name}} (ID: {{feature.featureId}}) for {{settings.buildTargetGroup}}.");
                }} else {{
                    Debug.Log($"JulesBuildAutomation: OpenXR feature: {{feature.name}} (ID: {{feature.featureId}}) already enabled for {{settings.buildTargetGroup}}.");
                }}
                return;
            }}
        }}
        Debug.LogWarning($"JulesBuildAutomation: OpenXR feature with ID '{{featureId}}' not found for {{settings.buildTargetGroup}}. Ensure the relevant package/feature set is installed.");
    }}

    // Creates the basic elements required for a VR scene, including XR Origin, controllers, and a ground plane.
    // It also ensures a sample scene exists or creates one.
    private static void CreateBasicVRSceneElements()
    {{
        Debug.Log("JulesBuildAutomation: Creating basic VR scene elements...");

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
            Debug.Log($"JulesBuildAutomation: Created new scene at: {{sampleScenePath}}");
        }}
        else
        {{
            activeScene = EditorSceneManager.OpenScene(sampleScenePath);
            Debug.Log($"JulesBuildAutomation: Opened existing scene at: {{sampleScenePath}}");
        }}

        GameObject mainCamera = GameObject.FindWithTag("MainCamera");
        if (mainCamera != null && mainCamera.GetComponent<Camera>() != null && mainCamera.GetComponent<Camera>().CompareTag("MainCamera"))
        {{
            Debug.Log("JulesBuildAutomation: Found and removing default Main Camera.");
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
            Debug.Log("JulesBuildAutomation: Added XR Interaction Manager.");
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
        Debug.Log("JulesBuildAutomation: Basic VR scene elements created and scene saved.");
    }}

    // Helper method to add an XR controller (left or right) to the scene with appropriate interactors.
    private static void AddXRController(Transform parent, string name, bool isLeftHand)
    {{
        GameObject controllerGO = new GameObject(name);
        controllerGO.transform.SetParent(parent);

        var controller = controllerGO.AddComponent<UnityEngine.XR.Interaction.Toolkit.XRController>();
        controller.controllerNode = isLeftHand ? UnityEngine.XR.XRNode.LeftHand : UnityEngine.XR.XRNode.RightHand;

        if (isLeftHand)
        {{
            controllerGO.AddComponent<UnityEngine.XR.Interaction.Toolkit.XRRayInteractor>();
            Debug.Log($"JulesBuildAutomation: Added {{name}} with XRRayInteractor.");
        }}
        else
        {{
            controllerGO.AddComponent<UnityEngine.XR.Interaction.Toolkit.XRDirectInteractor>();
            Debug.Log($"JulesBuildAutomation: Added {{name}} with XRDirectInteractor.");
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

    // Adds Rigidbody and XRGrabInteractable components to a GameObject to make it a grabbable physics object.
    private static void AddPhysicsAndInteraction(GameObject obj)
    {{
        if (obj.GetComponent<Rigidbody>() == null)
        {{
            Rigidbody rb = obj.AddComponent<Rigidbody>();
            rb.mass = 1.0f;
            Debug.Log($"JulesBuildAutomation: Added Rigidbody to {{obj.name}}.");
        }}

        if (obj.GetComponent<XRGrabInteractable>() == null)
        {{
            obj.AddComponent<XRGrabInteractable>();
            Debug.Log($"JulesBuildAutomation: Added XRGrabInteractable to {{obj.name}}.");
        }}

        Collider collider = obj.GetComponent<Collider>();
        if (collider != null)
        {{
            collider.isTrigger = false;
        }}
    }}

    // Adds a set of interactable physics-enabled objects (cube, sphere, cylinder) to the current scene.
    private static void AddInteractablePhysicsObjects()
    {{
        Debug.Log("JulesBuildAutomation: Adding interactable physics objects...");

        Scene activeScene = EditorSceneManager.GetActiveScene();
        if (!activeScene.IsValid())
        {{
            Debug.LogError("JulesBuildAutomation: No active scene found. Please ensure a scene is open.");
            return;
        }}

        GameObject cube = GameObject.CreatePrimitive(PrimitiveType.Cube);
        cube.name = "Interactable_Cube";
        cube.transform.position = new Vector3(0.5f, 1f, 1f);
        AddPhysicsAndInteraction(cube);
        Renderer cubeRenderer = cube.GetComponent<Renderer>();
        if (cubeRenderer != null)
        {{
            cubeRenderer.sharedMaterial = new Material(Shader.Find("Standard"));
            cubeRenderer.sharedMaterial.color = Color.cyan;
        }}
        Debug.Log("JulesBuildAutomation: Added Interactable_Cube.");

        GameObject sphere = GameObject.CreatePrimitive(PrimitiveType.Sphere);
        sphere.name = "Interactable_Sphere";
        sphere.transform.position = new Vector3(-0.5f, 1f, 1f);
        AddPhysicsAndInteraction(sphere);
        Renderer sphereRenderer = sphere.GetComponent<Renderer>();
        if (sphereRenderer != null)
        {{
            sphereRenderer.sharedMaterial = new Material(Shader.Find("Standard"));
            sphereRenderer.sharedMaterial.color = Color.magenta;
        }}
        Debug.Log("JulesBuildAutomation: Added Interactable_Sphere.");

        GameObject cylinder = GameObject.CreatePrimitive(PrimitiveType.Cylinder);
        cylinder.name = "Interactable_Cylinder";
        cylinder.transform.position = new Vector3(0f, 1f, 0.5f);
        AddPhysicsAndInteraction(cylinder);
        Renderer cylinderRenderer = cylinder.GetComponent<Renderer>();
        if (cylinderRenderer != null)
        {{
            cylinderRenderer.sharedMaterial = new Material(Shader.Find("Standard"));
            cylinderRenderer.sharedMaterial.color = Color.yellow;
        }}
        Debug.Log("JulesBuildAutomation: Added Interactable_Cylinder.");

        EditorSceneManager.SaveScene(activeScene);
        AssetDatabase.SaveAssets();
        AssetDatabase.Refresh();
        Debug.Log("JulesBuildAutomation: Interactable physics objects added to the scene.");
    }}

    // Creates and saves prefabs for Rube Goldberg machine components (Ramp, Lever, Domino)
    // into the "Assets/RubeGoldbergPrefabs" folder.
    private static void CreateRubeGoldbergPrefabs()
    {{
        Debug.Log("JulesBuildAutomation: Creating Rube Goldberg prefabs...");

        string prefabsPath = "Assets/RubeGoldbergPrefabs";
        if (!AssetDatabase.IsValidFolder(prefabsPath))
        {{
            AssetDatabase.CreateFolder("Assets", "RubeGoldbergPrefabs");
            Debug.Log($"JulesBuildAutomation: Created folder: {{prefabsPath}}");
        }}

        // --- Ramp Prefab ---
        GameObject rampBase = GameObject.CreatePrimitive(PrimitiveType.Cube);
        rampBase.name = "Ramp_Prefab_Base";
        rampBase.transform.localScale = new Vector3(1.0f, 0.1f, 2.0f);
        rampBase.transform.rotation = Quaternion.Euler(-15f, 0, 0);
        rampBase.transform.position = new Vector3(0, 0.5f, 0);

        AddPhysicsAndInteraction(rampBase);

        string rampPrefabPath = $"{{prefabsPath}}/Ramp.prefab";
        PrefabUtility.SaveAsPrefabAsset(rampBase, rampPrefabPath);
        Object.DestroyImmediate(rampBase);
        Debug.Log($"JulesBuildAutomation: Created Ramp prefab at {{rampPrefabPath}}.");

        // --- Lever Prefab (Simple representation) ---
        GameObject leverBase = new GameObject("Lever_Prefab_Base");

        GameObject pivot = GameObject.CreatePrimitive(PrimitiveType.Cylinder);
        pivot.name = "Pivot";
        pivot.transform.SetParent(leverBase.transform);
        pivot.transform.localScale = new Vector3(0.1f, 0.5f, 0.1f);
        pivot.transform.localPosition = new Vector3(0, 0.25f, 0);

        // Add a kinematic Rigidbody to the pivot. This allows the HingeJoint to connect to it.
        // A kinematic Rigidbody does not simulate physics but can act as a fixed reference for joints.
        Rigidbody pivotRb = pivot.AddComponent<Rigidbody>();
        pivotRb.isKinematic = true;
        Debug.Log($"JulesBuildAutomation: Added kinematic Rigidbody to {{pivot.name}}.");

        GameObject arm = GameObject.CreatePrimitive(PrimitiveType.Cube);
        arm.name = "Arm";
        arm.transform.SetParent(leverBase.transform);
        arm.transform.localScale = new Vector3(0.1f, 0.1f, 1.0f);
        arm.transform.localPosition = new Vector3(0, 0.5f, 0.5f);

        Rigidbody armRb = arm.AddComponent<Rigidbody>();
        armRb.mass = 0.5f;

        HingeJoint hj = arm.AddComponent<HingeJoint>();
        // Connect the arm's Rigidbody to the pivot's Rigidbody
        hj.connectedBody = pivotRb;
        hj.anchor = new Vector3(0, 0, -0.5f);
        hj.axis = new Vector3(1, 0, 0);
        hj.useLimits = true;
        JointLimits limits = hj.limits;
        limits.min = -45f;
        limits.max = 45f;
        hj.limits = limits;
        Debug.Log($"JulesBuildAutomation: Configured HingeJoint on {{arm.name}}, connected to {{pivot.name}}.");

        XRGrabInteractable armGrab = arm.AddComponent<XRGrabInteractable>();
        armGrab.trackPosition = false; // HingeJoint handles position, we want to grab for rotation

        string leverPrefabPath = $"{{prefabsPath}}/Lever.prefab";
        PrefabUtility.SaveAsPrefabAsset(leverBase, leverPrefabPath);
        Object.DestroyImmediate(leverBase);
        Debug.Log($"JulesBuildAutomation: Created Lever prefab at {{leverPrefabPath}}.");

        // --- Domino Prefab ---
        GameObject domino = GameObject.CreatePrimitive(PrimitiveType.Cube);
        domino.name = "Domino_Prefab";
        domino.transform.localScale = new Vector3(0.1f, 0.5f, 0.25f);
        AddPhysicsAndInteraction(domino);

        string dominoPrefabPath = $"{{prefabsPath}}/Domino.prefab";
        PrefabUtility.SaveAsPrefabAsset(domino, dominoPrefabPath);
        Object.DestroyImmediate(domino);
        Debug.Log($"JulesBuildAutomation: Created Domino prefab at {{dominoPrefabPath}}.");

        AssetDatabase.SaveAssets();
        AssetDatabase.Refresh();
        Debug.Log("JulesBuildAutomation: All Rube Goldberg prefabs created. Automation sequence complete.");
    }}
}}
