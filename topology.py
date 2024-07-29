import hooke_pb2


class Topology:
    def __init__(self, nodes_pipeline=[], nodes_metadata_store={}):
        # node_topology is currently a list of node ids
        # where two consecutive nodes is two consecutive
        # layers in the pipeline
        self.nodes_pipeline = nodes_pipeline
        # self.nodes_metadata_store is a metadata store for the nodes in the topology
        # TODO this will be placed on etcd in the future
        self.nodes_metadata_store = nodes_metadata_store

    def get_next_node_id(self, id):
        if self.nodes_metadata_store.index(id) == len(self.nodes_pipeline) - 1:
            return None
        return self.nodes_pipeline[self.nodes_pipeline.index(id) + 1]

    def get_prev_node_id(self, id):
        if self.nodes_metadata_store.index(id) == 0:
            return None
        return self.nodes_pipeline[self.nodes_pipeline.index(id) - 1]

    def append(self, id, ip_addr, port):
        # TODO: in the future, we will have to get the node's IP address
        # and port via etcd
        self.nodes_metadata_store[id] = hooke_pb2.NodeInfo(
            ip_addr=ip_addr, node_id=id, port=port
        )
        self.nodes_pipeline.append(id)

    def remove(self, node_id):
        # TODO: in the future, we will have to get the node's IP address
        # and port via etcd
        self.nodes_metadata_store.pop(node_id)
        self.nodes_pipeline.remove(node_id)

    def __str__(self):
        ret_str = "Topology:\n"
        for k, v in self.nodes_metadata_store.items():
            ret_str += f"Node ID: {k}, IP Address: {v.ip_addr}, Port: {v.port}\n"
        return ret_str
