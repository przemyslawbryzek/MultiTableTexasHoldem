import sys
from shared import discovery
from client.network.client import Client

if __name__ == "__main__":
    match len(sys.argv):
        case 1:
            sock = discovery.join_membership()
            host = discovery.probe_request(sock)
            if not host:
                print("failed to discover server on the local network", file=sys.stderr)
                sys.exit(1)
            client = Client(host)
        case 2:
            client = Client(sys.argv[1])
        case 3:
            client = Client(sys.argv[1], int(sys.argv[2]))
        case _:
            print(f"usage: {sys.argv[0]} [HOST] [PORT]", file=sys.stderr)
            sys.exit(1)
    # TODO
