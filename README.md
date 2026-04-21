# Introduction

This project is used to build and deploy automatic service scaler in the Docker Swarm Cluster.

# Prerequisite

The Docker Swarm Cluster are deployed.

# Usage

1. Running the `docker stack deploy -c monitoring-stack.yml monitoring` command to deploy the Prometheus as a monitoring system in the Docker Swarm Manager.
2. Running the `cd scaler/` command then execute the `./deploy.sh` script to deploy the automatic service scaler in the Docker Swamr Manager.
3. Happy Scaling!
