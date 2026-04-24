#!/bin/bash

# Build and deploy the auto-scaler
echo "Building and deploying the auto-scaler is started."

docker build -t swarm-autoscaler:v1.0 . --no-cache

docker service rm autoscaler

docker service create \
  --name autoscaler \
  --mount type=bind,source=/var/run/docker.sock,target=/var/run/docker.sock \
  --mount type=bind,source=/tmp/scaler.log,target=/app/scaler.log \
  --network monitoring_monitoring \
  --constraint 'node.role == manager' \
  --replicas 1 \
  swarm-autoscaler:v1.0

echo "Building and deploying the auto-scaler is done."
