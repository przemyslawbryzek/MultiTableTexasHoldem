import socket
import struct
import time

MULTICAST_GROUP = "224.3.3.3"
UDP_PORT = 9876
MULTICAST_TTL = 2
RECV_BUF = 16

_PING = b"ping"
_PONG = b"pong"


def join_membership(*, blocking: bool = True) -> socket.socket:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)

    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    if hasattr(socket, "SO_REUSEPORT"):
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)

    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, MULTICAST_TTL)

    mreq = struct.pack("4sL", socket.inet_aton(MULTICAST_GROUP), socket.INADDR_ANY)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

    sock.bind(("", UDP_PORT))
    sock.setblocking(blocking)
    return sock


def probe_request(sock: socket.socket) -> str | None:
    sock.sendto(_PING, (MULTICAST_GROUP, UDP_PORT))
    deadline = time.monotonic() + 5.0
    sock.settimeout(5.0)
    try:
        while time.monotonic() < deadline:
            remaining = deadline - time.monotonic()
            sock.settimeout(max(remaining, 0))
            data, (addr, _port) = sock.recvfrom(RECV_BUF)
            if data == _PONG:
                return addr
    except (socket.timeout, OSError):
        pass
    return None


def probe_request_nb(sock: socket.socket) -> None:
    sock.sendto(_PING, (MULTICAST_GROUP, UDP_PORT))


def probe_response(sock: socket.socket) -> None:
    data, addr = sock.recvfrom(RECV_BUF)
    if data == _PING:
        sock.sendto(_PONG, addr)