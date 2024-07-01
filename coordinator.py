class Coordinator:
    def __init__():
        pass

    def node_join(self, node_id):
        self.topology.append(node_id)
        return self.topology

    def node_leave(self, node_id):
        self.topology.remove(node_id)
        return self.topology
