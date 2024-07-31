import grpc
from topology import Topology
import hooke_pb2_grpc
import util
from concurrent import futures
import sys
import os
import fcntl

# design doc
# https://lucid.app/lucidspark/2a727cdb-ee2a-47af-97a8-6964fba8edd5/edit?invitationId=inv_273daa92-8b0e-4455-9305-3dd94411eec3&page=0_0#

class CoordinatorServicer(hooke_pb2_grpc.CoordinatorServicer):
    def __init__(self):
        self.topology = Topology()
        self.clients = {}  # node_id -> NodeStub
        self.channels = {}  # node_id -> channel

    def NodeJoin(self, request, context):
        node_id = request.node_id
        ip_addr = request.ip_addr
        port = request.port

        print(f"Node {node_id} joined")
        self.topology.append(node_id, ip_addr, port)
        self.channels[node_id] = util.create_persistent_channel(ip_addr, port)
        self.clients[node_id] = hooke_pb2_grpc.NodeStub(self.channels[node_id])

        # This should be async in the future
        try:
            self.broadcast_new_topology(node_id)
        except grpc.RpcError as e:
            print(f"Error while broadcasting topology: {e}")
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            raise e

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
                print("Broadcasting to", node_id)
                try:
                    self.clients[node_id].MembershipChanges(topology)
                except grpc.RpcError as e:
                    print(f"Error while broadcasting topology to {node_id}: {e}")
                    raise e
                print("Broadcasted to", node_id)
        print("Broadcasting done")

    def close(self):
        print("Closing all channels")
        for node_id in self.clients:
            self.channels[node_id].close()


def serve(port="8080"):
    coordinator_server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    hooke_pb2_grpc.add_CoordinatorServicer_to_server(
        CoordinatorServicer(), coordinator_server
    )
    coordinator_server.add_insecure_port(f"[::]:{port}")
    try:
        coordinator_server.start()
        # notify()
        print(f"Coordinator started at port {port}")
        coordinator_server.wait_for_termination()
    except Exception as e:
        print(f"Coordinator error: {e}", file=sys.stderr)
        coordinator_server.stop(0)
        exit(1)


def notify():
    pipe_path = os.getenv("COORDINATOR_PIPE_PATH", "./tmp/coordinator_pipe")
    if not os.path.exists(pipe_path):
        os.mkfifo(pipe_path)
    with open(pipe_path, "w") as pipe:
        fd = pipe.fileno()
        flags = fcntl.fcntl(fd, fcntl.F_GETFL)
        fcntl.fcntl(fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)
        payload = f"COORDINATOR"
        os.write(fd, payload.encode())


if __name__ == "__main__":
    serve()
