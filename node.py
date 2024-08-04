import uuid
import sys
from util import get_random_transformer
import hooke_pb2_grpc
import hooke_pb2
import grpc
from topology import Topology
import util
from concurrent import futures
import etcd3
import network
import etcd_utils
import logging
import json


class NodeServicer(hooke_pb2_grpc.NodeServicer):
    def __init__(
        self,
        port,
        host="localhost",
        coordinator_port=8080,
        coordinator_host="localhost",
        etcd_port=2379,
        etcd_host="localhost",
    ):
        self.port = port
        self.host = host
        self.version = 0
        self.transform = get_random_transformer()
        self.id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"http://localhost:{port}"))
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        self.neighbor = self.init_coordinator_connection(
            coordinator_host, coordinator_port
        )
        self.init_etcd_connection(etcd_host, etcd_port)

    def init_coordinator_connection(self, coordinator_host, coordinator_port):
        """
        Initialize connection to coordinator and join the network.
        Returns the neighbor nodes.
        """
        self.coordinator_channel = util.create_persistent_channel(
            coordinator_host, coordinator_port
        )
        self.coordinator_stub = hooke_pb2_grpc.CoordinatorStub(self.coordinator_channel)
        try:
            return self.coordinator_stub.NodeJoin(
                hooke_pb2.NodeInfo(
                    host=self.host, node_id=self.id, port=self.port
                )
            )
        except grpc.RpcError as e:
            self.logger.error(f"Error while joining: {e}")
            raise e

    def init_etcd_connection(self, etcd_host, etcd_port):
        """Initialize connection to etcd and write own metadata"""
        self.etcd_host = etcd_host
        self.etcd_port = etcd_port

        # self.etcd_client is the inbuilt database connection for node metadata
        self.etcd_client = etcd3.client(host=etcd_host, port=etcd_port)

        # write own metadata to etcd
        try:
            new_metadata = {
                etcd_utils.IP.ADDR: self.host,
                etcd_utils.IP.PORT: self.port,
            }
            self.etcd_client.put(f"nodes/{self.id}/metadata", json.dumps(new_metadata))
        except Exception as e:
            self.logger.error(f"Error while writing metadata to etcd: {e}")
            raise e

    # RPC method call by coordinator
    def MembershipChanges(self, request, context):
        try:
            self.logger.info(
                f"New neighbor info for node {self.id}: {request}", flush=True
            )
            self.neighbor = request
            return hooke_pb2.Void()
        except Exception as e:
            self.logger.error(f"Error while processing new neighbor info: {e}")
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            raise e

    def leave(self):
        try:
            self.coordinator_stub.NodeLeave(
                hooke_pb2.NodeInfo(
                    ip_addr=self.ip_addr, node_id=self.id, port=self.port
                )
            )
        except grpc.RpcError as e:
            self.logger.error(f"Error while leaving: {e}")
        self.coordinator_channel.close()

    def __str__(self) -> str:
        return f"[Node] id = {self.id}, port = {self.port}"


def serve(port):
    # TODO auto-assign port
    # TODO auto-find etcd host and port

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
