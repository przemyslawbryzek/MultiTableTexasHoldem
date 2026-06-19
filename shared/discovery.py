import socket
import struct
import time

MULTICAST_GROUP = "224.3.3.3"
UDP_PORT = 9876


def join_membership(*, blocking=True):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    mreq = struct.pack("4sl", socket.inet_aton(MULTICAST_GROUP), socket.INADDR_ANY)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((MULTICAST_GROUP, UDP_PORT))
    sock.setblocking(blocking)
    return sock


def probe_request(sock: socket.socket) -> str | None:
    sock.settimeout(1)
    sock.sendto("ping", (MULTICAST_GROUP, UDP_PORT))
    start = time.time()
    try:
        while True:
            buf, (addr,) = sock.recvfrom(4)
            if buf.decode() == "pong":
                return addr
            if time.time() - start >= 5:
                return None
    except socket.timeout:
        return None


def probe_response(sock: socket.socket):
    buf, addr = sock.recvfrom(4)
    if buf.decode() == "ping":
        sock.sendto("pong", addr)
