# import hooke_pb2
import etcd3
import json
import network
import etcd_utils
import logging

class Topology:
    def __init__(self, etcd_host, etcd_port, addr, nodes_pipeline=[]):
        # node_topology is currently a list of node ids
        # where two consecutive nodes is two consecutive
        # layers in the pipeline
        self.nodes_pipeline = nodes_pipeline
        # self.etcd is the inbuilt database connection for node metadata
        self.etcd_client = etcd3.client(host=etcd_host, port=etcd_port)

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
        if node_id >= len(self.nodes_pipeline) - 1:
            return -1
        
        try:
            next_node = self.etcd_client.get(f"nodes/{node_id}/next_node")

            if not next_node or not next_node[0]:
                return -1
            
            return int(next_node[0])
        
        except Exception as e:
            self.logger.error("Error getting next node id for node %s: %s", node_id, e)
            return -1
    
    def get_prev_node(self, node_id):
        """
        Gets the id for the previous node. Returns -1 if it doesn't exist.
        """
        if node_id == 0:
            return -1

        try:
            prev_node = self.etcd_client.get(f"nodes/{node_id}/prev_node")

            if not prev_node or not prev_node[0]:
                return -1
        
            return int(prev_node[0])
        
        except Exception as e:
            self.logger.error("Error getting previous node id for node %s: %s", node_id, e)
            return -1
        
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
            etcd_utils.IP.ADDR: self.addr, 
            etcd_utils.IP.PORT: port, 
        }

        try:
            self.etcd_client.put(f"nodes/{node_id}/metadata", json.dumps(new_metadata))
            self.etcd_client.put(f"nodes/{node_id}/next_node", str(-1))
            self.etcd_client.put(f"nodes/{node_id}/prev_node", str(prev_node))
            self.nodes_pipeline.append(node_id)

            # updates prev_node metadata if it exists
            if prev_node != -1:
                self.etcd_client.put(f"nodes/{prev_node}/next_node", str(node_id))

            self.logger.info("Appended node %s at port %s", node_id, port)

        except Exception as e:
            self.logger.error("error appending node %s, error %s", node_id, e)
            return
        
    
    def remove(self, node_id):
        """
        Removes a node and all its metadata from the topology. Also updates the next_node for its previous node/prev_node for the next node.
        """

        # updates the "linked list" in the prev_node and next_node metadata in etcd.
        try:
            prev_node = self.etcd_client.get(f"nodes/{node_id}/prev_node")
            next_node = self.etcd_client.get(f"nodes/{node_id}/next_node")
            
            prev_node_id = int(prev_node[0]) if prev_node[0] else -1
            next_node_id = int(next_node[0]) if next_node[0] else -1

            if prev_node_id > -1:
                self.etcd_client.put(f"nodes/{prev_node_id}/next_node", str(next_node))

            if next_node_id > -1:
                self.etcd_client.put(f"nodes/{next_node_id}/prev_node", str(prev_node))

            # removes node from pipeline and etcd
            self.nodes_pipeline.remove(node_id)
            self.etcd_client.delete(f"nodes/{node_id}",dir=True)

            self.logger.info("Deleted node %s from topology and memory.", node_id)

        except Exception as e:
            self.logger.error("Unable to remove node %s: %s", node_id, e)

        
    def __str__(self):
        ret_str = "Topology:\n"
        for node_id in self.nodes_pipeline:
            node_metadata = self.get_node_metadata(node_id)
            if not node_metadata:
                ret_str += f"Node ID: {node_id}: Error getting metadata\n"
                continue
            ret_str += f"Node ID: {node_id}, IP Address: {node_metadata.get(etcd_utils.IP.ADDR, "")}, Port: {node_metadata.get(etcd_utils.IP.PORT, "")}\n"
        
        return ret_str
        

    def get_node_metadata(self, node_id):
        """
        Returns node metadata as a dict if it exists. If it doesn't, returns None.
        """
        metadata, _ = self.etcd_client.get(f"nodes/{node_id}/metadata")
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

t = Topology("localhost", 64629, "localhost")
t.append(0)
t.append(1)
# print(t.get_next_node_id(0))
print(t)
