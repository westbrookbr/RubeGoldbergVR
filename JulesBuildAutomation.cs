
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

    // --- Asset Optimization Methods ---

    [MenuItem("Jules/Apply Asset Optimizations")]
    public static void ApplyAssetOptimizations()
    {{
        Debug.Log("JulesBuildAutomation: Starting Asset Optimizations & Runtime Performance Setup...");
        OptimizeTextureImportSettings();
        OptimizeMeshImportSettings();
        OptimizeAudioImportSettings();

        // Runtime Performance Methods
        EnableBatching();
        ConfigureLightBaking();
        SetupPhysicsLayerCulling();

        AssetDatabase.SaveAssets();
        AssetDatabase.Refresh();
        Debug.Log("JulesBuildAutomation: All Asset Optimizations and Runtime Performance Settings applied.");
    }}

    public static void EnableBatching()
    {{
        Debug.Log("JulesBuildAutomation: Enabling Static and Dynamic Batching...");
        PlayerSettings.staticBatching = true;
        PlayerSettings.dynamicBatching = true; // Requires GraphicsSettings.useScriptableRenderPipelineBatching if SRP is used. Assuming built-in.
        Debug.Log($"JulesBuildAutomation: Static Batching: {{PlayerSettings.staticBatching}}, Dynamic Batching: {{PlayerSettings.dynamicBatching}}");
    }}

    public static void ConfigureLightBaking()
    {{
        Debug.Log("JulesBuildAutomation: Configuring Light Baking Settings...");
        // Focus on global settings. Scene-specific settings are more complex.
        LightmapEditorSettings.mixedBakeMode = MixedLightingMode.Subtractive;
        // Other potential settings:
        // LightmapEditorSettings.realtimeGI = false; // If focusing on baked lighting primarily
        // LightmapEditorSettings.bakedGI = true;
        Debug.Log($"JulesBuildAutomation: Set Mixed Bake Mode to {{LightmapEditorSettings.mixedBakeMode}}.");
    }}

    public static void SetupPhysicsLayerCulling()
    {{
        Debug.Log("JulesBuildAutomation: Setting up Physics Layer Collision Matrix...");

        string[] layerNames = new string[] {{ "Player", "Environment", "Interactables" }};
        EnsureLayersExist(layerNames);

        int playerLayer = LayerMask.NameToLayer("Player");
        int environmentLayer = LayerMask.NameToLayer("Environment");
        int interactablesLayer = LayerMask.NameToLayer("Interactables");

        // Verify layers were found/created
        if (playerLayer == -1 || environmentLayer == -1 || interactablesLayer == -1)
        {{
            Debug.LogError("JulesBuildAutomation: Could not find or create all necessary layers for physics culling. Aborting SetupPhysicsLayerCulling.");
            return;
        }}

        Debug.Log($"JulesBuildAutomation: Using layers - Player: {{playerLayer}}, Environment: {{environmentLayer}}, Interactables: {{interactablesLayer}}");

        // Default: All layers collide with each other. We will ignore specific pairs.

        // Disable collision between Interactables and other Interactables
        Physics.IgnoreLayerCollision(interactablesLayer, interactablesLayer, true);
        Debug.Log("JulesBuildAutomation: Disabled collisions between 'Interactables' and 'Interactables'.");

        // Example: Player should collide with Environment and Interactables (so no IgnoreLayerCollision(..., ..., true))
        // Explicitly ensure they collide (though it's default)
        Physics.IgnoreLayerCollision(playerLayer, environmentLayer, false);
        Physics.IgnoreLayerCollision(playerLayer, interactablesLayer, false);
        Debug.Log("JulesBuildAutomation: Ensured 'Player' collides with 'Environment' and 'Interactables'.");

        // Example: Interactables should collide with Environment
        Physics.IgnoreLayerCollision(interactablesLayer, environmentLayer, false);
        Debug.Log("JulesBuildAutomation: Ensured 'Interactables' collides with 'Environment'.");

        // Potentially disable Player vs Player if multiple player entities might exist on same layer
        // Physics.IgnoreLayerCollision(playerLayer, playerLayer, true);

        Debug.Log("JulesBuildAutomation: Physics Layer Collision Matrix setup complete.");
    }}

    [MenuItem("Jules/Setup Object Pools")]
    public static void SetupRubeGoldbergObjectPools()
    {{
        Debug.Log("JulesBuildAutomation: Setting up Rube Goldberg Object Pools...");

        string prefabsPath = "Assets/RubeGoldbergPrefabs";
        if (!AssetDatabase.IsValidFolder(prefabsPath))
        {{
            Debug.LogError($"JulesBuildAutomation: Prefabs folder '{prefabsPath}' not found. Run 'Create Rube Goldberg Prefabs' first.");
            return;
        }}

        string[] prefabNames = {{ "Ramp", "Lever", "Domino" }};
        int prewarmCount = 5;

        foreach (string prefabName in prefabNames)
        {{
            string prefabFilePath = $"{prefabsPath}/{prefabName}.prefab";
            GameObject prefab = AssetDatabase.LoadAssetAtPath<GameObject>(prefabFilePath);

            if (prefab == null)
            {{
                Debug.LogError($"JulesBuildAutomation: Prefab '{prefabName}' not found at '{prefabFilePath}'. Cannot create pool.");
                continue;
            }}

            // Create a GameObject to host the pool
            string poolGameObjectName = $"{prefabName}_Pool";
            GameObject poolGO = GameObject.Find(poolGameObjectName);
            if (poolGO == null)
            {{
                poolGO = new GameObject(poolGameObjectName);
                Debug.Log($"JulesBuildAutomation: Created Pool GameObject: {poolGameObjectName}");
            }}
            else
            {{
                Debug.Log($"JulesBuildAutomation: Found existing Pool GameObject: {poolGameObjectName}");
            }}

            SimpleObjectPool pool = poolGO.GetComponent<SimpleObjectPool>();
            if (pool == null)
            {{
                pool = poolGO.AddComponent<SimpleObjectPool>();
                Debug.Log($"JulesBuildAutomation: Added SimpleObjectPool component to {poolGameObjectName}");
            }}

            pool.Prewarm(prefab, prewarmCount);
            Debug.Log($"JulesBuildAutomation: Prewarmed pool for '{prefabName}' with {prewarmCount} objects.");
        }}
        EditorSceneManager.MarkSceneDirty(EditorSceneManager.GetActiveScene()); // Ensure scene changes are saved
        Debug.Log("JulesBuildAutomation: Rube Goldberg Object Pools setup complete.");
    }}

    // Helper method to add layers if they don't exist
    private static void EnsureLayersExist(string[] layerNames)
    {{
        Debug.Log("JulesBuildAutomation: Ensuring custom layers exist...");
        SerializedObject tagManager = new SerializedObject(AssetDatabase.LoadAssetAtPath<Object>("ProjectSettings/TagManager.asset"));
        SerializedProperty layersProp = tagManager.FindProperty("layers");

        if (layersProp == null || !layersProp.isArray)
        {{
            Debug.LogError("JulesBuildAutomation: Could not find 'layers' property in TagManager.asset.");
            return;
        }}

        foreach (string layerName in layerNames)
        {{
            bool layerExists = false;
            // Check existing layers (user layers start at index 8)
            for (int i = 8; i < layersProp.arraySize; i++)
            {{
                SerializedProperty layerSP = layersProp.GetArrayElementAtIndex(i);
                if (layerSP.stringValue == layerName)
                {{
                    layerExists = true;
                    Debug.Log($"JulesBuildAutomation: Layer '{{layerName}}' already exists.");
                    break;
                }}
            }}

            if (!layerExists)
            {{
                SerializedProperty firstEmptyLayer = null;
                for (int i = 8; i < layersProp.arraySize; i++)
                {{
                    SerializedProperty layerSP = layersProp.GetArrayElementAtIndex(i);
                    if (string.IsNullOrEmpty(layerSP.stringValue))
                    {{
                        firstEmptyLayer = layerSP;
                        break;
                    }}
                }}

                if (firstEmptyLayer != null)
                {{
                    firstEmptyLayer.stringValue = layerName;
                    Debug.Log($"JulesBuildAutomation: Added layer '{{layerName}}'.");
                }}
                else
                {{
                    Debug.LogWarning($"JulesBuildAutomation: Could not add layer '{{layerName}}'. No empty layer slots available in TagManager.");
                }}
            }}
        }}
        tagManager.ApplyModifiedProperties();
        AssetDatabase.SaveAssets(); // Save changes to TagManager.asset
    }}

    public static void OptimizeTextureImportSettings()
    {{
        Debug.Log("JulesBuildAutomation: Optimizing Texture Import Settings...");
        string[] textureGuids = AssetDatabase.FindAssets("t:Texture");
        foreach (string guid in textureGuids)
        {{
            string path = AssetDatabase.GUIDToAssetPath(guid);
            TextureImporter textureImporter = AssetImporter.GetAtPath(path) as TextureImporter;
            if (textureImporter != null)
            {{
                Debug.Log($"JulesBuildAutomation: Processing Texture: {{path}}");
                textureImporter.mipmapEnabled = true;

                // Standalone (Windows, Mac, Linux) Settings
                TextureImporterPlatformSettings standaloneSettings = textureImporter.GetPlatformTextureSettings("Standalone");
                standaloneSettings.overridden = true;
                standaloneSettings.format = textureImporter.DoesSourceTextureHaveAlpha() ? TextureImporterFormat.DXT5 : TextureImporterFormat.DXT1;
                standaloneSettings.compressionQuality = (int)TextureCompressionQuality.Normal; // Default is Normal (50)
                textureImporter.SetPlatformTextureSettings(standaloneSettings);

                // Android Settings
                TextureImporterPlatformSettings androidSettings = textureImporter.GetPlatformTextureSettings("Android");
                androidSettings.overridden = true;
                androidSettings.format = TextureImporterFormat.ASTC_4x4; // A common choice for ASTC
                androidSettings.compressionQuality = (int)TextureCompressionQuality.Normal;
                textureImporter.SetPlatformTextureSettings(androidSettings);

                EditorUtility.SetDirty(textureImporter);
                textureImporter.SaveAndReimport();
            }}
        }}
        Debug.Log($"JulesBuildAutomation: Finished optimizing {{textureGuids.Length}} textures.");
    }}

    public static void OptimizeMeshImportSettings()
    {{
        Debug.Log("JulesBuildAutomation: Optimizing Mesh Import Settings...");
        string[] modelGuids = AssetDatabase.FindAssets("t:Model");
        foreach (string guid in modelGuids)
        {{
            string path = AssetDatabase.GUIDToAssetPath(guid);
            ModelImporter modelImporter = AssetImporter.GetAtPath(path) as ModelImporter;
            if (modelImporter != null)
            {{
                Debug.Log($"JulesBuildAutomation: Processing Model: {{path}}");
                modelImporter.meshCompression = ModelImporterMeshCompression.Medium;
                modelImporter.optimizeMeshData = true;
                // modelImporter.isReadable = false; // Set to false if you don't need to access mesh data from scripts at runtime

                EditorUtility.SetDirty(modelImporter);
                modelImporter.SaveAndReimport();
            }}
        }}
        Debug.Log($"JulesBuildAutomation: Finished optimizing {{modelGuids.Length}} models.");
    }}

    public static void OptimizeAudioImportSettings()
    {{
        Debug.Log("JulesBuildAutomation: Optimizing Audio Import Settings...");
        string[] audioGuids = AssetDatabase.FindAssets("t:AudioClip");
        foreach (string guid in audioGuids)
        {{
            string path = AssetDatabase.GUIDToAssetPath(guid);
            AudioImporter audioImporter = AssetImporter.GetAtPath(path) as AudioImporter;
            if (audioImporter != null)
            {{
                Debug.Log($"JulesBuildAutomation: Processing AudioClip: {{path}}");

                // Common settings
                audioImporter.forceToMono = false; // Assuming stereo is desired where available
                audioImporter.loadInBackground = true; // Good for non-critical sounds

                // Standalone (Windows, Mac, Linux) Settings
                AudioImporterSampleSettings standaloneSettings = audioImporter.GetOverrideSampleSettings("Standalone");
                if (standaloneSettings.compressionFormat != AudioCompressionFormat.Vorbis || standaloneSettings.quality < 0.7f) // Check if already optimal
                {{
                    standaloneSettings.loadType = AudioClipLoadType.CompressedInMemory; // Or Streaming for music
                    standaloneSettings.compressionFormat = AudioCompressionFormat.Vorbis;
                    standaloneSettings.quality = 0.8f; // Higher quality for standalone
                    audioImporter.SetOverrideSampleSettings("Standalone", standaloneSettings);
                }}

                // Android Settings
                AudioImporterSampleSettings androidSettings = audioImporter.GetOverrideSampleSettings("Android");
                if (androidSettings.compressionFormat != AudioCompressionFormat.Vorbis || androidSettings.quality > 0.6f) // Check if already optimal or needs more compression
                {{
                    androidSettings.loadType = AudioClipLoadType.CompressedInMemory; // Or Streaming for music
                    androidSettings.compressionFormat = AudioCompressionFormat.Vorbis;
                    androidSettings.quality = 0.5f; // Moderate quality for Android
                    audioImporter.SetOverrideSampleSettings("Android", androidSettings);
                }}

                // Fallback settings for other platforms (optional, but good practice)
                AudioImporterSampleSettings defaultSettings = audioImporter.defaultSampleSettings;
                if (defaultSettings.compressionFormat != AudioCompressionFormat.Vorbis)
                {{
                    defaultSettings.loadType = AudioClipLoadType.CompressedInMemory;
                    defaultSettings.compressionFormat = AudioCompressionFormat.Vorbis;
                    defaultSettings.quality = 0.7f; // Default quality
                    audioImporter.defaultSampleSettings = defaultSettings;
                }}

                // Only reimport if changes were made.
                // Check if any settings were actually changed to avoid unnecessary reimports.
                // For simplicity in this step, we'll reimport if the importer is dirty.
                // A more robust check would compare old vs new settings for each platform.
                if (EditorUtility.IsDirty(audioImporter)) // Heuristic: if we set overrides, it's likely dirty.
                {{
                     EditorUtility.SetDirty(audioImporter);
                     audioImporter.SaveAndReimport();
                }}
            }}
        }}
        Debug.Log($"JulesBuildAutomation: Finished optimizing {{audioGuids.Length}} audio clips.");
    }}

    public static void OptimizeBuildSettings()
    {{
        Debug.Log("JulesBuildAutomation: Optimizing Build Settings...");

        // --- Stripping Level ---
        // For Android
        PlayerSettings.SetManagedStrippingLevel(BuildTargetGroup.Android, ManagedStrippingLevel.StripEngineCode);
        Debug.Log($"JulesBuildAutomation: Set Android Managed Stripping Level to StripEngineCode.");

        // For Standalone
        PlayerSettings.SetManagedStrippingLevel(BuildTargetGroup.Standalone, ManagedStrippingLevel.Medium); // A common general stripping level
        PlayerSettings.stripUnusedMeshComponents = true; // Specific mesh stripping
        Debug.Log($"JulesBuildAutomation: Set Standalone Managed Stripping Level to Medium and enabled stripUnusedMeshComponents.");

        // --- API Compatibility Level ---
        // Set for Android
        PlayerSettings.SetApiCompatibilityLevel(BuildTargetGroup.Android, ApiCompatibilityLevel.NET_Standard_2_1);
        Debug.Log($"JulesBuildAutomation: Set Android API Compatibility Level to .NET Standard 2.1.");

        // Set for Standalone
        PlayerSettings.SetApiCompatibilityLevel(BuildTargetGroup.Standalone, ApiCompatibilityLevel.NET_Standard_2_1);
        Debug.Log($"JulesBuildAutomation: Set Standalone API Compatibility Level to .NET Standard 2.1.");

        Debug.Log("JulesBuildAutomation: Finished Optimizing Build Settings.");
    }}

    [MenuItem("Jules/PerformAlphaTestBuild")]
    public static void PerformAlphaTestBuild()
    {{
        Debug.Log("JulesBuildAutomation: Starting Alpha Test Build...");

        // Call general build and asset optimization methods first.
        // These methods may contain their own platform-specific logic or apply globally.
        OptimizeBuildSettings();
        ApplyAssetOptimizations(); // Ensure assets are optimized before building

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

        // --- Demonstrate fetching from Rube Goldberg Object Pools ---
        Debug.Log("JulesBuildAutomation: Attempting to fetch Rube Goldberg elements from pools...");
        string[] prefabNamesToFetch = {{ "Ramp", "Lever", "Domino" }};
        float xOffset = 2.0f; // Initial x-offset for placing fetched objects

        foreach (string prefabName in prefabNamesToFetch)
        {{
            string poolGameObjectName = $"{prefabName}_Pool";
            GameObject poolGO = GameObject.Find(poolGameObjectName);
            if (poolGO != null)
            {{
                SimpleObjectPool pool = poolGO.GetComponent<SimpleObjectPool>();
                if (pool != null)
                {{
                    GameObject instance = pool.Get();
                    if (instance != null)
                    {{
                        instance.transform.position = new Vector3(xOffset, 1.0f, 2.0f);
                        // Apply physics and interaction if needed, though prefabs should ideally have this pre-configured.
                        // For demonstration, we assume the prefab is already configured correctly.
                        // AddPhysicsAndInteraction(instance); // Uncomment if prefabs are very basic
                        Debug.Log($"JulesBuildAutomation: Fetched '{instance.name}' from pool and placed at x={xOffset}.");
                        xOffset += 1.5f; // Increment x-offset for next object
                    }}
                    else
                    {{
                        Debug.LogWarning($"JulesBuildAutomation: Failed to Get() object for '{prefabName}' from its pool.");
                    }}
                }}
                else
                {{
                    Debug.LogWarning($"JulesBuildAutomation: SimpleObjectPool component not found on '{poolGameObjectName}'.");
                }}
            }}
            else
            {{
                Debug.LogWarning($"JulesBuildAutomation: Pool GameObject '{poolGameObjectName}' not found. Run 'Setup Object Pools' first.");
            }}
        }}
        EditorSceneManager.MarkSceneDirty(EditorSceneManager.GetActiveScene());
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
