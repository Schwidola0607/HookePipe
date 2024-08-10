import socket
import etcd3

def is_port_available(etcd_client: etcd3.Etcd3Client, addr: str, port: int) -> bool:
    """
    Check if a given address:port is available by checking if there exists a lease on it in etcd.

    Returns True if the port is available, False otherwise.
    """
    used = etcd_client.get(f"ports/{addr}/{port}")
    if used[0]:
        return False
    
    return True

def find_available_port(etcd_client: etcd3.Etcd3Client, addr: str) -> int:
    """
    Attempts to find an open port between 1111 and 44444 for the given address.

    Returns the port as an int.

    TODO: implement lease system with etcd for ports - https://etcd.io/docs/v3.4/learning/api/#lease-api
    """

    # Arbitrarily chose between 1111 and 44444 for ports
    for i in range(1111, 44444):
        if is_port_available(etcd_client, addr, i):
            return i

    return -1