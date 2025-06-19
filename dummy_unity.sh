#!/bin/bash
echo "Dummy Unity Editor invoked with: $@"

# Simulate project creation success
if [[ "$@" == *"-createProject"* ]]; then
  echo "Simulating project creation..."
  # The project path is the last argument.
  PROJECT_PATH="${@: -1}"
  # Remove quotes if any
  PROJECT_PATH_NO_QUOTES=$(echo ${PROJECT_PATH} | sed 's/"//g')

  # Ensure the base directory for the project path exists if it's nested
  # e.g. if PROJECT_PATH_NO_QUOTES is /app/RubeGoldbergVR, /app must exist.
  # In this sandbox, /app is the root and always exists.

  echo "Attempting to create directory: ${PROJECT_PATH_NO_QUOTES}"
  mkdir -p "${PROJECT_PATH_NO_QUOTES}"

  if [ -d "${PROJECT_PATH_NO_QUOTES}" ]; then
    echo "Simulated project directory created at ${PROJECT_PATH_NO_QUOTES}"
    exit 0
  else
    echo "Error: Failed to create directory ${PROJECT_PATH_NO_QUOTES}"
    exit 1
  fi
fi

# Simulate executeMethod success
if [[ "$@" == *"-executeMethod"* ]]; then
  echo "Simulating method execution for: $@"
  # Potentially grab -projectPath argument
  PROJECT_PATH_ARG=""
  for i in "${!BASH_ARGV[@]}"; do
    if [[ "${BASH_ARGV[$i]}" == "-projectPath" ]]; then
      PROJECT_PATH_ARG="${BASH_ARGV[$((i-1))]}"
      break
    fi
  done
  # Remove quotes if any
  PROJECT_PATH_ARG_NO_QUOTES=$(echo ${PROJECT_PATH_ARG} | sed 's/"//g')


  LOG_FILE_ARG=""
   for i in "${!BASH_ARGV[@]}"; do
    if [[ "${BASH_ARGV[$i]}" == "-logFile" ]]; then
      LOG_FILE_ARG="${BASH_ARGV[$((i-1))]}"
      break
    fi
  done
  LOG_FILE_ARG_NO_QUOTES=$(echo ${LOG_FILE_ARG} | sed 's/"//g')

  if [ ! -z "$LOG_FILE_ARG_NO_QUOTES" ]; then
    echo "Logging to ${LOG_FILE_ARG_NO_QUOTES}"
    # Ensure directory for log file exists
    mkdir -p "$(dirname "${LOG_FILE_ARG_NO_QUOTES}")"
    echo "Dummy Unity log for method execution: $@" > "${LOG_FILE_ARG_NO_QUOTES}"
  else
     echo "No logFile specified."
  fi

  # Check if project path exists, as a real Unity editor would
  if [ ! -z "${PROJECT_PATH_ARG_NO_QUOTES}" ] && [ ! -d "${PROJECT_PATH_ARG_NO_QUOTES}" ]; then
    echo "Error: Project path ${PROJECT_PATH_ARG_NO_QUOTES} does not exist."
    exit 1 # Or a specific Unity error code
  fi

  exit 0
fi

echo "Dummy Unity: No matching arguments for specific actions."
exit 0
