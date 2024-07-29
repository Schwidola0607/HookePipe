import random
import hooke_pb2
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
        nodes_topology=topology.nodes_topology,
        nodes_metadata_store=topology.nodes_metadata_store,
    )


def protobuf_to_topology(hooke_topology):
    return Topology(
        nodes_topology=hooke_topology.nodes_topology,
        nodes_metadata_store=hooke_topology.nodes_metadata_store,
    )
