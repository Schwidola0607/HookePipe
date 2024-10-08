import grpc
from topology.topology import Topology
import hooke_grpc.hooke_pb2 as hooke_pb2
import hooke_grpc.hooke_pb2_grpc as hooke_pb2_grpc
import util
from concurrent import futures
import sys
import os
import fcntl
from logconfig import colors
import etcd3
# design doc
# https://lucid.app/lucidspark/2a727cdb-ee2a-47af-97a8-6964fba8edd5/edit?invitationId=inv_273daa92-8b0e-4455-9305-3dd94411eec3&page=0_0#


class CoordinatorServicer(hooke_pb2_grpc.CoordinatorServicer):
    def __init__(
        self,
        etcd_port=23790,
        etcd_host="localhost",
    ):
        etcd_client = etcd3.client(host=etcd_host, port=etcd_port)
        self.topology = Topology(etcd_client=etcd_client)
        self.clients = {}  # node_id -> NodeStub
        self.channels = {}  # node_id -> Channel
        self.logger = colors.get_logger("coordinator_logger")

    def NodeJoin(self, request, context):
        node_id = request.node_id
        node_host = request.host
        node_port = request.port

        self.logger.info(f"Node {node_id} joined")
        self.topology.append(node_id)
        self.channels[node_id] = util.create_persistent_channel(node_host, node_port)
        self.clients[node_id] = hooke_pb2_grpc.NodeStub(self.channels[node_id])

        # This should be async in the future
        try:
            self.broadcast_new_topology(node_id)
        except grpc.RpcError as e:
            self.logger.error(f"Error while broadcasting topology: {e}")
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            raise e

        response = hooke_pb2.NeighborInfo(
            next_node_id=self.topology.get_next_node_id(node_id),
            prev_node_id=self.topology.get_prev_node_id(node_id),
        )
        return response

    def NodeLeave(self, request, context):
        node_id = request.node_id
        self.logger.info(f"Node {node_id} left")
        self.topology.remove(node_id)

        # This should be async in the future
        self.broadcast_new_topology(node_id)

    def broadcast_new_topology(self, exclude_node_id=None):
        self.logger.info("Broadcasting new neighbor info")
        for node_id in self.clients:
            if node_id != exclude_node_id:
                self.logger.info(f"Sending neighbor info to {node_id}")
                try:
                    neighbor = hooke_pb2.NeighborInfo(
                        next_node_id=self.topology.get_next_node_id(node_id),
                        prev_node_id=self.topology.get_prev_node_id(node_id),
                    )
                    self.clients[node_id].MembershipChanges(neighbor)
                except grpc.RpcError as e:
                    self.logger.info(
                        f"Error while broadcasting neighbor info to {node_id}: {e}"
                    )
                    raise e
                self.logger.info(f"Broadcasted to {node_id}")
        self.logger.info("Broadcasting done")

    def close(self):
        self.logger.info("Closing all channels")
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
        notify()
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
        payload = "COORDINATOR"
        os.write(fd, payload.encode())


if __name__ == "__main__":
    serve()
