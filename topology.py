import hooke_pb2
import xmlrpc.client
import etcd3
import json
import network
import util
import logging

class Topology:
    def __init__(self, etcd_host, etcd_port, addr, nodes_pipeline=[]):
        # node_topology is currently a list of node ids
        # where two consecutive nodes is two consecutive
        # layers in the pipeline
        self.nodes_pipeline = nodes_pipeline

        # self.etcd is the inbuilt database connection for node metadata
        self.etcd = etcd3.client(host=etcd_host, port=etcd_port)

        # self.addr is just the address for nodes - e.g. localhost
        # assumes every node will have the same address - unsure if safe assumption
        self.addr = addr

        # use logging instead of print statements
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def get_next_node_id(self, node_id):
        """
        Gets the id for the next node. Returns -1 if it doesn't exist.
        """
        if node_id >= len(self.nodes_topology) - 1:
            return -1

        next_node = self.etcd.get(f"nodes/{node_id}/next_node")

        if not next_node:
            return -1
        
        return int(next_node)
    
    def get_prev_node(self, node_id):
        """
        Gets the id for the previous node. Returns -1 if it doesn't exist.
        """
        if node_id == 0:
            return -1

        prev_node = self.etcd.get(f"nodes/{node_id}/prev_node")

        if not prev_node:
            return -1
        
        return int(prev_node)
        
    def append(self, node_id):
        """
        Adds a node to the topology and assigns it a port, stored in etcd. Also updates next_node for the previous node.
        """
        prev_node = self.nodes_pipeline[-1] if self.nodes_pipeline else -1
        port = network.find_available_port(self.addr)

        if port == -1:
            # TODO: handle the case where there's no open ports
            return
        
        new_metadata = {
            util.IP.ADDR: self.addr, 
            util.IP.PORT: port, 
        }

        self.etcd.put(f"nodes/{node_id}/metadata", json.dumps(new_metadata))
        self.etcd.put(f"nodes/{node_id}/next_node", -1)
        self.etcd.put(f"nodes/{node_id}/prev_node", prev_node)

        self.nodes_pipeline.append(node_id)

        # updates prev_node metadata if it exists
        if prev_node != -1:
            self.etcd.put(f"nodes/{prev_node}/next_node", node_id)
    
    def remove(self, node_id):
        """
        Removes a node and all its metadata from the topology. Also updates the next_node for its previous node/prev_node for the next node.
        """

        # updates the "linked list" in the prev_node and next_node metadata in etcd.
        try:
            prev_node = self.etcd.get(f"nodes/{node_id}/prev_node")
            next_node = self.etcd.get(f"nodes/{node_id}/next_node")
            
            prev_node_id = int(prev_node) if prev_node else -1
            next_node_id = int(next_node) if next_node else -1

            if prev_node_id > -1:
                self.etcd.put(f"nodes/{prev_node_id}/next_node", next_node)

            if next_node_id > -1:
                self.etcd.put(f"nodes/{next_node_id}/prev_node", prev_node)

        except Exception as e:
            self.logger.error("Unable to update next_node data for previous node of %s: %s", node_id, e)

        # removes node from pipeline and etcd
        self.nodes_pipeline.remove(node_id)
        removed = self.etcd.delete_prefix(f"nodes/{node_id}")

        if removed:
            self.logger.info("Deleted node %s from topology and memory.", node_id)
        else:
            self.logger.error("Error deleting node data from memory. Deleted node %s from topology.", node_id)

    # def __str__(self):
    #     ret_str = "Topology:\n"
    #     for k, v in self.nodes_metadata_store.items():
    #         ret_str += f"Node ID: {k}, IP Address: {v.ip_addr}, Port: {v.port}\n"
    #     return ret_str
        

    def get_node_metadata(self, node_id):
        """
        Returns node metadata as a dict if it exists. If it doesn't, returns None.
        """
        metadata, _ = self.etcd.get(f"nodes/{node_id}/metadata")
        if metadata:
            return json.loads(metadata.decode('utf-8'))
        return None
    
    # def broadcast_new_topology(self, node_id):
    #     for k, v in self.nodes_metadata_store.items():
    #         if k == node_id:
    #             continue
    #         print(
    #             f"[broadcast_new_topology] Node ID: {k}, IP Address: {v.get_ip_addr()}, Port: {v.get_port()}"
    #         )
    #     for node_id in self.nodes_topology:
    #         # self.nodes_metadata_store[node_id].client.membership_change(self)
    #         # TODO: handle topology change
    #         print(node_id)
