#!/bin/bash

# Function to clean up on exit
cleanup() {
    docker compose -f docker/docker-compose.task.yaml exec -T remdis pkill -f python3
    kill 0
    pkill -f Travel\ Viewer.app
}

trap cleanup INT TERM

docker compose -f docker/docker-compose.task.yaml up -d

# Step 1: Start MMDAgent-EX
../MMDAgent-EX/Release/MMDAgent-EX MMDAgent-EX/task.mdf > /dev/null 2>&1 &

# Step 2: Start input process
./dist/input &

# Step 3: Run dialog system
docker compose -f docker/docker-compose.task.yaml exec -T remdis bash run.sh &

# Step 4: Run Travel Viewer
open -a Travel\ Viewer.app

wait
