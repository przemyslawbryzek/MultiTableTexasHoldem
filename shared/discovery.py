import random
import socket
import struct
from server.network import server

MULTICAST_GROUP = "224.3.3.3"
UDP_PORT = 9876
UDP_EXTRA_PORTS = [9877, 9878, 9879]
UDP_ALL_PORTS = [UDP_PORT] + UDP_EXTRA_PORTS
MULTICAST_TTL = 2
RECV_BUF = 16

_PING = b"ping"
_PONG = b"pong"


def join_membership(*, listening_port: int | None = None) -> socket.socket:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)

    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    if hasattr(socket, "SO_REUSEPORT"):
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)

    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, MULTICAST_TTL)

    mreq = struct.pack("4sL", socket.inet_aton(MULTICAST_GROUP), socket.INADDR_ANY)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
    sock.setblocking(False)
    if listening_port is None:
        sock.bind(("", 0))
    elif listening_port is not server.DEFAULT_PORT:
        sock.bind(("", random.choice(UDP_EXTRA_PORTS)))
    else:
        sock.bind(("", UDP_PORT))
    return sock


def probe_request(sock: socket.socket) -> None:
    for port in UDP_ALL_PORTS:
        sock.sendto(_PING, (MULTICAST_GROUP, port))


def probe_poll(sock: socket.socket):
    addrs = []
    try:
        while True:
            data, (host, _) = sock.recvfrom(RECV_BUF)
            if data[: len(_PONG)] == _PONG:
                port = struct.unpack(">H", data[len(_PONG) :])[0]
                addrs.append((host, port))
    except OSError:
        pass
    return addrs


def probe_response(sock: socket.socket, listening_port: int) -> None:
    data, addr = sock.recvfrom(RECV_BUF)
    if data == _PING:
        sock.sendto(_PONG + struct.pack(">H", listening_port), addr)
