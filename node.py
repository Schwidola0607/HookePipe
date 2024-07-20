import uuid
from xmlrpc.server import SimpleXMLRPCServer
import xmlrpc.client
import sys
import numpy as np
from topology import Topology
import random


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


class Node:
    def __init__(
        self,
        transform,
        coordinator_client,
        port,
        number_of_active_mini_batches=4,
        ip_addr="localhost",
    ):
        self.version = 0
        self.transform = transform
        self.coordinator_client = coordinator_client
        url = f"http://localhost:{port}"
        self.id = str(uuid.uuid5(uuid.NAMESPACE_URL, url))
        self.topology = Topology()
        self.coordinator_client.node_join(self.id, ip_addr, port)
        self.number_of_active_mini_batches = number_of_active_mini_batches
        self.ip_addr = ip_addr
        self.port = port

    def forward(self, input):
        output = self.transform(input)
        next_node_client = self.topology.get_next_node(self.id)
        if next_node_client is not None:
            next_node_client.forward(
                output
            )  # TODO: think about underlying communication mechanism
        else:
            return output

    def backward(self):
        self.version += 1
        prev_node_client = self.topology.get_prev_node(self.id)
        if prev_node_client is not None:
            prev_node_client.backward()  # TODO: think about underlying communication mechanism

    # RPC method call by coordinator
    # In the future this  will be called asynchronously
    # or maybe let the RPC server handle the async part
    def membership_change(self, new_topology):
        print(f"New topology for node {self.id}: {new_topology}")
        self.topology = new_topology


coordinator_client = xmlrpc.client.ServerProxy("http://localhost:8000", allow_none=True)
port = int(sys.argv[1])
server = SimpleXMLRPCServer(("localhost", port), allow_none=True)
server.register_instance(Node(get_random_transformer, coordinator_client, port))
server.serve_forever()
