import uuid
import sys
from util import get_random_transformer
import hooke_pb2_grpc
import hooke_pb2
import grpc
from topology import Topology
import util
from concurrent import futures


class NodeServicer(hooke_pb2_grpc.NodeServicer):
    number_of_active_mini_batches = 4

    def __init__(
        self,
        port,
        ip_addr="localhost",
    ):
        self.port = port
        self.ip_addr = ip_addr
        self.version = 0
        self.transform = get_random_transformer()
        self.id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"http://localhost:{port}"))

        self.coordinator_channel = util.create_persistent_channel("localhost", 8080)
        self.coordinator_stub = hooke_pb2_grpc.CoordinatorStub(self.coordinator_channel)
        try:
            self.coordinator_stub.NodeJoin(
                hooke_pb2.NodeInfo(
                    ip_addr=self.ip_addr, node_id=self.id, port=self.port
                )
            )
        except grpc.RpcError as e:
            print(f"Error while joining: {e}")
            raise e

    # RPC method call by coordinator
    def MembershipChanges(self, request, context):
        try:
            topology = util.protobuf_to_topology(request)
            print(f"New topology for node {self.id}: {topology}", flush=True)
            self.topology = topology
            return hooke_pb2.Void()
        except Exception as e:
            print(f"Error while processing new topology: {e}")
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            raise e

    # # TODO this will be called via NCCL / Gloo
    # def forward(self, input):
    #     output = self.transform(input)
    #     self.version += 1
    #     next_id = self.topology.get_next_node_id(self.id)
    #     if next_id is None:
    #         return output
    #     return self.peers[next_id].forward(output)

    # # TODO this will be called via NCCL / Gloo
    # def backward(self):
    #     self.version += 1
    #     prev_id = self.topology.get_prev_node_id(self.id)
    #     if prev_id is None:
    #         return None
    #     return self.peers[prev_id].backward()

    def leave(self):
        try:
            self.coordinator_stub.NodeLeave(
                hooke_pb2.NodeInfo(
                    ip_addr=self.ip_addr, node_id=self.id, port=self.port
                )
            )
        except grpc.RpcError as e:
            print(f"Error while leaving: {e}")
        self.coordinator_channel.close()

    def __str__(self) -> str:
        return f"[Node] id = {self.id}, port = {self.port}"


def serve(port):
    node_server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    hooke_pb2_grpc.add_NodeServicer_to_server(NodeServicer(port), node_server)
    node_server.add_insecure_port(f"[::]:{port}")
    try:
        node_server.start()
        print(f"Node server started at port {port}")
        node_server.wait_for_termination()
    except Exception as e:
        print(f"Node server error: {e}", file=sys.stderr)
        node_server.stop(0)
        exit(1)


if __name__ == "__main__":
    serve(int(sys.argv[1]))
