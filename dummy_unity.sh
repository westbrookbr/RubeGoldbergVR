#!/bin/bash

# dummy_unity.sh
# This script mimics the Unity Editor CLI behavior for testing purposes.
# It logs arguments and creates placeholder files/directories.

LOG_FILE="/dev/null" # Default log file if -logFile is not provided
PROJECT_PATH="."     # Default project path to current directory if not specified
EXECUTE_METHOD=""
UNITY_VERSION_ARG=""
CREATE_PROJECT_FLAG=false

# Parse arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        -quit) QUIT_FLAG=true; ;; # Not actively used but parsed
        -batchmode) BATCHMODE_FLAG=true; ;; # Not actively used but parsed
        -nographics) NOGRAPHICS_FLAG=true; ;; # Not actively used but parsed
        -createProject) CREATE_PROJECT_FLAG=true; PROJECT_PATH="$2"; shift ;;
        -projectPath) PROJECT_PATH="$2"; shift ;;
        -executeMethod) EXECUTE_METHOD="$2"; shift ;;
        -logFile) LOG_FILE="$2"; shift ;;
        -version) UNITY_VERSION_ARG="$2"; shift ;; # Capture Unity version
        *) echo "Unknown parameter passed: $1"; ;; # Optionally log unknown params
    esac
    shift # Shift to next argument
done

# Ensure the log directory exists if a log file is specified
if [ "$LOG_FILE" != "/dev/null" ] && [ -n "$LOG_FILE" ]; then
    LOG_DIR=$(dirname "$LOG_FILE")
    mkdir -p "$LOG_DIR"
fi

# Append to log file instead of overwriting with '>>'
echo "--- Dummy Unity Editor CLI Invoked ---" >> "$LOG_FILE"
# Log all received arguments for clarity
# This needs to be done carefully if arguments were processed above.
# For simplicity, we'll just log the key parsed values.
echo "Timestamp: $(date)" >> "$LOG_FILE"
echo "Raw Arguments: $@" >> "$LOG_FILE" # Note: this will be empty if all args were shifted
echo "Parsed Project Path: $PROJECT_PATH" >> "$LOG_FILE"
echo "Parsed Execute Method: $EXECUTE_METHOD" >> "$LOG_FILE"
echo "Parsed Log File: $LOG_FILE" >> "$LOG_FILE"
echo "Parsed Unity Version: $UNITY_VERSION_ARG" >> "$LOG_FILE"
echo "Create Project Flag: $CREATE_PROJECT_FLAG" >> "$LOG_FILE"


# Simulate project creation if -createProject was passed
if [ "$CREATE_PROJECT_FLAG" = true ] && [ -n "$PROJECT_PATH" ]; then
  echo "Simulating project creation at $PROJECT_PATH with version $UNITY_VERSION_ARG..." >> "$LOG_FILE"
  mkdir -p "$PROJECT_PATH"
  mkdir -p "$PROJECT_PATH/Assets"
  mkdir -p "$PROJECT_PATH/ProjectSettings"
  mkdir -p "$PROJECT_PATH/Logs" # Ensure Logs directory is created within the project
  touch "$PROJECT_PATH/ProjectSettings/ProjectSettings.asset"
  echo "Unity project structure simulated at '$PROJECT_PATH'." >> "$LOG_FILE"
fi

# Simulate script deployment (assuming it's copied to Assets/Editor already by Python)
# This part is more about acknowledging the structure Unity would expect.
if [ -n "$PROJECT_PATH" ]; then
    EDITOR_DIR="$PROJECT_PATH/Assets/Editor"
    mkdir -p "$EDITOR_DIR"
    # The Python script is responsible for copying JulesBuildAutomation.cs.
    # This dummy script can just acknowledge its expected presence if needed for logs.
    if [ -f "$EDITOR_DIR/JulesBuildAutomation.cs" ]; then
        echo "JulesBuildAutomation.cs found in $EDITOR_DIR." >> "$LOG_FILE"
    else
        echo "JulesBuildAutomation.cs NOT found in $EDITOR_DIR (this might be okay if it's not deployed yet)." >> "$LOG_FILE"
    fi
fi


# Simulate -executeMethod calls
if [ -n "$EXECUTE_METHOD" ]; then
  echo "Simulating Unity Editor executing method: $EXECUTE_METHOD on project: $PROJECT_PATH" >> "$LOG_FILE"

  # Common directories that might be created or expected by the C# script
  SCENES_DIR="$PROJECT_PATH/Assets/Scenes"
  PREFABS_DIR="$PROJECT_PATH/Assets/RubeGoldbergPrefabs"

  if [ "$EXECUTE_METHOD" == "JulesBuildAutomation.SetupVRProject" ]; then
    echo "Simulating JulesBuildAutomation.SetupVRProject execution..." >> "$LOG_FILE"
    mkdir -p "$PROJECT_PATH/Assets/Editor" # Ensure Editor folder
    echo "Simulated XR package installation requests (logged)." >> "$LOG_FILE"
    echo "Simulated XR configuration (logged)." >> "$LOG_FILE"
    echo "SetupVRProject simulation finished." >> "$LOG_FILE"

  elif [ "$EXECUTE_METHOD" == "JulesBuildAutomation.SetupRubeGoldbergGame" ]; then
    echo "Simulating JulesBuildAutomation.SetupRubeGoldbergGame execution..." >> "$LOG_FILE"

    # Simulate scene creation/opening
    mkdir -p "$SCENES_DIR"
    touch "$SCENES_DIR/SampleScene.unity"
    echo "Simulated creation/opening of SampleScene.unity in $SCENES_DIR" >> "$LOG_FILE"

    # Simulate basic VR scene elements (logging)
    echo "Simulated creation of XR Origin, Main Camera, Controllers, Ground Plane." >> "$LOG_FILE"

    # Simulate interactable physics objects (logging)
    echo "Simulated adding of Interactable_Cube, Interactable_Sphere, Interactable_Cylinder." >> "$LOG_FILE"

    # Simulate Rube Goldberg prefab creation
    mkdir -p "$PREFABS_DIR"
    touch "$PREFABS_DIR/Ramp.prefab"
    touch "$PREFABS_DIR/Lever.prefab"
    touch "$PREFABS_DIR/Domino.prefab"
    echo "Simulated creation of Rube Goldberg prefabs in $PREFABS_DIR." >> "$LOG_FILE"
    echo "SetupRubeGoldbergGame simulation finished." >> "$LOG_FILE"

  elif [ "$EXECUTE_METHOD" == "JulesBuildAutomation.PerformAlphaTestBuild" ]; then
    echo "Simulating JulesBuildAutomation.PerformAlphaTestBuild execution..." >> "$LOG_FILE"
    mkdir -p "$PROJECT_PATH/Builds/AlphaTest/Windows"
    mkdir -p "$PROJECT_PATH/Builds/AlphaTest/Android"
    touch "$PROJECT_PATH/Builds/AlphaTest/Windows/RubeGoldbergVR.exe" # Dummy exe
    touch "$PROJECT_PATH/Builds/AlphaTest/Android/RubeGoldbergVR.apk" # Dummy apk
    echo "Simulated Alpha Test builds for Windows and Android." >> "$LOG_FILE"
    echo "PerformAlphaTestBuild simulation finished." >> "$LOG_FILE"
  else
    echo "Unknown method to execute: $EXECUTE_METHOD" >> "$LOG_FILE"
  fi
fi

echo "Dummy Unity Editor finished operations." >> "$LOG_FILE"
exit 0 # Important to exit with 0 for success
