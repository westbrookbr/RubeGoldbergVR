#!/bin/bash

echo "Dummy Unity Editor invoked with arguments: $@"

# Log file path is usually the last argument or after -logFile
LOG_FILE_ARG_INDEX=-1
PROJECT_PATH_ARG_INDEX=-1
EXECUTE_METHOD_ARG_INDEX=-1

for i in $(seq 1 $#); do
    if [ "${!i}" == "-logFile" ]; then
        LOG_FILE_ARG_INDEX=$((i + 1))
    fi
    if [ "${!i}" == "-projectPath" ]; then
        PROJECT_PATH_ARG_INDEX=$((i + 1))
    fi
    if [ "${!i}" == "-executeMethod" ]; then
        EXECUTE_METHOD_ARG_INDEX=$((i + 1))
    fi
done

LOG_FILE=""
if [ $LOG_FILE_ARG_INDEX -ne -1 ] && [ $LOG_FILE_ARG_INDEX -le $# ]; then
    LOG_FILE="${!LOG_FILE_ARG_INDEX}"
fi

PROJECT_PATH="." # Default to current directory if not specified
if [ $PROJECT_PATH_ARG_INDEX -ne -1 ] && [ $PROJECT_PATH_ARG_INDEX -le $# ]; then
    PROJECT_PATH="${!PROJECT_PATH_ARG_INDEX}"
fi

# Create project directory if -createProject is used
if [[ "$@" == *"-createProject"* ]]; then
    CREATE_PROJECT_PATH_ARG_INDEX=-1
    for i in $(seq 1 $#); do
        if [ "${!i}" == "-createProject" ]; then
            CREATE_PROJECT_PATH_ARG_INDEX=$((i + 1))
            break
        fi
    done
    if [ $CREATE_PROJECT_PATH_ARG_INDEX -ne -1 ] && [ $CREATE_PROJECT_PATH_ARG_INDEX -le $# ]; then
        PROJECT_TO_CREATE="${!CREATE_PROJECT_PATH_ARG_INDEX}"
        echo "Dummy Unity: Creating project at $PROJECT_TO_CREATE"
        mkdir -p "$PROJECT_TO_CREATE/Assets/Editor"
        mkdir -p "$PROJECT_TO_CREATE/Logs" # Also create Logs directory here
        # Create a dummy Library folder to simulate Unity project structure
        mkdir -p "$PROJECT_TO_CREATE/Library"
        # Create a dummy ProjectSettings folder
        mkdir -p "$PROJECT_TO_CREATE/ProjectSettings"
    fi
fi

# Ensure log directory exists
if [ -n "$LOG_FILE" ]; then
    LOG_DIR=$(dirname "$LOG_FILE")
    mkdir -p "$LOG_DIR"
    echo "Dummy Unity: Logging to $LOG_FILE" > "$LOG_FILE"
    echo "Command: $0 $@" >> "$LOG_FILE"
else
    # Default log if no -logFile is provided, common for initial create project
    mkdir -p "$PROJECT_PATH/Logs"
    LOG_FILE="$PROJECT_PATH/Logs/dummy_unity_default.log"
    echo "Dummy Unity: Default logging to $LOG_FILE" > "$LOG_FILE"
    echo "Command: $0 $@" >> "$LOG_FILE"
fi


# Simulate -executeMethod
if [ $EXECUTE_METHOD_ARG_INDEX -ne -1 ] && [ $EXECUTE_METHOD_ARG_INDEX -le $# ]; then
    METHOD_NAME="${!EXECUTE_METHOD_ARG_INDEX}"
    echo "Dummy Unity: Attempting to execute method $METHOD_NAME" >> "$LOG_FILE"
    if [ "$METHOD_NAME" == "JulesBuildAutomation.SetupVRProject" ]; then
        echo "Jules: Starting VR Project Setup..." >> "$LOG_FILE"
        # Simulate creation of Assets/Editor if it doesn't exist from project creation step
        mkdir -p "$PROJECT_PATH/Assets/Editor"
        echo "Jules: Created folder: Assets/Editor" >> "$LOG_FILE" # if it were to create it
        echo "Jules: Attempting to install package: com.unity.xr.interaction.toolkit@2.3.1" >> "$LOG_FILE"
        echo "Jules: Attempting to install package: com.unity.xr.openxr@1.9.0" >> "$LOG_FILE"
        echo "Jules: All XR packages installation requests sent. Now configuring XR Plug-in Management and OpenXR. Please wait for assembly compilation." >> "$LOG_FILE"
        echo "Jules: Starting XR configuration..." >> "$LOG_FILE"
        echo "Jules: Configuring XR for Windows, Mac & Linux..." >> "$LOG_FILE"
        echo "Jules: Added OpenXR Loader to Windows, Mac & Linux XR General Settings." >> "$LOG_FILE"
        echo "Jules: Configuring Windows, Mac & Linux OpenXR settings..." >> "$LOG_FILE"
        echo "Jules: Enabled OpenXR feature: Oculus Touch Controller Profile (ID: com.unity.openxr.features.oculustouchcontroller) for Standalone." >> "$LOG_FILE"
        echo "Jules: Enabled OpenXR feature: Meta Quest Support (ID: com.unity.openxr.features.metarequestsupport) for Standalone." >> "$LOG_FILE"
        echo "Jules: Enabled OpenXR feature: HP Reverb G2 Controller Profile (ID: com.unity.openxr.features.hp_reverb_g2_controller) for Standalone." >> "$LOG_FILE"
        echo "Jules: Configuring XR for Android..." >> "$LOG_FILE"
        echo "Jules: Added OpenXR Loader to Android XR General Settings." >> "$LOG_FILE"
        echo "Jules: Configuring Android OpenXR settings..." >> "$LOG_FILE"
        echo "Jules: Enabled OpenXR feature: Oculus Touch Controller Profile (ID: com.unity.openxr.features.oculustouchcontroller) for Android." >> "$LOG_FILE"
        echo "Jules: Enabled OpenXR feature: Meta Quest Support (ID: com.unity.openxr.features.metarequestsupport) for Android." >> "$LOG_FILE"
        echo "Jules: Enabled OpenXR feature: HP Reverb G2 Controller Profile (ID: com.unity.openxr.features.hp_reverb_g2_controller) for Android." >> "$LOG_FILE"
        echo "Jules: XR configuration complete. Project ready for VR development." >> "$LOG_FILE"
        echo "Jules: Creating basic VR scene elements..." >> "$LOG_FILE"
        # Simulate scene creation/opening
        mkdir -p "$PROJECT_PATH/Assets/Scenes"
        echo "Jules: Created new scene at: Assets/Scenes/SampleScene.unity" >> "$LOG_FILE" # This will create a zero byte file.
        touch "$PROJECT_PATH/Assets/Scenes/SampleScene.unity"

        echo "Jules: Found and removing default Main Camera." >> "$LOG_FILE" # Simulating it finds one
        echo "Jules: Added XR Interaction Manager." >> "$LOG_FILE"
        echo "Jules: Added Left Hand Controller with XRRayInteractor." >> "$LOG_FILE"
        echo "Jules: Added Right Hand Controller with XRDirectInteractor." >> "$LOG_FILE"
        echo "Jules: Basic VR scene elements created and scene saved." >> "$LOG_FILE"
        echo "SetupVRProject completed successfully by dummy script." >> "$LOG_FILE"
    elif [ "$METHOD_NAME" == "JulesBuildAutomation.PerformAlphaTestBuild" ]; then
        echo "Jules: Starting Alpha Test Build..." >> "$LOG_FILE"
        # Simulate finding the scene
        SCENE_PATH="$PROJECT_PATH/Assets/Scenes/SampleScene.unity"
        if [ ! -f "$SCENE_PATH" ]; then
            # This case should ideally not happen if SetupVRProject ran correctly
            echo "Jules: Scene 'Assets/Scenes/SampleScene.unity' not found for build. Please ensure it exists." >> "$LOG_FILE"
            exit 1 # Simulate build failure
        fi
        echo "Jules: Building for Windows Standalone (Alpha Test)..." >> "$LOG_FILE"
        mkdir -p "$PROJECT_PATH/Builds/AlphaTest/Windows"
        echo "Dummy Build Output for Windows" > "$PROJECT_PATH/Builds/AlphaTest/Windows/RubeGoldbergVR.exe"
        echo "Jules: Windows Alpha Test Build succeeded: 12345 bytes at Builds/AlphaTest/Windows/RubeGoldbergVR.exe" >> "$LOG_FILE"

        echo "Jules: Building for Android (Alpha Test for Quest/VR)..." >> "$LOG_FILE"
        mkdir -p "$PROJECT_PATH/Builds/AlphaTest/Android"
        echo "Dummy Build Output for Android" > "$PROJECT_PATH/Builds/AlphaTest/Android/RubeGoldbergVR.apk"
        echo "Jules: Android Alpha Test Build succeeded: 67890 bytes at Builds/AlphaTest/Android/RubeGoldbergVR.apk" >> "$LOG_FILE"
        echo "Jules: All Alpha Test Builds completed successfully." >> "$LOG_FILE"
        echo "PerformAlphaTestBuild completed successfully by dummy script." >> "$LOG_FILE"
    elif [ "$METHOD_NAME" == "JulesBuildAutomation.SetupRubeGoldbergGame" ]; then
        echo "Jules: Starting Rube Goldberg Game Setup..." >> "$LOG_FILE"
        # Simulate CreateBasicVRSceneElements
        echo "Jules: Creating basic VR scene elements..." >> "$LOG_FILE"
        mkdir -p "$PROJECT_PATH/Assets/Scenes"
        touch "$PROJECT_PATH/Assets/Scenes/SampleScene.unity" # Simulate scene creation
        echo "Jules: Created new scene at: Assets/Scenes/SampleScene.unity" >> "$LOG_FILE"
        echo "Jules: Found and removing default Main Camera." >> "$LOG_FILE"
        echo "Jules: Added XR Interaction Manager." >> "$LOG_FILE"
        echo "Jules: Added Left Hand Controller with XRRayInteractor." >> "$LOG_FILE"
        echo "Jules: Added Right Hand Controller with XRDirectInteractor." >> "$LOG_FILE"
        echo "Jules: Basic VR scene elements created and scene saved." >> "$LOG_FILE"

        # Simulate AddInteractablePhysicsObjects
        echo "Jules: Adding interactable physics objects..." >> "$LOG_FILE"
        echo "Jules: Added Interactable_Cube." >> "$LOG_FILE"
        echo "Jules: Added Interactable_Sphere." >> "$LOG_FILE"
        echo "Jules: Added Interactable_Cylinder." >> "$LOG_FILE"
        echo "Jules: Interactable physics objects added to the scene." >> "$LOG_FILE"

        # Simulate CreateRubeGoldbergPrefabs
        echo "Jules: Creating Rube Goldberg prefabs..." >> "$LOG_FILE"
        mkdir -p "$PROJECT_PATH/Assets/RubeGoldbergPrefabs"
        # Simulate creation of dummy prefab files
        touch "$PROJECT_PATH/Assets/RubeGoldbergPrefabs/Ramp.prefab"
        touch "$PROJECT_PATH/Assets/RubeGoldbergPrefabs/Lever.prefab"
        touch "$PROJECT_PATH/Assets/RubeGoldbergPrefabs/Domino.prefab"
        echo "Jules: Created folder: Assets/RubeGoldbergPrefabs" >> "$LOG_FILE"
        echo "Jules: Created Ramp prefab at Assets/RubeGoldbergPrefabs/Ramp.prefab." >> "$LOG_FILE"
        echo "Jules: Added kinematic Rigidbody to Pivot." >> "$LOG_FILE"
        echo "Jules: Configured HingeJoint on Arm, connected to Pivot." >> "$LOG_FILE"
        echo "Jules: Created Lever prefab at Assets/RubeGoldbergPrefabs/Lever.prefab." >> "$LOG_FILE"
        echo "Jules: Created Domino prefab at Assets/RubeGoldbergPrefabs/Domino.prefab." >> "$LOG_FILE"
        echo "Jules: All Rube Goldberg prefabs created." >> "$LOG_FILE"

        echo "JulesBuildAutomation.SetupRubeGoldbergGame completed successfully by dummy script." >> "$LOG_FILE"
        # EditorApplication.Exit(0) is called in C#, so simulate successful exit
    else
        echo "Dummy Unity: Unknown method $METHOD_NAME" >> "$LOG_FILE"
        exit 1 # Simulate error for unknown method
    fi
fi

# Simulate a short delay like a real Unity process might have
sleep 1
echo "Dummy Unity Editor finished." >> "$LOG_FILE"
exit 0
