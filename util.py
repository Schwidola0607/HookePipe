import random
import hooke_grpc.hooke_pb2 as hooke_pb2
import grpc
from topology.topology import Topology


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
