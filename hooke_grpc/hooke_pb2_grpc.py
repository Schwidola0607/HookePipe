# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc
import warnings

import hooke_grpc.hooke_pb2 as hooke__pb2

GRPC_GENERATED_VERSION = '1.65.1'
GRPC_VERSION = grpc.__version__
EXPECTED_ERROR_RELEASE = '1.66.0'
SCHEDULED_RELEASE_DATE = 'August 6, 2024'
_version_not_supported = False

try:
    from grpc._utilities import first_version_is_lower
    _version_not_supported = first_version_is_lower(GRPC_VERSION, GRPC_GENERATED_VERSION)
except ImportError:
    _version_not_supported = True

if _version_not_supported:
    warnings.warn(
        f'The grpc package installed is at version {GRPC_VERSION},'
        + f' but the generated code in hooke_pb2_grpc.py depends on'
        + f' grpcio>={GRPC_GENERATED_VERSION}.'
        + f' Please upgrade your grpc module to grpcio>={GRPC_GENERATED_VERSION}'
        + f' or downgrade your generated code using grpcio-tools<={GRPC_VERSION}.'
        + f' This warning will become an error in {EXPECTED_ERROR_RELEASE},'
        + f' scheduled for release on {SCHEDULED_RELEASE_DATE}.',
        RuntimeWarning
    )


class CoordinatorStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.NodeJoin = channel.unary_unary(
                '/hooke.Coordinator/NodeJoin',
                request_serializer=hooke__pb2.NodeInfo.SerializeToString,
                response_deserializer=hooke__pb2.NeighborInfo.FromString,
                _registered_method=True)
        self.NodeLeave = channel.unary_unary(
                '/hooke.Coordinator/NodeLeave',
                request_serializer=hooke__pb2.NodeInfo.SerializeToString,
                response_deserializer=hooke__pb2.Void.FromString,
                _registered_method=True)


class CoordinatorServicer(object):
    """Missing associated documentation comment in .proto file."""

    def NodeJoin(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def NodeLeave(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_CoordinatorServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'NodeJoin': grpc.unary_unary_rpc_method_handler(
                    servicer.NodeJoin,
                    request_deserializer=hooke__pb2.NodeInfo.FromString,
                    response_serializer=hooke__pb2.NeighborInfo.SerializeToString,
            ),
            'NodeLeave': grpc.unary_unary_rpc_method_handler(
                    servicer.NodeLeave,
                    request_deserializer=hooke__pb2.NodeInfo.FromString,
                    response_serializer=hooke__pb2.Void.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'hooke.Coordinator', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))
    server.add_registered_method_handlers('hooke.Coordinator', rpc_method_handlers)


 # This class is part of an EXPERIMENTAL API.
class Coordinator(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def NodeJoin(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/hooke.Coordinator/NodeJoin',
            hooke__pb2.NodeInfo.SerializeToString,
            hooke__pb2.NeighborInfo.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def NodeLeave(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/hooke.Coordinator/NodeLeave',
            hooke__pb2.NodeInfo.SerializeToString,
            hooke__pb2.Void.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)


class NodeStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.MembershipChanges = channel.unary_unary(
                '/hooke.Node/MembershipChanges',
                request_serializer=hooke__pb2.NeighborInfo.SerializeToString,
                response_deserializer=hooke__pb2.Void.FromString,
                _registered_method=True)


class NodeServicer(object):
    """Missing associated documentation comment in .proto file."""

    def MembershipChanges(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_NodeServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'MembershipChanges': grpc.unary_unary_rpc_method_handler(
                    servicer.MembershipChanges,
                    request_deserializer=hooke__pb2.NeighborInfo.FromString,
                    response_serializer=hooke__pb2.Void.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'hooke.Node', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))
    server.add_registered_method_handlers('hooke.Node', rpc_method_handlers)


 # This class is part of an EXPERIMENTAL API.
class Node(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def MembershipChanges(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/hooke.Node/MembershipChanges',
            hooke__pb2.NeighborInfo.SerializeToString,
            hooke__pb2.Void.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)
