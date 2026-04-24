#!/bin/bash

# Build and deploy the auto-scaler
echo "Building and deploying the auto-scaler is started."

docker build -t swarm-autoscaler:v1.0 . --no-cache

docker service rm autoscaler

touch $HOME/swarm-auto-scaler/scaler/scaler.log

docker service create \
  --name autoscaler \
  --mount type=bind,source=/var/run/docker.sock,target=/var/run/docker.sock \
  --mount type=bind,source=$HOME/swarm-auto-scaler/scaler/scaler.log,target=/app/scaler.log \
  --network monitoring_monitoring \
  --constraint 'node.role == manager' \
  --replicas 1 \
  swarm-autoscaler:v1.0

echo "Building and deploying the auto-scaler is done."
