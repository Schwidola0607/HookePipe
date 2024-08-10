import socket
import etcd3
import random
import sys
sys.path.append("..")
from topology import etcd_utils

def is_port_available(etcd_client: etcd3.Etcd3Client, addr: str, port: int) -> bool:
    """
    Check if a given address:port is available by checking if there exists a lease on it in etcd.

    Returns True if the port is available, False otherwise.
    """
    used = etcd_client.get(f"ports/{addr}/{port}")
    if used[0]:
        return False
    
    return True

def find_and_claim_available_port(etcd_client: etcd3.Etcd3Client, addr: str, id) -> tuple[etcd3.Lease, int]:
    """
    Attempts to find an open port between 1111 and 44444 for the given address.

    Attempts to claim the port by storing data in etcd.

    Returns the lease.
    """

    # Arbitrarily chose between 1111 and 44444 for ports
    visited = set()
    i = 0
    while i < 44444:
        port = random.randint(1111, 44444)
        
        if port in visited:
            continue

        if is_port_available(etcd_client=etcd_client, addr=addr, port=port):
            lease = etcd_client.lease(ttl=etcd_utils.ETCD_LEASE_EXPIRY_TIME)
            etcd_client.put(f"ports/{addr}/{port}", id, lease=lease)
            return lease, port

        visited.add(port)
        
        i += 1

    raise Exception("unable to find available port")