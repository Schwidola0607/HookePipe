#!/bin/bash
# Script to start node.py up to argv[1] times with ports starting from 8000

# Ensure the script exits if any command fails
# set -e
mkdir -p ./tmp
pipe_path="./tmp/coordinator_pipe"
export COORDINATOR_PIPE_PATH=$pipe_path

# Start coordinator.py at 8080
echo "Starting coordinator.py"
python "coordinator.py" &

# Wait for coordinator to start
read line < "$pipe_path";
echo $line

# Maximum number of instances to start
num_nodes=$1

# Starting port number
start_port=8000

# Loop through the range and start node.py with different ports
echo "Starting $num_nodes nodes"
for ((i=0; i<num_nodes; i++)); do
    port=$((start_port + i))
    python "node.py" $port &
done

# Wait for all background processes to finish
wait
