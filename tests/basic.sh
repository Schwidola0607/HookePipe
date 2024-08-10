#!/bin/bash
# Script to start node.py up to argv[1] times with ports starting from 8000

# Ensure the script exits if any command fails
# set -e
mkdir -p ./tmp
pipe_path="./tmp/coordinator_pipe"
export COORDINATOR_PIPE_PATH=$pipe_path


nodes_pids=()
# Start coordinator.py at 8080
echo "Starting coordinator.py"
python "coordinator.py" &
coordinator_pid=$!
echo $coordinator_pid

# Wait for coordinator to start
read line < "$pipe_path";
echo $line

# Maximum number of instances to start
num_nodes=$1

# Starting port number
start_port=8000

# Loop through the range and start node.py with different ports
echo "Test with $num_nodes nodes"
for ((i=0; i<num_nodes; i++)); do
    echo starting node $i
    python "node.py" &
    nodes_pids+=($!)
    # Why do we need to sleep here?
    sleep 1
done


# Wait for ctrl-c
trap cleanup SIGINT

cleanup() {
    echo "Caught Ctrl-C (SIGINT)! Killing all processes started by test."
    # Kill the coordinator
    kill $coordinator_pid

    # Kill all the nodes
    for pid in "${nodes_pids[@]}"; do
        kill $pid
    done

    # Remove the pipe
    rm $pipe_path

    # Remove the tmp directory
    rm -rf ./tmp

    # Exit with success
    exit 0
    exit 1
}

# Wait for all background processes to finish
wait