from xmlrpc.server import SimpleXMLRPCServer
import grpc
from topology import Topology
import hooke_pb2
import util


class CoordinatorServicer(hooke_pb2.CoordinatorServicer):
    def __init__(self):
        self.topology = Topology()
        self.clients = {}

    def NodeJoin(self, request, context):
        node_id = request.node_id
        ip_addr = request.ip_addr
        port = request.port

        print(f"Node {node_id} joined")
        self.topology.append(node_id, ip_addr, port)
        with grpc.insecure_channel(f"{ip_addr}:{port}") as channel:
            self.clients[node_id] = hooke_pb2.NodeStub(channel)

        # This should be async in the future
        self.broadcast_new_topology(node_id)
        response = util.protobuf_from_topology(self.topology)
        return response

    def NodeLeave(self, request, context):
        node_id = request.node_id
        print(f"Node {node_id} left")
        self.topology.remove(node_id)

        # This should be async in the future
        self.broadcast_new_topology(node_id)

    def broadcast_new_topology(self, exclude_node_id=None):
        print("Broadcasting new topology")
        topology = util.protobuf_from_topology(self.topology)
        for node_id in self.clients:
            if node_id != exclude_node_id:
                self.clients[node_id].MembershipChanges(topology)


def serve(port="8080"):
    coordinator_server = grpc.server(grpc.ThreadPoolExecutor(max_workers=10))
    hooke_pb2.add_CoordinatorServicer_to_server(
        CoordinatorServicer(), coordinator_server
    )
    coordinator_server.add_insecure_port(f"[::]:{port}")
    coordinator_server.start()
    coordinator_server.wait_for_termination()


if __name__ == "__main__":
    serve()
