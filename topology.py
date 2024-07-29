from xmlrpc.server import SimpleXMLRPCServer
import xmlrpc.client


class Topology:
    def __init__(self):
        # node_topology is currently a list of node ids
        # where two consecutive nodes is two consecutive
        # layers in the pipeline
        self.nodes_topology = []
        # self.nodes_metadata_store is a metadata store for the nodes in the topology
        # TODO this will be placed on etcd in the future
        self.nodes_metadata_store = {}

    def get_next_node_id(self, id):
        if self.nodes_metadata_store.index(id) == len(self.nodes_topology) - 1:
            return None
        return self.nodes_topology[self.nodes_topology.index(id) + 1]

    def get_prev_node_id(self, id):
        if self.nodes_metadata_store.index(id) == 0:
            return None
        return self.nodes_topology[self.nodes_topology.index(id) - 1]

    def append(self, id, ip_addr, port):
        # TODO: in the future, we will have to get the node's IP address
        # and port via etcd
        self.nodes_metadata_store[id] = NodeClientInfo(ip_addr, port)
        self.nodes_topology.append(id)

    def remove(self, node_id):
        # TODO: in the future, we will have to get the node's IP address
        # and port via etcd
        self.nodes_metadata_store.pop(node_id)
        self.nodes_topology.remove(node_id)

    def __str__(self):
        for k, v in self.nodes_metadata_store.items():
            print(f"Node ID: {k}, IP Address: {v.get_ip_addr()}, Port: {v.get_port()}")


class NodeClientInfo:
    # TODO: in the future, this class will be
    # stored in etcd
    def __init__(self, ip_addr, port):
        self.ip_addr = ip_addr
        self.port = port

    def get_ip_addr(self):
        return self.ip_addr

    def get_port(self):
        return self.port
