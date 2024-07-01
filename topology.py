class Topology:
    def __init__(self, nodes):
        self.nodes = nodes

    def get_next_node(self, node_id):
        pass

    def get_prev_node(self, node_id):
        pass

    def append(self, node_id):
        self.nodes.append(node_id)

    def remove(self, node_id):
        self.nodes.remove(node_id)
