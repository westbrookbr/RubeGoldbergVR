using UnityEngine;
using UnityEditor;
using UnityEditor.XR.Management;
using UnityEngine.XR.Management;

public class JulesBuildAutomation : MonoBehaviour
{
    [MenuItem("Jules/Build Automation/Apply XR Settings")]
    public static void ApplyXRSettings()
    {
        // Corrected item 1: Commented out the problematic line
        // XRGeneralSettingsForEditor.Get === Unity Editor Build Automation ===

        BuildTargetGroup standaloneBuildTargetGroup = BuildTargetGroup.Standalone;
        BuildTargetGroup androidBuildTargetGroup = BuildTargetGroup.Android;

        XRGeneralSettings standaloneGeneralSettings;
        XRGeneralSettings androidGeneralSettings;

        // Corrected item 2: Changed variable name
        standaloneGeneralSettings = GetBuildTargetSettings(standaloneBuildTargetGroup);

        // Corrected item 3: Changed variable name
        androidGeneralSettings = GetBuildTargetSettings(androidBuildTargetGroup);

        XRManagerSettings generalSettings;
        // Corrected item 4: Corrected TryGetConfigObject call
        EditorBuildSettings.TryGetConfigObject(XRGeneralSettingsForEditor.k_SettingsKey, out generalSettings);

        if (standaloneGeneralSettings != null)
        {
            // Corrected item 5: Corrected isInitialized check
            if (!standaloneGeneralSettings.Manager.isInitialized)
            {
                // Corrected item 6: Corrected manager settings
                standaloneGeneralSettings.Manager.automaticInitialize = true;
                standaloneGeneralSettings.Manager.automaticRunning = true;
            }
        }

        if (androidGeneralSettings != null)
        {
            // Corrected item 7: Corrected isInitialized check
            if (!androidGeneralSettings.Manager.isInitialized)
            {
                // Corrected item 8: Corrected manager settings
                androidGeneralSettings.Manager.automaticInitialize = true;
                androidGeneralSettings.Manager.automaticRunning = true;
            }
        }

        // Corrected item 9: Robust XROrigin prefab finding
        string[] guids = AssetDatabase.FindAssets("t:Prefab XROrigin");
        if (guids.Length > 0)
        {
            string path = AssetDatabase.GUIDToAssetPath(guids[0]);
            GameObject xrOriginPrefab = AssetDatabase.LoadAssetAtPath<GameObject>(path);
            if (xrOriginPrefab != null)
            {
                Debug.Log("XROrigin prefab found at: " + path);
                // Further operations with the prefab can be done here
            }
            else
            {
                Debug.LogError("Failed to load XROrigin prefab at path: " + path);
            }
        }
        else
        {
            Debug.LogError("XROrigin prefab not found.");
        }
    }

    static XRGeneralSettings GetBuildTargetSettings(BuildTargetGroup buildTargetGroup)
    {
        XRGeneralSettingsPerBuildTarget buildTargetSettings = null;
        EditorBuildSettings.TryGetConfigObject(XRGeneralSettingsForEditor.k_SettingsKey, out buildTargetSettings);

        if (buildTargetSettings != null)
        {
            return buildTargetSettings.SettingsForBuildTarget(buildTargetGroup);
        }
        return null;
    }
}
