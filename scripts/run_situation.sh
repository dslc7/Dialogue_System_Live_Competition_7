#!/bin/bash

# Function to clean up on exit
cleanup() {
    docker compose -f docker/docker-compose.prod.yaml exec -T remdis pkill -f run.sh  # Send signal to run.sh
    kill 0
}

trap cleanup INT TERM

docker compose -f docker/docker-compose.prod.yaml up -d

# Step 1: Start MMDAgent-EX
../MMDAgent-EX/Release/MMDAgent-EX MMDAgent-EX/situation.mdf > /dev/null 2>&1 &

# Step 2: Start input process
./dist/input &

# Step 3: Run dialog system
docker compose -f docker/docker-compose.prod.yaml exec -T remdis bash run.sh &

wait
