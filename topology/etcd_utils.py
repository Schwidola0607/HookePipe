class IP:
    ADDR = "ip_addr"
    PORT = "port"

class NodeUtil:
    NEXT_NODE_ID = "next_node_id"
    PREV_NODE_ID = "prev_node_id"

    def next_node_endpoint(node_id):
        """
        Returns the endpoint for next_node in etcd.
        """

        return f"nodes/{node_id}/next_node"
    
    def prev_node_endpoint(node_id):
        """
        Returns the endpoint for prev_node in etcd.
        """

        return f"nodes/{node_id}/prev_node"