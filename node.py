import uuid


class Node:
    def __init__(self, transform, coordinator_client, number_of_active_mini_batches=4):
        self.version = 0
        self.transform = transform
        self.coordinator_client = coordinator_client
        self.id = uuid.uuid5()
        self.topology = self.coordinator_client.node_join(self.id)
        self.number_of_active_mini_batches = number_of_active_mini_batches

    def forward(self, input):
        output = self.transform(input)
        next_node_client = self.topology.get_next_node(self.id)
        if next_node_client is not None:
            next_node_client.forward(output)
        else:
            return output

    def backward(self):
        self.version += 1
        prev_node_client = self.topology.get_prev_node(self.id)
        if prev_node_client is not None:
            prev_node_client.backward()

    def membership_change(self, new_topology):
        self.topology = new_topology
        return self.topology
