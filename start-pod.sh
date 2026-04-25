#!/bin/bash
set -e

POD_NAME="selenium-crawler-pod"
SELENIUM_NAME="selenium-chromium"

echo "Creating pod $POD_NAME..."
# Expose 4444 for selenium (optional if accessed from host, but good for debugging)
# Expose 8000 for FastAPI if we later dockerize it. 
# Right now, FastAPI runs on the host and accesses Selenium at localhost:4444
podman --cgroup-manager=cgroupfs pod create --name $POD_NAME -p 4444:4444

echo "Starting Selenium Standalone Chromium container..."
podman --cgroup-manager=cgroupfs run -d --name $SELENIUM_NAME --pod $POD_NAME -v /dev/shm:/dev/shm docker.io/selenium/standalone-chromium:latest

echo "Podman setup complete."
echo "Selenium Grid is accessible at http://localhost:4444"
echo "You can now run the FastAPI backend using: uvicorn main:app --host 0.0.0.0 --port 8000"
