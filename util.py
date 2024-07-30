import random
import hooke_pb2
import grpc
from topology import Topology


def get_random_transformer():
    transformations = [
        lambda x: [i * 2 for i in x],  # Double each element
        lambda x: [i**2 for i in x],  # Square each element
        lambda x: [
            i + random.randint(1, 10) for i in x
        ],  # Add a random integer between 1 and 10 to each element
        lambda x: [
            i - random.randint(1, 10) for i in x
        ],  # Subtract a random integer between 1 and 10 from each element
        lambda x: [i / 2 for i in x],  # Divide each element by 2
        lambda x: [-i for i in x],  # Negate each element
        lambda x: [i**0.5 for i in x],  # Square root of each element
    ]
    return random.choice(transformations)


def protobuf_from_topology(topology):
    return hooke_pb2.Topology(
        nodes_pipeline=topology.nodes_pipeline,
        nodes_metadata_store=topology.nodes_metadata_store,
    )


def protobuf_to_topology(hooke_topology):
    return Topology(
        hooke_topology.nodes_pipeline,
        hooke_topology.nodes_metadata_store,
    )


def create_persistent_channel(ip_addr, port):
    # tweak these parameters if needed
    options = [
        # ("grpc.keepalive_time_ms", 10000),
        # ("grpc.keepalive_timeout_ms", 5000),
        # ("grpc.keepalive_permit_without_calls", True),
        # ("grpc.http2.max_pings_without_data", 0),
        # ("grpc.http2.min_time_between_pings_ms", 10000),
        # ("grpc.http2.min_ping_interval_without_data_ms", 5000),
    ]
    channel = grpc.insecure_channel(f"{ip_addr}:{port}", options=options)
    return channel

class IP:
    ADDR = "ip_addr"
    PORT = "port"

class NodeUtil:
    NEXT_NODE_ID = "next_node_id"
    PREV_NODE_ID = "prev_node_id"

    def next_node_endpoint(node_id):
        """
        Returns the endpoint for next_node in etcd.
        """

        return f"nodes/{node_id}/next_node"
    
    def prev_node_endpoint(node_id):
        """
        Returns the endpoint for prev_node in etcd.
        """

        return f"nodes/{node_id}/prev_node"