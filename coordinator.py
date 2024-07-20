from xmlrpc.server import SimpleXMLRPCServer
import xmlrpc.client
from topology import Topology


class Coordinator:
    def __init__(self):
        self.topology = Topology()

    def node_join(self, node_id, ip_addr, port):
        print(f"Node {node_id} joined")
        self.topology.append(node_id, ip_addr, port)
        # This should be async in the future
        self.topology.broadcast_new_topology()

    def node_leave(self, node_id):
        print(f"Node {node_id} left")
        self.topology.remove(node_id)
        # This should be async in the future
        self.topology.broadcast_new_topology()


server = SimpleXMLRPCServer(("localhost", 8000), allow_none=True)
server.register_instance(Coordinator())
server.serve_forever()
