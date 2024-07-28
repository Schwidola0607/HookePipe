import socket

def is_port_available(addr: str, port: int):
    """
    Check if a given address:port is available by attempting to create a socket.

    Returns True if the port is available, False otherwise.
    """

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind((addr, port))  # Try to bind the socket to the IP and port
            return True         # If successful, the port is available
        except socket.error as e:
            print(f"Socket error: {e}")
            return False

def find_available_port(addr: str):
    """
    Attempts to find an open port between 1111 and 44444 for the given address.

    Returns the port as a string.

    TODO: implement lease system with etcd for ports - https://etcd.io/docs/v3.4/learning/api/#lease-api
    """

    # Arbitrarily chose between 1111 and 44444 for ports
    for i in range(1111, 44444):
        if is_port_available(addr):
            return i

    return -1