import hooke_pb2
import xmlrpc.client
import etcd3
import json
import network
import utils
import logging

class Topology:
    def __init__(self, etcd_host, etcd_port, addr, nodes_pipeline=[], nodes_metadata_store={}):
        # node_topology is currently a list of node ids
        # where two consecutive nodes is two consecutive
        # layers in the pipeline
        self.nodes_pipeline = nodes_pipeline
        # self.nodes_metadata_store is a metadata store for the nodes in the topology
        # TODO this will be placed on etcd in the future
        self.nodes_metadata_store = nodes_metadata_store

        # self.etcd is an inbuilt database for node metadata
        self.etcd = etcd3.client(host=etcd_host, port=etcd_port)

        # self.addr is just the address for nodes - e.g. localhost
        # assumes every node will have the same address - unsure if safe assumption
        self.addr = addr

        # use logging instead of print statements
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    # def get_next_node_id(self, id):
    #     if self.nodes_metadata_store.index(id) == len(self.nodes_pipeline) - 1:
    #         return None
    #     return self.nodes_pipeline[self.nodes_pipeline.index(id) + 1]

    def get_next_node(self, node_id):
        """
        Gets the ServerProxy client for the next node.
        """
        if node_id >= len(self.nodes_topology) - 1:
            return None
        
        next_id = node_id + 1

        metadata = self.get_node_metadata(next_id)

        if (not metadata) or (utils.IP.ADDR not in metadata) or (utils.IP.PORT not in metadata):
            return None

        # returns a new server proxy every time.
        # we may want to use the same one in the future - server proxies are not threadsafe though
        return xmlrpc.client.ServerProxy(
            f"http://{metadata[utils.IP.ADDR]}:{int(metadata[utils.IP.PORT])}", allow_none=True
        )

    # def get_prev_node_id(self, id):
    #     if self.nodes_metadata_store.index(id) == 0:
    #         return None
    #     return self.nodes_pipeline[self.nodes_pipeline.index(id) - 1]
    
    def get_prev_node(self, node_id):
        """
        Gets the ServerProxy client for the previous node.
        """
        if node_id >= len(self.nodes_topology) - 1:
            return None
        
        next_id = node_id - 1

        metadata = self.get_node_metadata(next_id)

        if (not metadata) or (utils.IP.ADDR not in metadata) or (utils.IP.PORT not in metadata):
            return None

        # returns a new server proxy every time.
        # we may want to use the same one in the future - server proxies are not threadsafe though
        return xmlrpc.client.ServerProxy(
            f"http://{metadata[utils.IP.ADDR]}:{int(metadata[utils.IP.PORT])}", allow_none=True
        )

    # def append(self, id, ip_addr, port):
    #     # TODO: in the future, we will have to get the node's IP address
    #     # and port via etcd
    #     self.nodes_metadata_store[id] = hooke_pb2.NodeInfo(
    #         ip_addr=ip_addr, node_id=id, port=port
    #     )
    #     self.nodes_pipeline.append(id)

    def append(self, node_id):
        """
        Adds a node to the topology and assigns it a port, stored in etcd.
        """
        metadata, _ = self.etcd.get(f"nodes/{node_id}/metadata")

        # checks if node already exists
        if metadata:
            metadata = json.loads(metadata.decode('utf-8'))
            
            ip_addr = metadata.get(utils.IP.ADDR)
            port = metadata.get(utils.IP.PORT)

            if ip_addr and port:
                self.logger.info("Node already exists with addr %s and port %s", ip_addr, port)
                return

        # finds available port and creates metadata
        port = network.find_available_port(self.addr)

        if port == -1:
            # TODO: handle the case where there's no open ports?
            return
        
        new_metadata = {utils.IP.ADDR: self.addr, utils.IP.PORT: port}

        # adds metadata to etcd/node topology
        self.etcd.put(f"nodes/{node_id}/metadata", json.dumps(new_metadata))
        self.nodes_topology.append(node_id)
    
    

    def remove(self, node_id):
        """
        Removes a node and all its metadata from the topology.
        """
        self.nodes_topology.remove(node_id)
        removed = self.etcd.delete_prefix(f"nodes/{node_id}")

        if removed:
            self.logger.info("Deleted node %s from topology and memory.", node_id)
        else:
            self.logger.error("Error deleting node data from memory. Deleted node %s from topology.", node_id)

    # def remove(self, node_id):
    #     # TODO: in the future, we will have to get the node's IP address
    #     # and port via etcd
    #     self.nodes_metadata_store.pop(node_id)
    #     self.nodes_pipeline.remove(node_id)

    def __str__(self):
        ret_str = "Topology:\n"
        for k, v in self.nodes_metadata_store.items():
            ret_str += f"Node ID: {k}, IP Address: {v.ip_addr}, Port: {v.port}\n"
        return ret_str
        

    def get_node_metadata(self, node_id):
        """
        Returns node metadata as a dict if it exists. If it doesn't, returns None.
        """
        metadata, _ = self.etcd.get(f"nodes/{node_id}/metadata")
        if metadata:
            return json.loads(metadata.decode('utf-8'))
        return None
    
    def broadcast_new_topology(self, node_id):
        for k, v in self.nodes_metadata_store.items():
            if k == node_id:
                continue
            print(
                f"[broadcast_new_topology] Node ID: {k}, IP Address: {v.get_ip_addr()}, Port: {v.get_port()}"
            )
        for node_id in self.nodes_topology:
            # self.nodes_metadata_store[node_id].client.membership_change(self)
            # TODO: handle topology change
            print(node_id)

    # def __str__(self):
    #     for k, v in self.nodes_metadata_store.items():
    #         print(f"Node ID: {k}, IP Address: {v.get_ip_addr()}, Port: {v.get_port()}")
