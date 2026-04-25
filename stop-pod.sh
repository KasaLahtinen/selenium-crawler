#!/bin/bash
set -e

POD_NAME="selenium-crawler-pod"

echo "Stopping and removing pod $POD_NAME..."
podman --cgroup-manager=cgroupfs pod rm -f $POD_NAME

echo "Cleanup complete."
