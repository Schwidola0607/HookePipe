import uuid
import sys
import network.network as network
from util import get_random_transformer
import hooke_grpc.hooke_pb2_grpc as hooke_pb2_grpc
import hooke_grpc.hooke_pb2 as hooke_pb2
import grpc
import util
from concurrent import futures
import etcd3
from logconfig import colors
import topology.etcd_utils as etcd_utils
import logging
import json
import asyncio


class NodeServicer(hooke_pb2_grpc.NodeServicer):
    def __init__(
        self,
        host="localhost",
        coordinator_port=8080,
        coordinator_host="localhost",
        etcd_port=23790,
        etcd_host="localhost",
    ):
        self.logger = colors.get_logger("node_logger")
        self.port = -1
        self.host = host
        self.version = 0
        self.transform = get_random_transformer()
        self.id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"http://localhost:{self.port}"))
        self.lease = None
        self.init_etcd_connection(etcd_host, etcd_port)
        self.claim_port()
        self.neighbor = self.init_coordinator_connection(
            coordinator_host, coordinator_port
        )

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
                hooke_pb2.NodeInfo(host=self.host, node_id=self.id, port=self.port)
            )
        except grpc.RpcError as e:
            self.logger.error(f"Error while joining: {e}")
            raise e

    def init_etcd_connection(self, etcd_host, etcd_port):
        """Initialize connection to etcd"""
        self.etcd_host = etcd_host
        self.etcd_port = etcd_port

        # self.etcd_client is the inbuilt database connection for node metadata
        self.etcd_client = etcd3.client(host=etcd_host, port=etcd_port)
            
    def claim_port(self):
        """Claims a port by creating a lease with etcd, and adds the node metadata"""
        try:
            self.port = network.find_available_port(self.etcd_client, self.host)

            self.lease = self.etcd_client.lease(ttl=etcd_utils.ETCD_LEASE_EXPIRY_TIME)

            self.etcd_client.put(f"ports/{self.host}/{self.port}", self.id, lease=self.lease)

            # adds metadata including host and port
            new_metadata = {
                etcd_utils.IP.ADDR: self.host,
                etcd_utils.IP.PORT: self.port,
            }
            self.etcd_client.put(f"nodes/{self.id}/metadata", json.dumps(new_metadata), lease=self.lease)
        except Exception as e:
            self.logger.error(f"Error while writing metadata to etcd: {e}")
            raise e

    # RPC method call by coordinator
    def MembershipChanges(self, request, context):
        try:
            self.logger.info(f"New neighbor info for node {self.id}: {request}")
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

    async def refresh_port_lease(self):
        """Refreshes the lease that the given node has on its port."""
        if self.lease:
            self.lease.refresh()
        else:
            self.logger.error("Node %s: Error refreshing port %s lease", self.id, self.port)

    def __str__(self) -> str:
        return f"[Node] id = {self.id}, port = {self.port}"

async def serve():
    node_server = grpc.aio.server()
    node = NodeServicer()
    hooke_pb2_grpc.add_NodeServicer_to_server(node, node_server)
    node_server.add_insecure_port(f"[::]:{node.port}")

    async def refresh_lease():
        while True:
            await asyncio.sleep(5)
            # not sure if this is actuall async right now but should be fine
            await node.refresh_port_lease()
    
    asyncio.create_task(refresh_lease())

    try:
        await node_server.start()
        print(f"Node server started at port {node.port}")
        await node_server.wait_for_termination()
    except Exception as e:
        print(f"Node server error: {e}", file=sys.stderr)
        node_server.stop(0)
        exit(1)

if __name__ == "__main__":
    import asyncio
    asyncio.run(serve())